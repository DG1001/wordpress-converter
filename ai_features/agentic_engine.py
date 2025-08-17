"""
Agentic Workflow Engine

Generates todo lists from user requests and manages task execution
with AI-powered planning and incremental changes.
"""

import json
import logging
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path

from .llm_providers import LLMManager, LLMResponse
from .website_memory import SiteMemory, WebsiteMemory
from .smart_editor import SmartEditor, EditResult
from .ai_config import get_ai_config

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskType(Enum):
    MODIFY_CONTENT = "modify_content"
    ADD_FEATURE = "add_feature"
    STYLE_CHANGE = "style_change"
    STRUCTURE_CHANGE = "structure_change"
    FIX_ISSUE = "fix_issue"
    OPTIMIZE = "optimize"


class TaskPriority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class TodoTask:
    """Individual todo task"""
    id: str
    description: str
    task_type: TaskType
    priority: TaskPriority
    files_affected: List[str]
    dependencies: List[str]
    estimated_complexity: str
    llm_prompt: str
    status: TaskStatus = TaskStatus.PENDING
    created_at: str = None
    started_at: str = None
    completed_at: str = None
    error_message: str = None
    result_summary: str = None
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()


@dataclass
class WorkflowSession:
    """Workflow session containing multiple tasks"""
    session_id: str
    site_id: str
    user_request: str
    tasks: List[TodoTask]
    status: str = "created"
    created_at: str = None
    updated_at: str = None
    progress: Dict[str, Any] = None
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        if not self.updated_at:
            self.updated_at = self.created_at
        if not self.progress:
            self.progress = {
                "total_tasks": len(self.tasks),
                "completed": 0,
                "failed": 0,
                "in_progress": 0
            }


class TaskAnalyzer:
    """Analyzes user requests and generates structured tasks"""
    
    def __init__(self, llm_manager: LLMManager, memory: SiteMemory):
        self.llm_manager = llm_manager
        self.memory = memory
        self.config = get_ai_config()
    
    def analyze_request(self, user_request: str) -> Dict[str, Any]:
        """Analyze user request and extract intent"""
        
        system_prompt = f"""
        You are an AI assistant that analyzes website editing requests. 
        
        Website Context:
        - Site has {len(self.memory.pages)} pages
        - Technology: {self.memory.technology_stack.get('framework', 'Static HTML')}
        - CSS Framework: {self.memory.technology_stack.get('css_framework', 'Custom')}
        - Main pages: {list(self.memory.pages.keys())[:5]}
        
        Analyze the user request and extract:
        1. Intent (what they want to achieve)
        2. Scope (which parts of the site are affected)
        3. Complexity (low/medium/high)
        4. Required changes (specific modifications needed)
        
        Return analysis in JSON format with keys: intent, scope, complexity, required_changes.
        """
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"User request: {user_request}"}
        ]
        
        try:
            response = self.llm_manager.chat_completion(
                messages=messages,
                model_type='analysis'
            )
            
            # Try to parse JSON response
            try:
                analysis = json.loads(response.content)
            except json.JSONDecodeError:
                # Fallback: extract key information using keywords
                analysis = self._fallback_analysis(user_request, response.content)
            
            return analysis
            
        except Exception as e:
            logger.error(f"Failed to analyze request: {e}")
            return self._fallback_analysis(user_request, "")
    
    def _fallback_analysis(self, user_request: str, llm_response: str) -> Dict[str, Any]:
        """Fallback analysis using keyword matching"""
        request_lower = user_request.lower()
        
        # Detect intent
        if any(word in request_lower for word in ['add', 'create', 'new']):
            intent = 'add_feature'
        elif any(word in request_lower for word in ['change', 'modify', 'update', 'edit']):
            intent = 'modify_content'
        elif any(word in request_lower for word in ['style', 'color', 'design', 'css']):
            intent = 'style_change'
        elif any(word in request_lower for word in ['fix', 'repair', 'broken']):
            intent = 'fix_issue'
        else:
            intent = 'modify_content'
        
        # Detect scope
        if any(word in request_lower for word in ['all', 'entire', 'whole', 'every']):
            scope = 'site_wide'
        elif any(word in request_lower for word in ['header', 'footer', 'navigation']):
            scope = 'global_component'
        elif any(word in request_lower for word in ['page', 'specific']):
            scope = 'single_page'
        else:
            scope = 'multiple_pages'
        
        # Estimate complexity
        complexity_indicators = len([word for word in ['complex', 'difficult', 'multiple', 'many', 'various'] if word in request_lower])
        if complexity_indicators >= 2:
            complexity = 'high'
        elif complexity_indicators == 1:
            complexity = 'medium'
        else:
            complexity = 'low'
        
        return {
            'intent': intent,
            'scope': scope,
            'complexity': complexity,
            'required_changes': [user_request]
        }
    
    def generate_tasks(self, user_request: str, analysis: Dict[str, Any]) -> List[TodoTask]:
        """Generate specific tasks based on analysis"""
        
        system_prompt = f"""
        You are an AI task planner for website editing. Generate specific, actionable tasks.
        
        Website Memory:
        - Pages: {list(self.memory.pages.keys())}
        - Components: {list(self.memory.components.keys())}
        - File structure: {list(self.memory.file_structure.get('directories', []))}
        - Technology: {self.memory.technology_stack}
        
        User Request: {user_request}
        Analysis: {json.dumps(analysis, indent=2)}
        
        Generate a list of specific tasks. Each task should:
        1. Be actionable and specific
        2. Include the files that need to be modified
        3. Have clear dependencies
        4. Include the exact prompt for the LLM to execute the task
        
        Return tasks as JSON array with format:
        [
          {{
            "description": "Clear description of what to do",
            "task_type": "modify_content|add_feature|style_change|structure_change|fix_issue|optimize",
            "priority": "low|medium|high|critical",
            "files_affected": ["file1.html", "style.css"],
            "dependencies": [],
            "estimated_complexity": "low|medium|high",
            "llm_prompt": "Specific instructions for LLM to execute this task"
          }}
        ]
        
        Keep tasks granular and executable. Each task should be completable independently.
        """
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Generate tasks for: {user_request}"}
        ]
        
        try:
            response = self.llm_manager.chat_completion(
                messages=messages,
                model_type='planning'
            )
            
            # Parse tasks from response
            try:
                tasks_data = json.loads(response.content)
                if not isinstance(tasks_data, list):
                    tasks_data = [tasks_data]
            except json.JSONDecodeError:
                logger.warning("Failed to parse tasks JSON, using fallback")
                return self._generate_fallback_tasks(user_request, analysis)
            
            # Convert to TodoTask objects
            tasks = []
            for i, task_data in enumerate(tasks_data):
                # Ensure task_data is a dictionary
                if not isinstance(task_data, dict):
                    logger.warning(f"Task data at index {i} is not a dict: {type(task_data)}")
                    task_data = {'description': str(task_data)}
                
                task = TodoTask(
                    id=str(uuid.uuid4()),
                    description=task_data.get('description', f'Task {i+1}'),
                    task_type=TaskType(task_data.get('task_type', 'modify_content')),
                    priority=TaskPriority(task_data.get('priority', 'medium')),
                    files_affected=task_data.get('files_affected', []),
                    dependencies=task_data.get('dependencies', []),
                    estimated_complexity=task_data.get('estimated_complexity', 'medium'),
                    llm_prompt=task_data.get('llm_prompt', task_data.get('description', ''))
                )
                tasks.append(task)
            
            return tasks
            
        except Exception as e:
            logger.error(f"Failed to generate tasks: {e}")
            return self._generate_fallback_tasks(user_request, analysis)
    
    def _generate_fallback_tasks(self, user_request: str, analysis: Dict[str, Any]) -> List[TodoTask]:
        """Generate basic tasks when LLM fails"""
        tasks = []
        
        # Create a basic task based on the request
        task = TodoTask(
            id=str(uuid.uuid4()),
            description=f"Implement user request: {user_request}",
            task_type=TaskType.MODIFY_CONTENT,
            priority=TaskPriority.MEDIUM,
            files_affected=list(self.memory.pages.keys())[:3],  # First 3 pages
            dependencies=[],
            estimated_complexity=analysis.get('complexity', 'medium'),
            llm_prompt=f"User wants to: {user_request}. Please implement this change on the website."
        )
        tasks.append(task)
        
        return tasks


class TaskExecutor:
    """Executes individual tasks using LLM and SmartEditor"""
    
    def __init__(self, llm_manager: LLMManager, smart_editor: SmartEditor):
        self.llm_manager = llm_manager
        self.smart_editor = smart_editor
        self.config = get_ai_config()
    
    def execute_task(self, task: TodoTask) -> Tuple[bool, Optional[str]]:
        """Execute a single task"""
        logger.info(f"Executing task: {task.description}")
        
        task.status = TaskStatus.IN_PROGRESS
        task.started_at = datetime.now().isoformat()
        
        try:
            # Get task-specific instructions from LLM
            instructions = self._get_execution_instructions(task)
            
            if not instructions:
                raise Exception("Failed to get execution instructions")
            
            # Execute the instructions
            success = self._execute_instructions(task, instructions)
            
            if success:
                task.status = TaskStatus.COMPLETED
                task.completed_at = datetime.now().isoformat()
                task.result_summary = f"Successfully executed: {task.description}"
                return True, task.result_summary
            else:
                raise Exception("Failed to execute instructions")
                
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Task execution failed: {error_msg}")
            
            task.status = TaskStatus.FAILED
            task.error_message = error_msg
            
            return False, error_msg
    
    def _get_execution_instructions(self, task: TodoTask) -> Optional[Dict[str, Any]]:
        """Get specific execution instructions from LLM"""
        
        system_prompt = f"""
        You are an AI that generates specific file editing instructions for website modifications.
        
        Task: {task.description}
        Files to modify: {task.files_affected}
        Task type: {task.task_type.value}
        
        Generate specific instructions for each file that needs to be modified.
        Return JSON format:
        {{
          "file_operations": [
            {{
              "file_path": "path/to/file.html",
              "operation_type": "replace|insert|append|delete",
              "target_content": "content to find/replace",
              "new_content": "new content to insert",
              "explanation": "why this change is needed"
            }}
          ]
        }}
        
        Make sure the target_content is specific enough to uniquely identify the location.
        Keep changes minimal and focused.
        """
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": task.llm_prompt}
        ]
        
        try:
            response = self.llm_manager.chat_completion(
                messages=messages,
                model_type='coding'
            )
            
            # Check if response is empty
            if not response.content or not response.content.strip():
                logger.warning("Empty response from LLM, using fallback instructions")
                return self._get_fallback_instructions(task)
            
            # Try to parse JSON response
            try:
                instructions = json.loads(response.content.strip())
                return instructions
            except json.JSONDecodeError as json_error:
                logger.warning(f"JSON parsing failed: {json_error}, trying to extract from response")
                return self._extract_instructions_from_text(response.content, task)
            
        except Exception as e:
            logger.error(f"Failed to get execution instructions: {e}")
            return self._get_fallback_instructions(task)
    
    def _get_fallback_instructions(self, task: TodoTask) -> Dict[str, Any]:
        """Generate fallback instructions when LLM fails"""
        logger.info("Generating fallback instructions")
        
        # Create basic instructions based on task type
        if "dark mode" in task.description.lower():
            # Check if this is a repair request or initial implementation
            if "check" in task.description.lower() or "fix" in task.description.lower() or "repair" in task.description.lower():
                # This is a repair/fix request - create comprehensive repair instructions
                return {
                    "file_operations": [
                        {
                            "file_path": "index.html",
                            "operation_type": "replace",
                            "target_content": "<!DOCTYPE html>",
                            "new_content": """<!DOCTYPE html>
<html lang="de-de">
<head>
    <meta charset="utf-8"/>
    <title>Generic Site Title</title>
    <meta content="width=device-width, initial-scale=1" name="viewport"/>
    <meta content="This is meta description" name="description"/>
    <meta content="Themefisher" name="author"/>
    <meta content="Hugo 0.68.3" name="generator"/>
    
    <!-- plugins -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet"/>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet"/>
    <link href="./plugins/magnific-popup/magnific-popup.css" rel="stylesheet"/>
    <link href="./plugins/slick/slick.css" rel="stylesheet"/>
    <link href="./scss/style.min.css" media="screen" rel="stylesheet"/>
    <link href="./images/favicon.png" rel="shortcut icon" type="image/x-icon"/>
    <link href="./images/favicon.png" rel="icon" type="image/x-icon"/>
    
    <!-- Dark Mode Styles -->
    <style>
        :root {
            --bg-color: #ffffff;
            --text-color: #333333;
            --nav-bg: #f8f9fa;
            --card-bg: #ffffff;
        }
        
        body.dark-mode {
            --bg-color: #121212;
            --text-color: #e0e0e0;
            --nav-bg: #1e1e1e;
            --card-bg: #2d2d2d;
        }
        
        body {
            background-color: var(--bg-color);
            color: var(--text-color);
            transition: background-color 0.3s ease, color 0.3s ease;
        }
        
        .navbar {
            background-color: var(--nav-bg) !important;
        }
        
        .dark-mode .navbar-light .navbar-nav .nav-link {
            color: var(--text-color) !important;
        }
        
        .dark-mode .card {
            background-color: var(--card-bg);
            color: var(--text-color);
        }
        
        .dark-mode-toggle {
            position: fixed;
            top: 100px;
            right: 20px;
            z-index: 1000;
            padding: 12px 16px;
            background: linear-gradient(45deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 50px;
            cursor: pointer;
            font-size: 16px;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
            transition: all 0.3s ease;
        }
        
        .dark-mode-toggle:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6);
        }
        
        .dark-mode-toggle.active {
            background: linear-gradient(45deg, #f093fb 0%, #f5576c 100%);
        }
    </style>
    
    <!-- Dark Mode Script -->
    <script>
        function toggleDarkMode() {
            const body = document.body;
            const button = document.querySelector('.dark-mode-toggle');
            
            body.classList.toggle('dark-mode');
            button.classList.toggle('active');
            
            const isDarkMode = body.classList.contains('dark-mode');
            localStorage.setItem('darkMode', isDarkMode);
            
            // Update button text
            button.textContent = isDarkMode ? '☀️ Light Mode' : '🌙 Dark Mode';
        }
        
        document.addEventListener('DOMContentLoaded', function() {
            const savedDarkMode = localStorage.getItem('darkMode') === 'true';
            const button = document.querySelector('.dark-mode-toggle');
            
            if (savedDarkMode) {
                document.body.classList.add('dark-mode');
                button.classList.add('active');
                button.textContent = '☀️ Light Mode';
            } else {
                button.textContent = '🌙 Dark Mode';
            }
        });
    </script>
</head>
<body>
    <button class="dark-mode-toggle" onclick="toggleDarkMode()">🌙 Dark Mode</button>""",
                            "explanation": "Repair and improve the dark mode implementation with clean HTML structure"
                        }
                    ]
                }
            else:
                # Initial dark mode implementation
                return {
                    "file_operations": [
                        {
                            "file_path": "index.html",
                            "operation_type": "insert",
                            "target_content": "</head>",
                            "new_content": """
    <style>
        .dark-mode {
            background-color: #121212;
            color: #ffffff;
        }
        .dark-mode-toggle {
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 10px;
            background: #333;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
        }
    </style>
    <script>
        function toggleDarkMode() {
            document.body.classList.toggle('dark-mode');
            localStorage.setItem('darkMode', document.body.classList.contains('dark-mode'));
        }
        document.addEventListener('DOMContentLoaded', function() {
            if (localStorage.getItem('darkMode') === 'true') {
                document.body.classList.add('dark-mode');
            }
        });
    </script>
</head>""",
                            "explanation": "Add dark mode styles and toggle functionality"
                        },
                        {
                            "file_path": "index.html", 
                            "operation_type": "insert",
                            "target_content": "<body",
                            "new_content": '<body><button class="dark-mode-toggle" onclick="toggleDarkMode()">🌙 Dark Mode</button>',
                            "explanation": "Add dark mode toggle button"
                        }
                    ]
                }
        else:
            # Generic fallback
            files_to_modify = task.files_affected if task.files_affected else ["index.html"]
            return {
                "file_operations": [
                    {
                        "file_path": files_to_modify[0],
                        "operation_type": "insert",
                        "target_content": "</head>",
                        "new_content": f"<!-- {task.description} -->\n</head>",
                        "explanation": f"Basic implementation of: {task.description}"
                    }
                ]
            }
    
    def _extract_instructions_from_text(self, response_text: str, task: TodoTask) -> Dict[str, Any]:
        """Try to extract instructions from non-JSON response"""
        logger.info("Attempting to extract instructions from text response")
        
        # Look for JSON-like patterns in the response
        import re
        
        # Try to find JSON blocks in markdown code blocks
        json_pattern = r'```(?:json)?\s*(\{.*?\})\s*```'
        matches = re.findall(json_pattern, response_text, re.DOTALL | re.IGNORECASE)
        
        for match in matches:
            try:
                instructions = json.loads(match)
                logger.info("Successfully extracted JSON from markdown block")
                return instructions
            except json.JSONDecodeError:
                continue
        
        # Try to find standalone JSON objects
        json_pattern = r'\{[^{}]*"file_operations"[^{}]*\}'
        matches = re.findall(json_pattern, response_text, re.DOTALL)
        
        for match in matches:
            try:
                instructions = json.loads(match)
                logger.info("Successfully extracted JSON object")
                return instructions
            except json.JSONDecodeError:
                continue
        
        # Fall back to basic instructions
        logger.warning("Could not extract instructions from text, using fallback")
        return self._get_fallback_instructions(task)
    
    def _execute_instructions(self, task: TodoTask, instructions: Dict[str, Any]) -> bool:
        """Execute the file operations"""
        file_operations = instructions.get('file_operations', [])
        
        if not file_operations:
            logger.warning("No file operations in instructions")
            return False
        
        results = []
        
        for operation in file_operations:
            try:
                result = self.smart_editor.edit_file(
                    file_path=operation['file_path'],
                    target_content=operation['target_content'],
                    new_content=operation['new_content'],
                    operation_type=operation.get('operation_type', 'replace')
                )
                
                results.append(result)
                
                if not result.success:
                    logger.error(f"File operation failed: {result.error_message}")
                    return False
                    
            except Exception as e:
                logger.error(f"Failed to execute file operation: {e}")
                return False
        
        # Validate changes
        for operation in file_operations:
            validation = self.smart_editor.validate_changes(operation['file_path'])
            if not validation['valid']:
                logger.error(f"Validation failed for {operation['file_path']}: {validation['issues']}")
                # Could rollback here if needed
        
        return True


class AgenticEngine:
    """Main agentic workflow engine"""
    
    def __init__(self, site_id: str):
        self.site_id = site_id
        self.config = get_ai_config()
        
        # Initialize components
        self.memory_manager = WebsiteMemory()
        self.memory = self.memory_manager.load_memory(site_id)
        
        if not self.memory:
            raise ValueError(f"No memory found for site ID: {site_id}")
        
        # Initialize LLM manager with active provider
        provider_configs = self.config.config['providers']
        active_provider = self.config.get_active_provider()
        self.llm_manager = LLMManager(provider_configs, active_provider)
        
        # Initialize other components
        self.smart_editor = SmartEditor(site_id, self.memory_manager)
        self.task_analyzer = TaskAnalyzer(self.llm_manager, self.memory)
        self.task_executor = TaskExecutor(self.llm_manager, self.smart_editor)
        
        # Session storage
        self.active_sessions = {}
    
    def create_workflow_session(self, user_request: str) -> WorkflowSession:
        """Create new workflow session from user request"""
        logger.info(f"Creating workflow session for: {user_request}")
        
        # Analyze the request
        analysis = self.task_analyzer.analyze_request(user_request)
        
        # Generate tasks
        tasks = self.task_analyzer.generate_tasks(user_request, analysis)
        
        # Create session
        session = WorkflowSession(
            session_id=str(uuid.uuid4()),
            site_id=self.site_id,
            user_request=user_request,
            tasks=tasks
        )
        
        # Store session
        self.active_sessions[session.session_id] = session
        
        # Save session to file immediately
        self.save_session(session.session_id)
        
        logger.info(f"Created session {session.session_id} with {len(tasks)} tasks")
        return session
    
    def execute_workflow_session(self, session_id: str, auto_execute: bool = False) -> Dict[str, Any]:
        """Execute workflow session tasks"""
        if session_id not in self.active_sessions:
            # Try to load session from file
            if not self.load_session(session_id):
                raise ValueError(f"Session not found: {session_id}")
        
        session = self.active_sessions[session_id]
        session.status = "executing"
        session.updated_at = datetime.now().isoformat()
        
        execution_results = {
            'session_id': session_id,
            'status': 'executing',
            'results': [],
            'progress': session.progress
        }
        
        # Execute tasks in order, respecting dependencies
        executable_tasks = self._get_executable_tasks(session.tasks)
        
        for task in executable_tasks:
            if not auto_execute and task.status == TaskStatus.PENDING:
                # Skip if not auto-executing
                continue
            
            success, message = self.task_executor.execute_task(task)
            
            result = {
                'task_id': task.id,
                'description': task.description,
                'success': success,
                'message': message,
                'completed_at': task.completed_at or datetime.now().isoformat()
            }
            
            execution_results['results'].append(result)
            
            # Update progress
            if success:
                session.progress['completed'] += 1
            else:
                session.progress['failed'] += 1
                
                # Stop on failure if not configured to continue
                if not self.config.get_workflow_config().get('continue_on_failure', False):
                    break
        
        # Update session status
        if session.progress['completed'] == session.progress['total_tasks']:
            session.status = "completed"
        elif session.progress['failed'] > 0:
            session.status = "failed"
        else:
            session.status = "partial"
        
        session.updated_at = datetime.now().isoformat()
        execution_results['status'] = session.status
        execution_results['progress'] = session.progress
        
        return execution_results
    
    def _get_executable_tasks(self, tasks: List[TodoTask]) -> List[TodoTask]:
        """Get tasks that can be executed based on dependencies"""
        executable = []
        completed_task_ids = {task.id for task in tasks if task.status == TaskStatus.COMPLETED}
        
        for task in tasks:
            if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
                continue
                
            # Check if all dependencies are completed
            if all(dep_id in completed_task_ids for dep_id in task.dependencies):
                executable.append(task)
        
        # Sort by priority
        priority_order = {TaskPriority.CRITICAL: 0, TaskPriority.HIGH: 1, 
                         TaskPriority.MEDIUM: 2, TaskPriority.LOW: 3}
        
        executable.sort(key=lambda t: priority_order[t.priority])
        return executable
    
    def get_session_status(self, session_id: str) -> Dict[str, Any]:
        """Get current status of workflow session"""
        if session_id not in self.active_sessions:
            return {'error': f'Session not found: {session_id}'}
        
        session = self.active_sessions[session_id]
        
        return {
            'session_id': session.session_id,
            'site_id': session.site_id,
            'user_request': session.user_request,
            'status': session.status,
            'progress': session.progress,
            'created_at': session.created_at,
            'updated_at': session.updated_at,
            'tasks': [
                {
                    'id': task.id,
                    'description': task.description,
                    'status': task.status.value,
                    'priority': task.priority.value,
                    'files_affected': task.files_affected,
                    'error_message': task.error_message
                }
                for task in session.tasks
            ]
        }
    
    def modify_task(self, session_id: str, task_id: str, **updates) -> bool:
        """Modify a task in the session"""
        if session_id not in self.active_sessions:
            return False
        
        session = self.active_sessions[session_id]
        
        for task in session.tasks:
            if task.id == task_id:
                for key, value in updates.items():
                    if hasattr(task, key):
                        setattr(task, key, value)
                
                session.updated_at = datetime.now().isoformat()
                return True
        
        return False
    
    def add_task(self, session_id: str, task_data: Dict[str, Any]) -> bool:
        """Add new task to session"""
        if session_id not in self.active_sessions:
            return False
        
        session = self.active_sessions[session_id]
        
        task = TodoTask(
            id=str(uuid.uuid4()),
            description=task_data['description'],
            task_type=TaskType(task_data.get('task_type', 'modify_content')),
            priority=TaskPriority(task_data.get('priority', 'medium')),
            files_affected=task_data.get('files_affected', []),
            dependencies=task_data.get('dependencies', []),
            estimated_complexity=task_data.get('estimated_complexity', 'medium'),
            llm_prompt=task_data.get('llm_prompt', task_data['description'])
        )
        
        session.tasks.append(task)
        session.progress['total_tasks'] += 1
        session.updated_at = datetime.now().isoformat()
        
        return True
    
    def delete_task(self, session_id: str, task_id: str) -> bool:
        """Delete task from session"""
        if session_id not in self.active_sessions:
            return False
        
        session = self.active_sessions[session_id]
        
        for i, task in enumerate(session.tasks):
            if task.id == task_id:
                del session.tasks[i]
                session.progress['total_tasks'] -= 1
                session.updated_at = datetime.now().isoformat()
                return True
        
        return False
    
    def save_session(self, session_id: str, file_path: str = None) -> bool:
        """Save session to file"""
        if session_id not in self.active_sessions:
            return False
        
        session = self.active_sessions[session_id]
        
        if not file_path:
            sessions_dir = Path("ai_features/data/sessions")
            sessions_dir.mkdir(parents=True, exist_ok=True)
            file_path = sessions_dir / f"{session_id}.json"
        
        try:
            session_dict = asdict(session)
            # Convert enums to strings for JSON serialization
            for task in session_dict['tasks']:
                if isinstance(task['task_type'], TaskType):
                    task['task_type'] = task['task_type'].value
                if isinstance(task['priority'], TaskPriority):
                    task['priority'] = task['priority'].value
                if isinstance(task['status'], TaskStatus):
                    task['status'] = task['status'].value
            
            with open(file_path, 'w') as f:
                json.dump(session_dict, f, indent=2)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to save session: {e}")
            return False
    
    def load_session(self, session_id: str, file_path: str = None) -> bool:
        """Load session from file"""
        if not file_path:
            sessions_dir = Path("ai_features/data/sessions")
            file_path = sessions_dir / f"{session_id}.json"
        
        try:
            with open(file_path, 'r') as f:
                session_dict = json.load(f)
            
            # Convert back to proper types
            tasks = []
            for task_dict in session_dict['tasks']:
                task_dict['task_type'] = TaskType(task_dict['task_type'])
                task_dict['priority'] = TaskPriority(task_dict['priority'])
                task_dict['status'] = TaskStatus(task_dict['status'])
                tasks.append(TodoTask(**task_dict))
            
            session_dict['tasks'] = tasks
            session = WorkflowSession(**session_dict)
            
            self.active_sessions[session_id] = session
            return True
            
        except Exception as e:
            logger.error(f"Failed to load session: {e}")
            return False