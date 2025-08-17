"""
Smart Editor with Context Awareness

Provides context-aware file modifications with backup and rollback capabilities.
"""

import os
import json
import shutil
import logging
import hashlib
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass
import re

from .website_memory import SiteMemory, WebsiteMemory

logger = logging.getLogger(__name__)


@dataclass
class EditOperation:
    """Represents a single edit operation"""
    file_path: str
    operation_type: str  # 'replace', 'insert', 'delete', 'append'
    target_content: str
    new_content: str
    line_start: Optional[int] = None
    line_end: Optional[int] = None
    backup_path: Optional[str] = None
    timestamp: Optional[str] = None


@dataclass
class EditResult:
    """Result of an edit operation"""
    success: bool
    operation: EditOperation
    error_message: Optional[str] = None
    lines_changed: int = 0
    backup_created: bool = False


class FileBackupManager:
    """Manages file backups for rollback functionality"""
    
    def __init__(self, backup_dir: str = "ai_features/data/backups"):
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
    
    def create_backup(self, file_path: str, operation_id: str = None) -> str:
        """Create backup of file before editing"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        if not operation_id:
            operation_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create backup filename
        original_name = os.path.basename(file_path)
        backup_name = f"{operation_id}_{original_name}"
        backup_path = self.backup_dir / backup_name
        
        # Copy file to backup location
        shutil.copy2(file_path, backup_path)
        logger.info(f"Created backup: {backup_path}")
        
        return str(backup_path)
    
    def restore_backup(self, backup_path: str, original_path: str) -> bool:
        """Restore file from backup"""
        try:
            if not os.path.exists(backup_path):
                logger.error(f"Backup not found: {backup_path}")
                return False
            
            shutil.copy2(backup_path, original_path)
            logger.info(f"Restored file from backup: {backup_path} -> {original_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to restore backup: {e}")
            return False
    
    def list_backups(self, file_pattern: str = None) -> List[Dict[str, Any]]:
        """List available backups"""
        backups = []
        
        for backup_file in self.backup_dir.glob("*"):
            if backup_file.is_file():
                if file_pattern and file_pattern not in backup_file.name:
                    continue
                
                stat = backup_file.stat()
                backups.append({
                    'path': str(backup_file),
                    'original_name': backup_file.name.split('_', 1)[1] if '_' in backup_file.name else backup_file.name,
                    'created_at': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    'size': stat.st_size
                })
        
        return sorted(backups, key=lambda x: x['created_at'], reverse=True)


class ContextAwareEditor:
    """Editor that understands website structure and context"""
    
    def __init__(self, memory: SiteMemory):
        self.memory = memory
        self.site_path = memory.converted_path
    
    def analyze_edit_context(self, file_path: str, target_content: str) -> Dict[str, Any]:
        """Analyze context around the content to be edited"""
        context = {
            'file_type': self._get_file_type(file_path),
            'is_critical_file': self._is_critical_file(file_path),
            'related_files': self._find_related_files(file_path),
            'content_location': self._locate_content_in_file(file_path, target_content),
            'impact_analysis': {}
        }
        
        # Analyze potential impact
        if context['file_type'] == 'html':
            context['impact_analysis'] = self._analyze_html_impact(file_path, target_content)
        elif context['file_type'] == 'css':
            context['impact_analysis'] = self._analyze_css_impact(file_path, target_content)
        elif context['file_type'] == 'js':
            context['impact_analysis'] = self._analyze_js_impact(file_path, target_content)
        
        return context
    
    def _get_file_type(self, file_path: str) -> str:
        """Determine file type"""
        ext = os.path.splitext(file_path)[1].lower()
        if ext in ['.html', '.htm']:
            return 'html'
        elif ext == '.css':
            return 'css'
        elif ext == '.js':
            return 'js'
        elif ext in ['.jpg', '.jpeg', '.png', '.gif', '.svg']:
            return 'image'
        else:
            return 'other'
    
    def _is_critical_file(self, file_path: str) -> bool:
        """Check if file is critical to site functionality"""
        rel_path = os.path.relpath(file_path, self.site_path)
        
        # Main index files are critical
        if 'index.html' in rel_path:
            return True
        
        # Main CSS files are critical
        if rel_path in [style for page in self.memory.pages.values() for style in page.stylesheets]:
            return True
        
        # Files referenced by many pages are critical
        reference_count = 0
        for page in self.memory.pages.values():
            all_refs = page.stylesheets + page.scripts + page.images
            if rel_path in all_refs:
                reference_count += 1
        
        return reference_count > len(self.memory.pages) * 0.3  # Referenced by >30% of pages
    
    def _find_related_files(self, file_path: str) -> List[str]:
        """Find files related to the target file"""
        related = []
        rel_path = os.path.relpath(file_path, self.site_path)
        
        # For HTML files, find related CSS and JS
        if self._get_file_type(file_path) == 'html':
            page_info = self.memory.pages.get(rel_path)
            if page_info:
                related.extend(page_info.stylesheets)
                related.extend(page_info.scripts)
        
        # For CSS files, find HTML files that use it
        elif self._get_file_type(file_path) == 'css':
            for page_path, page_info in self.memory.pages.items():
                if rel_path in page_info.stylesheets:
                    related.append(page_path)
        
        # For JS files, find HTML files that use it
        elif self._get_file_type(file_path) == 'js':
            for page_path, page_info in self.memory.pages.items():
                if rel_path in page_info.scripts:
                    related.append(page_path)
        
        return related
    
    def _locate_content_in_file(self, file_path: str, target_content: str) -> Dict[str, Any]:
        """Locate content within file structure"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                lines = content.split('\n')
        except Exception as e:
            return {'error': str(e)}
        
        location = {
            'found': False,
            'line_number': None,
            'line_range': None,
            'context_before': [],
            'context_after': [],
            'exact_match': False
        }
        
        # Look for exact match
        if target_content in content:
            location['found'] = True
            location['exact_match'] = True
            
            # Find line number
            for i, line in enumerate(lines):
                if target_content in line:
                    location['line_number'] = i + 1
                    location['context_before'] = lines[max(0, i-3):i]
                    location['context_after'] = lines[i+1:min(len(lines), i+4)]
                    break
        
        # Look for fuzzy match
        else:
            # Try to find similar content
            target_words = target_content.lower().split()
            if len(target_words) >= 3:
                best_match = 0
                best_line = None
                
                for i, line in enumerate(lines):
                    line_words = line.lower().split()
                    common_words = set(target_words) & set(line_words)
                    if len(common_words) > best_match:
                        best_match = len(common_words)
                        best_line = i
                
                if best_match >= 2:  # At least 2 words in common
                    location['found'] = True
                    location['line_number'] = best_line + 1
                    location['context_before'] = lines[max(0, best_line-3):best_line]
                    location['context_after'] = lines[best_line+1:min(len(lines), best_line+4)]
        
        return location
    
    def _analyze_html_impact(self, file_path: str, target_content: str) -> Dict[str, Any]:
        """Analyze impact of HTML changes"""
        impact = {
            'affects_navigation': False,
            'affects_layout': False,
            'affects_content': False,
            'potential_issues': []
        }
        
        target_lower = target_content.lower()
        
        # Check if it affects navigation
        nav_indicators = ['nav', 'menu', 'href=', '<a ', 'navigation']
        if any(indicator in target_lower for indicator in nav_indicators):
            impact['affects_navigation'] = True
        
        # Check if it affects layout
        layout_indicators = ['div', 'section', 'header', 'footer', 'aside', 'main']
        if any(indicator in target_lower for indicator in layout_indicators):
            impact['affects_layout'] = True
        
        # Check if it affects content
        content_indicators = ['<p>', '<h1>', '<h2>', '<h3>', '<span>', 'class=']
        if any(indicator in target_lower for indicator in content_indicators):
            impact['affects_content'] = True
        
        # Potential issues
        if '<script' in target_lower:
            impact['potential_issues'].append('Modifying JavaScript may break functionality')
        if 'onclick=' in target_lower or 'onload=' in target_lower:
            impact['potential_issues'].append('Modifying event handlers may break interactivity')
        
        return impact
    
    def _analyze_css_impact(self, file_path: str, target_content: str) -> Dict[str, Any]:
        """Analyze impact of CSS changes"""
        impact = {
            'affects_layout': False,
            'affects_styling': False,
            'affects_responsiveness': False,
            'potential_issues': []
        }
        
        target_lower = target_content.lower()
        
        # Check layout impact
        layout_properties = ['display', 'position', 'float', 'flex', 'grid', 'width', 'height']
        if any(prop in target_lower for prop in layout_properties):
            impact['affects_layout'] = True
        
        # Check styling impact
        style_properties = ['color', 'background', 'font', 'border', 'margin', 'padding']
        if any(prop in target_lower for prop in style_properties):
            impact['affects_styling'] = True
        
        # Check responsiveness impact
        responsive_indicators = ['@media', 'min-width', 'max-width', '%', 'rem', 'em']
        if any(indicator in target_lower for indicator in responsive_indicators):
            impact['affects_responsiveness'] = True
        
        # Potential issues
        if '!important' in target_lower:
            impact['potential_issues'].append('Using !important may cause specificity issues')
        if 'position: fixed' in target_lower or 'position: absolute' in target_lower:
            impact['potential_issues'].append('Absolute/fixed positioning may cause layout issues')
        
        return impact
    
    def _analyze_js_impact(self, file_path: str, target_content: str) -> Dict[str, Any]:
        """Analyze impact of JavaScript changes"""
        impact = {
            'affects_functionality': False,
            'affects_events': False,
            'affects_data': False,
            'potential_issues': []
        }
        
        target_lower = target_content.lower()
        
        # Check functionality impact
        function_indicators = ['function', 'const', 'let', 'var', '=>']
        if any(indicator in target_lower for indicator in function_indicators):
            impact['affects_functionality'] = True
        
        # Check event handling impact
        event_indicators = ['addeventlistener', 'onclick', 'onload', 'event']
        if any(indicator in target_lower for indicator in event_indicators):
            impact['affects_events'] = True
        
        # Check data handling impact
        data_indicators = ['ajax', 'fetch', 'json', 'localstorage', 'sessionstorage']
        if any(indicator in target_lower for indicator in data_indicators):
            impact['affects_data'] = True
        
        # Potential issues
        if 'eval(' in target_lower:
            impact['potential_issues'].append('Using eval() is dangerous and should be avoided')
        if 'document.write' in target_lower:
            impact['potential_issues'].append('document.write can cause issues in modern browsers')
        
        return impact


class SmartEditor:
    """Main smart editor class with full editing capabilities"""
    
    def __init__(self, site_id: str, memory_manager: WebsiteMemory = None):
        self.site_id = site_id
        self.memory_manager = memory_manager or WebsiteMemory()
        self.memory = self.memory_manager.load_memory(site_id)
        
        if not self.memory:
            raise ValueError(f"No memory found for site ID: {site_id}")
        
        self.backup_manager = FileBackupManager()
        self.context_editor = ContextAwareEditor(self.memory)
        self.edit_history = []
    
    def edit_file(self, file_path: str, target_content: str, new_content: str, 
                  operation_type: str = 'replace', create_backup: bool = True) -> EditResult:
        """Perform smart file editing with context awareness"""
        
        # Convert relative path to absolute
        if not os.path.isabs(file_path):
            file_path = os.path.join(self.memory.converted_path, file_path)
        
        # Validate file exists
        if not os.path.exists(file_path):
            return EditResult(
                success=False,
                operation=EditOperation(file_path, operation_type, target_content, new_content),
                error_message=f"File not found: {file_path}"
            )
        
        # Analyze context
        context = self.context_editor.analyze_edit_context(file_path, target_content)
        
        # Create backup if requested
        backup_path = None
        if create_backup:
            try:
                operation_id = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                backup_path = self.backup_manager.create_backup(file_path, operation_id)
            except Exception as e:
                return EditResult(
                    success=False,
                    operation=EditOperation(file_path, operation_type, target_content, new_content),
                    error_message=f"Failed to create backup: {e}"
                )
        
        # Perform the edit
        operation = EditOperation(
            file_path=file_path,
            operation_type=operation_type,
            target_content=target_content,
            new_content=new_content,
            backup_path=backup_path,
            timestamp=datetime.now().isoformat()
        )
        
        try:
            result = self._perform_edit_operation(operation, context)
            
            # Add to history
            self.edit_history.append({
                'operation': operation,
                'result': result,
                'context': context,
                'timestamp': operation.timestamp
            })
            
            return result
            
        except Exception as e:
            # Restore backup if edit failed
            if backup_path:
                self.backup_manager.restore_backup(backup_path, file_path)
            
            return EditResult(
                success=False,
                operation=operation,
                error_message=f"Edit operation failed: {e}"
            )
    
    def _perform_edit_operation(self, operation: EditOperation, context: Dict[str, Any]) -> EditResult:
        """Perform the actual edit operation"""
        try:
            with open(operation.file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                original_lines = content.split('\n')
        except Exception as e:
            raise Exception(f"Failed to read file: {e}")
        
        lines_changed = 0
        
        if operation.operation_type == 'replace':
            if operation.target_content in content:
                new_content = content.replace(operation.target_content, operation.new_content)
                lines_changed = abs(len(new_content.split('\n')) - len(original_lines))
            else:
                raise Exception(f"Target content not found in file")
        
        elif operation.operation_type == 'insert':
            # Insert after target content
            if operation.target_content in content:
                new_content = content.replace(
                    operation.target_content, 
                    operation.target_content + operation.new_content
                )
                lines_changed = len(operation.new_content.split('\n')) - 1
            else:
                raise Exception(f"Target content not found in file")
        
        elif operation.operation_type == 'append':
            # Append to end of file
            new_content = content + operation.new_content
            lines_changed = len(operation.new_content.split('\n')) - 1
        
        elif operation.operation_type == 'delete':
            if operation.target_content in content:
                new_content = content.replace(operation.target_content, '')
                lines_changed = len(operation.target_content.split('\n')) - 1
            else:
                raise Exception(f"Target content not found in file")
        
        else:
            raise Exception(f"Unknown operation type: {operation.operation_type}")
        
        # Write the modified content
        try:
            with open(operation.file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
        except Exception as e:
            raise Exception(f"Failed to write file: {e}")
        
        return EditResult(
            success=True,
            operation=operation,
            lines_changed=lines_changed,
            backup_created=bool(operation.backup_path)
        )
    
    def validate_changes(self, file_path: str) -> Dict[str, Any]:
        """Validate file after changes"""
        validation = {
            'valid': True,
            'issues': [],
            'warnings': []
        }
        
        # Convert relative path to absolute (same as edit_file method)
        if not os.path.isabs(file_path):
            file_path = os.path.join(self.memory.converted_path, file_path)
        
        file_type = self.context_editor._get_file_type(file_path)
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except Exception as e:
            validation['valid'] = False
            validation['issues'].append(f"Cannot read file: {e}")
            return validation
        
        # HTML validation
        if file_type == 'html':
            validation.update(self._validate_html(content))
        
        # CSS validation
        elif file_type == 'css':
            validation.update(self._validate_css(content))
        
        # JavaScript validation
        elif file_type == 'js':
            validation.update(self._validate_js(content))
        
        return validation
    
    def _validate_html(self, content: str) -> Dict[str, Any]:
        """Basic HTML validation"""
        issues = []
        warnings = []
        
        # Check for basic HTML structure
        if '<html' not in content.lower():
            warnings.append('Missing HTML tag')
        if '<head' not in content.lower():
            warnings.append('Missing HEAD tag')
        if '<body' not in content.lower():
            warnings.append('Missing BODY tag')
        
        # Check for unclosed tags (basic check)
        open_tags = re.findall(r'<([a-zA-Z][a-zA-Z0-9]*)[^>]*>', content)
        close_tags = re.findall(r'</([a-zA-Z][a-zA-Z0-9]*)>', content)
        
        # Self-closing tags that don't need closing tags
        self_closing = {'img', 'br', 'hr', 'input', 'meta', 'link', 'area', 'base', 'col', 'embed', 'source', 'track', 'wbr'}
        
        open_tags = [tag.lower() for tag in open_tags if tag.lower() not in self_closing]
        close_tags = [tag.lower() for tag in close_tags]
        
        for tag in set(open_tags):
            if open_tags.count(tag) != close_tags.count(tag):
                issues.append(f'Unmatched {tag} tags')
        
        return {'issues': issues, 'warnings': warnings}
    
    def _validate_css(self, content: str) -> Dict[str, Any]:
        """Basic CSS validation"""
        issues = []
        warnings = []
        
        # Check for unmatched braces
        open_braces = content.count('{')
        close_braces = content.count('}')
        
        if open_braces != close_braces:
            issues.append(f'Unmatched braces: {open_braces} opening, {close_braces} closing')
        
        # Check for missing semicolons (basic check)
        lines = content.split('\n')
        for i, line in enumerate(lines):
            line = line.strip()
            if ':' in line and not line.endswith((';', '{', '}')) and line != '':
                if not any(char in line for char in ['/*', '*/', '@']):
                    warnings.append(f'Line {i+1}: Missing semicolon?')
        
        return {'issues': issues, 'warnings': warnings}
    
    def _validate_js(self, content: str) -> Dict[str, Any]:
        """Basic JavaScript validation"""
        issues = []
        warnings = []
        
        # Check for unmatched parentheses
        open_parens = content.count('(')
        close_parens = content.count(')')
        
        if open_parens != close_parens:
            issues.append(f'Unmatched parentheses: {open_parens} opening, {close_parens} closing')
        
        # Check for unmatched braces
        open_braces = content.count('{')
        close_braces = content.count('}')
        
        if open_braces != close_braces:
            issues.append(f'Unmatched braces: {open_braces} opening, {close_braces} closing')
        
        # Check for unmatched brackets
        open_brackets = content.count('[')
        close_brackets = content.count(']')
        
        if open_brackets != close_brackets:
            issues.append(f'Unmatched brackets: {open_brackets} opening, {close_brackets} closing')
        
        return {'issues': issues, 'warnings': warnings}
    
    def rollback_edit(self, edit_index: int = -1) -> bool:
        """Rollback to previous version using backup"""
        if not self.edit_history:
            logger.error("No edit history available")
            return False
        
        if abs(edit_index) > len(self.edit_history):
            logger.error(f"Invalid edit index: {edit_index}")
            return False
        
        edit_record = self.edit_history[edit_index]
        operation = edit_record['operation']
        
        if not operation.backup_path:
            logger.error("No backup available for this edit")
            return False
        
        return self.backup_manager.restore_backup(operation.backup_path, operation.file_path)
    
    def get_edit_history(self) -> List[Dict[str, Any]]:
        """Get edit history for this session"""
        return self.edit_history.copy()
    
    def batch_edit(self, operations: List[Dict[str, Any]], 
                   create_backup: bool = True, validate_each: bool = True) -> List[EditResult]:
        """Perform multiple edit operations"""
        results = []
        
        for op_dict in operations:
            result = self.edit_file(
                file_path=op_dict['file_path'],
                target_content=op_dict['target_content'],
                new_content=op_dict['new_content'],
                operation_type=op_dict.get('operation_type', 'replace'),
                create_backup=create_backup
            )
            
            results.append(result)
            
            # Stop on first failure if validation is enabled
            if validate_each and not result.success:
                logger.error(f"Batch edit stopped due to failure: {result.error_message}")
                break
        
        return results