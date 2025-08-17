"""
Website Memory System

Analyzes converted WordPress sites and creates persistent memory
for AI-powered editing capabilities.
"""

import os
import json
import hashlib
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass, asdict
from pathlib import Path
import re

logger = logging.getLogger(__name__)


@dataclass
class PageInfo:
    """Information about a website page"""
    path: str
    title: str
    content_hash: str
    word_count: int
    has_forms: bool
    external_links: List[str]
    internal_links: List[str]
    images: List[str]
    scripts: List[str]
    stylesheets: List[str]
    meta_description: str = ""
    headings: List[Dict[str, str]] = None
    
    def __post_init__(self):
        if self.headings is None:
            self.headings = []


@dataclass
class ComponentInfo:
    """Information about a website component"""
    type: str  # navigation, header, footer, sidebar, etc.
    selector: str
    content_pattern: str
    pages_found: List[str]
    variations: List[str]


@dataclass
class StylePattern:
    """CSS styling patterns"""
    framework: Optional[str]  # bootstrap, tailwind, etc.
    color_scheme: Dict[str, str]
    typography: Dict[str, str]
    layout_type: str  # grid, flex, table, etc.
    responsive_breakpoints: List[str]


@dataclass
class SiteMemory:
    """Complete website memory structure"""
    site_id: str
    site_url: str
    converted_path: str
    created_at: str
    last_updated: str
    technology_stack: Dict[str, str]
    pages: Dict[str, PageInfo]
    components: Dict[str, ComponentInfo]
    style_patterns: StylePattern
    navigation_structure: Dict[str, Any]
    content_patterns: Dict[str, Any]
    file_structure: Dict[str, Any]
    metadata: Dict[str, Any]


class WebsiteAnalyzer:
    """Analyzes website structure and content"""
    
    def __init__(self):
        self.html_parser_available = self._check_html_parser()
    
    def _check_html_parser(self) -> bool:
        """Check if BeautifulSoup is available"""
        try:
            from bs4 import BeautifulSoup
            return True
        except ImportError:
            logger.warning("BeautifulSoup not available, using regex parsing")
            return False
    
    def analyze_html_file(self, file_path: str) -> PageInfo:
        """Analyze a single HTML file"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except Exception as e:
            logger.error(f"Failed to read {file_path}: {e}")
            return None
        
        if self.html_parser_available:
            return self._analyze_with_bs4(file_path, content)
        else:
            return self._analyze_with_regex(file_path, content)
    
    def _analyze_with_bs4(self, file_path: str, content: str) -> PageInfo:
        """Analyze HTML using BeautifulSoup"""
        from bs4 import BeautifulSoup
        
        soup = BeautifulSoup(content, 'html.parser')
        
        # Extract basic information
        title = soup.find('title')
        title_text = title.get_text().strip() if title else os.path.basename(file_path)
        
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        meta_description = meta_desc.get('content', '') if meta_desc else ''
        
        # Count words in visible text
        for script in soup(["script", "style"]):
            script.decompose()
        visible_text = soup.get_text()
        word_count = len(visible_text.split())
        
        # Extract links
        internal_links = []
        external_links = []
        for link in soup.find_all('a', href=True):
            href = link['href']
            if href.startswith('http'):
                external_links.append(href)
            else:
                internal_links.append(href)
        
        # Extract images
        images = [img.get('src', '') for img in soup.find_all('img') if img.get('src')]
        
        # Extract scripts and stylesheets
        scripts = [script.get('src', '') for script in soup.find_all('script') if script.get('src')]
        stylesheets = [link.get('href', '') for link in soup.find_all('link', rel='stylesheet')]
        
        # Extract headings
        headings = []
        for i in range(1, 7):
            for heading in soup.find_all(f'h{i}'):
                headings.append({
                    'level': f'h{i}',
                    'text': heading.get_text().strip()
                })
        
        # Check for forms
        has_forms = bool(soup.find('form'))
        
        # Generate content hash
        content_hash = hashlib.md5(visible_text.encode()).hexdigest()
        
        return PageInfo(
            path=file_path,
            title=title_text,
            content_hash=content_hash,
            word_count=word_count,
            has_forms=has_forms,
            external_links=external_links,
            internal_links=internal_links,
            images=images,
            scripts=scripts,
            stylesheets=stylesheets,
            meta_description=meta_description,
            headings=headings
        )
    
    def _analyze_with_regex(self, file_path: str, content: str) -> PageInfo:
        """Analyze HTML using regex (fallback)"""
        # Extract title
        title_match = re.search(r'<title[^>]*>(.*?)</title>', content, re.IGNORECASE | re.DOTALL)
        title = title_match.group(1).strip() if title_match else os.path.basename(file_path)
        
        # Extract meta description
        meta_desc_match = re.search(r'<meta[^>]*name=["\']description["\'][^>]*content=["\']([^"\']*)["\']', content, re.IGNORECASE)
        meta_description = meta_desc_match.group(1) if meta_desc_match else ''
        
        # Extract visible text (remove scripts and styles)
        text_content = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.IGNORECASE | re.DOTALL)
        text_content = re.sub(r'<style[^>]*>.*?</style>', '', text_content, flags=re.IGNORECASE | re.DOTALL)
        text_content = re.sub(r'<[^>]+>', '', text_content)
        word_count = len(text_content.split())
        
        # Extract links
        link_matches = re.findall(r'<a[^>]*href=["\']([^"\']*)["\']', content, re.IGNORECASE)
        internal_links = [link for link in link_matches if not link.startswith('http')]
        external_links = [link for link in link_matches if link.startswith('http')]
        
        # Extract images
        images = re.findall(r'<img[^>]*src=["\']([^"\']*)["\']', content, re.IGNORECASE)
        
        # Extract scripts and stylesheets
        scripts = re.findall(r'<script[^>]*src=["\']([^"\']*)["\']', content, re.IGNORECASE)
        stylesheets = re.findall(r'<link[^>]*rel=["\']stylesheet["\'][^>]*href=["\']([^"\']*)["\']', content, re.IGNORECASE)
        
        # Extract headings
        headings = []
        for i in range(1, 7):
            heading_matches = re.findall(f'<h{i}[^>]*>(.*?)</h{i}>', content, re.IGNORECASE | re.DOTALL)
            for heading_text in heading_matches:
                clean_text = re.sub(r'<[^>]+>', '', heading_text).strip()
                headings.append({'level': f'h{i}', 'text': clean_text})
        
        # Check for forms
        has_forms = bool(re.search(r'<form[^>]*>', content, re.IGNORECASE))
        
        # Generate content hash
        content_hash = hashlib.md5(text_content.encode()).hexdigest()
        
        return PageInfo(
            path=file_path,
            title=title,
            content_hash=content_hash,
            word_count=word_count,
            has_forms=has_forms,
            external_links=external_links,
            internal_links=internal_links,
            images=images,
            scripts=scripts,
            stylesheets=stylesheets,
            meta_description=meta_description,
            headings=headings
        )
    
    def detect_components(self, pages: Dict[str, PageInfo]) -> Dict[str, ComponentInfo]:
        """Detect common components across pages"""
        components = {}
        
        # Analyze navigation patterns
        nav_links = {}
        for page_path, page_info in pages.items():
            for link in page_info.internal_links:
                if link not in nav_links:
                    nav_links[link] = []
                nav_links[link].append(page_path)
        
        # Find common navigation items (appear on multiple pages)
        common_nav_links = {link: pages for link, pages in nav_links.items() if len(pages) > 1}
        
        if common_nav_links:
            components['navigation'] = ComponentInfo(
                type='navigation',
                selector='nav, .nav, .navigation, .menu',
                content_pattern='Common navigation links',
                pages_found=list(set([page for pages in common_nav_links.values() for page in pages])),
                variations=list(common_nav_links.keys())
            )
        
        # Detect header/footer patterns
        title_patterns = {}
        for page_path, page_info in pages.items():
            if page_info.headings:
                first_heading = page_info.headings[0]['text']
                if first_heading not in title_patterns:
                    title_patterns[first_heading] = []
                title_patterns[first_heading].append(page_path)
        
        # Find stylesheet patterns
        common_styles = {}
        for page_path, page_info in pages.items():
            for stylesheet in page_info.stylesheets:
                if stylesheet not in common_styles:
                    common_styles[stylesheet] = []
                common_styles[stylesheet].append(page_path)
        
        if common_styles:
            global_styles = {style: pages for style, pages in common_styles.items() if len(pages) > len(pages) * 0.5}
            if global_styles:
                components['global_styles'] = ComponentInfo(
                    type='styles',
                    selector='link[rel="stylesheet"]',
                    content_pattern='Global stylesheets',
                    pages_found=list(set([page for pages in global_styles.values() for page in pages])),
                    variations=list(global_styles.keys())
                )
        
        return components
    
    def analyze_style_patterns(self, site_path: str, pages: Dict[str, PageInfo]) -> StylePattern:
        """Analyze CSS styling patterns"""
        framework = None
        color_scheme = {}
        typography = {}
        layout_type = "unknown"
        responsive_breakpoints = []
        
        # Look for CSS framework indicators
        all_stylesheets = set()
        for page_info in pages.values():
            all_stylesheets.update(page_info.stylesheets)
        
        for stylesheet in all_stylesheets:
            if 'bootstrap' in stylesheet.lower():
                framework = 'Bootstrap'
            elif 'tailwind' in stylesheet.lower():
                framework = 'Tailwind'
            elif 'foundation' in stylesheet.lower():
                framework = 'Foundation'
        
        # Try to analyze main CSS file if it exists
        css_files = []
        for root, dirs, files in os.walk(site_path):
            for file in files:
                if file.endswith('.css'):
                    css_files.append(os.path.join(root, file))
        
        if css_files:
            main_css = self._analyze_css_file(css_files[0])
            color_scheme = main_css.get('colors', {})
            typography = main_css.get('typography', {})
            layout_type = main_css.get('layout', 'unknown')
            responsive_breakpoints = main_css.get('breakpoints', [])
        
        return StylePattern(
            framework=framework,
            color_scheme=color_scheme,
            typography=typography,
            layout_type=layout_type,
            responsive_breakpoints=responsive_breakpoints
        )
    
    def _analyze_css_file(self, css_path: str) -> Dict[str, Any]:
        """Analyze CSS file for patterns"""
        try:
            with open(css_path, 'r', encoding='utf-8', errors='ignore') as f:
                css_content = f.read()
        except Exception:
            return {}
        
        analysis = {
            'colors': {},
            'typography': {},
            'layout': 'unknown',
            'breakpoints': []
        }
        
        # Extract color patterns
        color_matches = re.findall(r'color:\s*([^;]+)', css_content, re.IGNORECASE)
        bg_color_matches = re.findall(r'background-color:\s*([^;]+)', css_content, re.IGNORECASE)
        
        all_colors = color_matches + bg_color_matches
        color_counts = {}
        for color in all_colors:
            color = color.strip()
            color_counts[color] = color_counts.get(color, 0) + 1
        
        # Get most common colors
        if color_counts:
            sorted_colors = sorted(color_counts.items(), key=lambda x: x[1], reverse=True)
            analysis['colors'] = dict(sorted_colors[:5])
        
        # Extract typography patterns
        font_families = re.findall(r'font-family:\s*([^;]+)', css_content, re.IGNORECASE)
        font_sizes = re.findall(r'font-size:\s*([^;]+)', css_content, re.IGNORECASE)
        
        if font_families:
            analysis['typography']['primary_font'] = font_families[0].strip()
        if font_sizes:
            analysis['typography']['common_sizes'] = list(set(font_sizes))
        
        # Detect layout patterns
        if 'display: grid' in css_content or 'grid-template' in css_content:
            analysis['layout'] = 'grid'
        elif 'display: flex' in css_content or 'flex-direction' in css_content:
            analysis['layout'] = 'flexbox'
        elif 'float:' in css_content:
            analysis['layout'] = 'float'
        
        # Extract media queries (responsive breakpoints)
        media_queries = re.findall(r'@media[^{]*\([^)]*width[^)]*\)', css_content, re.IGNORECASE)
        analysis['breakpoints'] = list(set(media_queries))
        
        return analysis


class WebsiteMemory:
    """Manages website memory storage and retrieval"""
    
    def __init__(self, storage_path: str = "ai_features/data/memory"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.analyzer = WebsiteAnalyzer()
    
    def create_memory(self, site_path: str, site_url: str = "", site_id: str = None) -> SiteMemory:
        """Create memory for a website"""
        if not site_id:
            site_id = self._generate_site_id(site_path, site_url)
        
        logger.info(f"Creating memory for site: {site_id}")
        
        # Analyze all HTML files
        pages = {}
        html_files = self._find_html_files(site_path)
        
        for html_file in html_files:
            rel_path = os.path.relpath(html_file, site_path)
            page_info = self.analyzer.analyze_html_file(html_file)
            if page_info:
                pages[rel_path] = page_info
        
        # Detect components
        components = self.analyzer.detect_components(pages)
        
        # Analyze style patterns
        style_patterns = self.analyzer.analyze_style_patterns(site_path, pages)
        
        # Build navigation structure
        navigation_structure = self._build_navigation_structure(pages)
        
        # Analyze content patterns
        content_patterns = self._analyze_content_patterns(pages)
        
        # Build file structure
        file_structure = self._build_file_structure(site_path)
        
        # Detect technology stack
        technology_stack = self._detect_technology_stack(site_path, pages)
        
        # Create memory object
        memory = SiteMemory(
            site_id=site_id,
            site_url=site_url,
            converted_path=site_path,
            created_at=datetime.now().isoformat(),
            last_updated=datetime.now().isoformat(),
            technology_stack=technology_stack,
            pages=pages,
            components=components,
            style_patterns=style_patterns,
            navigation_structure=navigation_structure,
            content_patterns=content_patterns,
            file_structure=file_structure,
            metadata={}
        )
        
        # Save memory
        self.save_memory(memory)
        logger.info(f"Created memory for {len(pages)} pages")
        
        return memory
    
    def _generate_site_id(self, site_path: str, site_url: str) -> str:
        """Generate unique site ID"""
        content = f"{site_path}_{site_url}_{datetime.now().isoformat()}"
        return hashlib.md5(content.encode()).hexdigest()[:12]
    
    def _find_html_files(self, site_path: str) -> List[str]:
        """Find all HTML files in site directory"""
        html_files = []
        for root, dirs, files in os.walk(site_path):
            for file in files:
                if file.endswith(('.html', '.htm')):
                    html_files.append(os.path.join(root, file))
        return html_files
    
    def _build_navigation_structure(self, pages: Dict[str, PageInfo]) -> Dict[str, Any]:
        """Build navigation structure from page links"""
        nav_structure = {
            'main_pages': [],
            'hierarchies': {},
            'orphaned_pages': []
        }
        
        # Find pages that are linked from multiple other pages (likely main nav)
        link_counts = {}
        for page_info in pages.values():
            for link in page_info.internal_links:
                clean_link = link.strip('/').replace('index.html', '')
                link_counts[clean_link] = link_counts.get(clean_link, 0) + 1
        
        # Main pages are those linked from multiple pages
        nav_structure['main_pages'] = [
            link for link, count in link_counts.items() 
            if count > 1 and link
        ]
        
        # Find orphaned pages (not linked from anywhere)
        all_page_paths = set(pages.keys())
        linked_pages = set()
        for page_info in pages.values():
            for link in page_info.internal_links:
                clean_link = link.strip('/').replace('index.html', '')
                if clean_link in all_page_paths:
                    linked_pages.add(clean_link)
        
        nav_structure['orphaned_pages'] = list(all_page_paths - linked_pages)
        
        return nav_structure
    
    def _analyze_content_patterns(self, pages: Dict[str, PageInfo]) -> Dict[str, Any]:
        """Analyze content patterns across pages"""
        patterns = {
            'common_headings': {},
            'page_types': {},
            'content_length_distribution': {},
            'form_pages': []
        }
        
        # Analyze heading patterns
        heading_counts = {}
        for page_info in pages.values():
            for heading in page_info.headings:
                heading_text = heading['text'].lower()
                heading_counts[heading_text] = heading_counts.get(heading_text, 0) + 1
        
        patterns['common_headings'] = {
            heading: count for heading, count in heading_counts.items() 
            if count > 1
        }
        
        # Categorize page types based on content
        for page_path, page_info in pages.items():
            if page_info.has_forms:
                patterns['form_pages'].append(page_path)
            
            # Categorize by word count
            if page_info.word_count < 100:
                page_type = 'minimal'
            elif page_info.word_count < 500:
                page_type = 'short'
            elif page_info.word_count < 1500:
                page_type = 'medium'
            else:
                page_type = 'long'
            
            if page_type not in patterns['page_types']:
                patterns['page_types'][page_type] = []
            patterns['page_types'][page_type].append(page_path)
        
        return patterns
    
    def _build_file_structure(self, site_path: str) -> Dict[str, Any]:
        """Build file structure summary"""
        structure = {
            'total_files': 0,
            'file_types': {},
            'directories': [],
            'assets': {
                'images': [],
                'scripts': [],
                'styles': [],
                'other': []
            }
        }
        
        for root, dirs, files in os.walk(site_path):
            rel_root = os.path.relpath(root, site_path)
            if rel_root != '.':
                structure['directories'].append(rel_root)
            
            for file in files:
                structure['total_files'] += 1
                ext = os.path.splitext(file)[1].lower()
                structure['file_types'][ext] = structure['file_types'].get(ext, 0) + 1
                
                rel_path = os.path.relpath(os.path.join(root, file), site_path)
                
                if ext in ['.jpg', '.jpeg', '.png', '.gif', '.svg', '.webp']:
                    structure['assets']['images'].append(rel_path)
                elif ext in ['.js']:
                    structure['assets']['scripts'].append(rel_path)
                elif ext in ['.css']:
                    structure['assets']['styles'].append(rel_path)
                elif ext not in ['.html', '.htm']:
                    structure['assets']['other'].append(rel_path)
        
        return structure
    
    def _detect_technology_stack(self, site_path: str, pages: Dict[str, PageInfo]) -> Dict[str, str]:
        """Detect technology stack used in the website"""
        tech_stack = {
            'framework': 'Unknown',
            'css_framework': 'Unknown',
            'javascript_libraries': [],
            'cms': 'WordPress (converted)',
            'responsive': 'Unknown'
        }
        
        # Analyze scripts and stylesheets across all pages
        all_scripts = set()
        all_styles = set()
        
        for page_info in pages.values():
            all_scripts.update(page_info.scripts)
            all_styles.update(page_info.stylesheets)
        
        # Detect JavaScript libraries
        js_libraries = []
        for script in all_scripts:
            script_name = script.lower()
            if 'jquery' in script_name:
                js_libraries.append('jQuery')
            elif 'bootstrap' in script_name:
                js_libraries.append('Bootstrap JS')
            elif 'vue' in script_name:
                js_libraries.append('Vue.js')
            elif 'react' in script_name:
                js_libraries.append('React')
            elif 'angular' in script_name:
                js_libraries.append('Angular')
        
        tech_stack['javascript_libraries'] = js_libraries
        
        # Detect CSS framework
        for style in all_styles:
            style_name = style.lower()
            if 'bootstrap' in style_name:
                tech_stack['css_framework'] = 'Bootstrap'
            elif 'tailwind' in style_name:
                tech_stack['css_framework'] = 'Tailwind CSS'
            elif 'foundation' in style_name:
                tech_stack['css_framework'] = 'Foundation'
        
        # Check for responsive design
        has_viewport_meta = False
        has_media_queries = False
        
        # This would require deeper CSS analysis
        # For now, assume responsive if using modern frameworks
        if tech_stack['css_framework'] in ['Bootstrap', 'Tailwind CSS', 'Foundation']:
            tech_stack['responsive'] = 'Yes'
        
        return tech_stack
    
    def save_memory(self, memory: SiteMemory) -> bool:
        """Save memory to storage"""
        try:
            memory_file = self.storage_path / f"{memory.site_id}.json"
            
            # Convert dataclasses to dict for JSON serialization
            memory_dict = asdict(memory)
            
            with open(memory_file, 'w', encoding='utf-8') as f:
                json.dump(memory_dict, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved memory to {memory_file}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save memory: {e}")
            return False
    
    def load_memory(self, site_id: str) -> Optional[SiteMemory]:
        """Load memory from storage"""
        try:
            memory_file = self.storage_path / f"{site_id}.json"
            
            if not memory_file.exists():
                return None
            
            with open(memory_file, 'r', encoding='utf-8') as f:
                memory_dict = json.load(f)
            
            # Convert nested dictionaries back to dataclasses
            pages = {}
            for page_path, page_data in memory_dict.get('pages', {}).items():
                if isinstance(page_data, dict):
                    # Convert dict to PageInfo
                    pages[page_path] = PageInfo(
                        path=page_data.get('path', page_path),
                        title=page_data.get('title', ''),
                        content_hash=page_data.get('content_hash', ''),
                        word_count=page_data.get('word_count', 0),
                        has_forms=page_data.get('has_forms', False),
                        external_links=page_data.get('external_links', []),
                        internal_links=page_data.get('internal_links', []),
                        images=page_data.get('images', []),
                        scripts=page_data.get('scripts', []),
                        stylesheets=page_data.get('stylesheets', []),
                        meta_description=page_data.get('meta_description', ''),
                        headings=page_data.get('headings', [])
                    )
                else:
                    pages[page_path] = page_data
            
            components = {}
            for comp_name, comp_data in memory_dict.get('components', {}).items():
                if isinstance(comp_data, dict):
                    # Convert dict to ComponentInfo
                    components[comp_name] = ComponentInfo(
                        type=comp_data.get('type', ''),
                        selector=comp_data.get('selector', ''),
                        content_pattern=comp_data.get('content_pattern', ''),
                        pages_found=comp_data.get('pages_found', []),
                        variations=comp_data.get('variations', [])
                    )
                else:
                    components[comp_name] = comp_data
            
            style_patterns = memory_dict.get('style_patterns', {})
            if isinstance(style_patterns, dict):
                # Convert dict to StylePattern
                style_patterns = StylePattern(
                    framework=style_patterns.get('framework'),
                    color_scheme=style_patterns.get('color_scheme', {}),
                    typography=style_patterns.get('typography', {}),
                    layout_type=style_patterns.get('layout_type', 'unknown'),
                    responsive_breakpoints=style_patterns.get('responsive_breakpoints', [])
                )
            
            # Create SiteMemory with converted objects
            memory = SiteMemory(
                site_id=memory_dict['site_id'],
                site_url=memory_dict.get('site_url', ''),
                converted_path=memory_dict['converted_path'],
                created_at=memory_dict['created_at'],
                last_updated=memory_dict['last_updated'],
                technology_stack=memory_dict.get('technology_stack', {}),
                pages=pages,
                components=components,
                style_patterns=style_patterns,
                navigation_structure=memory_dict.get('navigation_structure', {}),
                content_patterns=memory_dict.get('content_patterns', {}),
                file_structure=memory_dict.get('file_structure', {}),
                metadata=memory_dict.get('metadata', {})
            )
            
            return memory
            
        except Exception as e:
            logger.error(f"Failed to load memory for {site_id}: {e}")
            return None
    
    def list_memories(self) -> List[Dict[str, Any]]:
        """List all stored memories"""
        memories = []
        
        for memory_file in self.storage_path.glob("*.json"):
            try:
                with open(memory_file, 'r', encoding='utf-8') as f:
                    memory_dict = json.load(f)
                
                memories.append({
                    'site_id': memory_dict['site_id'],
                    'site_url': memory_dict.get('site_url', ''),
                    'created_at': memory_dict['created_at'],
                    'page_count': len(memory_dict.get('pages', {})),
                    'file_path': str(memory_file)
                })
                
            except Exception as e:
                logger.error(f"Failed to read memory file {memory_file}: {e}")
        
        return sorted(memories, key=lambda x: x['created_at'], reverse=True)
    
    def delete_memory(self, site_id: str) -> bool:
        """Delete memory from storage"""
        try:
            memory_file = self.storage_path / f"{site_id}.json"
            if memory_file.exists():
                memory_file.unlink()
                logger.info(f"Deleted memory for {site_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to delete memory for {site_id}: {e}")
            return False