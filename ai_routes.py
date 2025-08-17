"""
AI Routes for Flask Application

New routes for AI-powered website editing functionality.
"""

import os
import json
import logging
from flask import Blueprint, request, jsonify, render_template
from flask_socketio import emit
from urllib.parse import urlparse

from ai_features import LLMProviderFactory, WebsiteMemory, AgenticEngine, SmartEditor
from ai_features.ai_config import get_ai_config

logger = logging.getLogger(__name__)

# Create Blueprint for AI routes
ai_bp = Blueprint('ai', __name__, url_prefix='/ai')


@ai_bp.route('/status')
def ai_status():
    """Get AI system status"""
    try:
        config = get_ai_config()
        provider_status = {}
        
        # Check provider configurations
        for provider_name in config.config['providers']:
            validation = config.validate_provider_config(provider_name)
            provider_status[provider_name] = validation
        
        return jsonify({
            'status': 'operational',
            'active_provider': config.get_active_provider(),
            'providers': provider_status,
            'memory_storage': os.path.exists('ai_features/data/memory'),
            'sessions_storage': os.path.exists('ai_features/data/sessions')
        })
        
    except Exception as e:
        logger.error(f"Error getting AI status: {e}")
        return jsonify({'status': 'error', 'error': str(e)}), 500


@ai_bp.route('/config', methods=['GET', 'POST'])
def ai_config():
    """Get or update AI configuration"""
    config = get_ai_config()
    
    if request.method == 'GET':
        return jsonify({
            'providers': config.config['providers'],
            'active_provider': config.get_active_provider(),
            'memory': config.get_memory_config(),
            'workflow': config.get_workflow_config()
        })
    
    elif request.method == 'POST':
        try:
            data = request.get_json()
            
            if 'active_provider' in data:
                success = config.set_active_provider(data['active_provider'])
                if not success:
                    return jsonify({'error': 'Invalid provider name'}), 400
            
            if 'providers' in data:
                for provider_name, provider_config in data['providers'].items():
                    config.update_provider_config(provider_name, provider_config)
            
            # Save configuration
            if config.save_config():
                return jsonify({'message': 'Configuration updated successfully'})
            else:
                return jsonify({'error': 'Failed to save configuration'}), 500
                
        except Exception as e:
            logger.error(f"Error updating AI config: {e}")
            return jsonify({'error': str(e)}), 500


@ai_bp.route('/memory')
def list_memories():
    """List all website memories"""
    try:
        memory_manager = WebsiteMemory()
        memories = memory_manager.list_memories()
        return jsonify(memories)
    except Exception as e:
        logger.error(f"Error listing memories: {e}")
        return jsonify({'error': str(e)}), 500


@ai_bp.route('/memory/<site_id>')
def get_memory(site_id):
    """Get specific website memory"""
    try:
        memory_manager = WebsiteMemory()
        memory = memory_manager.load_memory(site_id)
        
        if not memory:
            return jsonify({'error': 'Memory not found'}), 404
        
        # Convert to dict for JSON serialization with safe attribute access
        memory_dict = {
            'site_id': memory.site_id,
            'site_url': memory.site_url,
            'converted_path': memory.converted_path,
            'created_at': memory.created_at,
            'last_updated': memory.last_updated,
            'technology_stack': memory.technology_stack,
            'pages': {},
            'components': {},
            'navigation_structure': memory.navigation_structure,
            'content_patterns': memory.content_patterns,
            'file_structure': memory.file_structure
        }
        
        # Safe conversion of pages
        for k, v in memory.pages.items():
            if hasattr(v, 'title'):
                # It's a PageInfo object
                memory_dict['pages'][k] = {
                    'title': v.title,
                    'word_count': v.word_count,
                    'has_forms': v.has_forms,
                    'external_links': len(v.external_links),
                    'internal_links': len(v.internal_links),
                    'images': len(v.images)
                }
            elif isinstance(v, dict):
                # It's already a dict
                memory_dict['pages'][k] = {
                    'title': v.get('title', ''),
                    'word_count': v.get('word_count', 0),
                    'has_forms': v.get('has_forms', False),
                    'external_links': len(v.get('external_links', [])),
                    'internal_links': len(v.get('internal_links', [])),
                    'images': len(v.get('images', []))
                }
        
        # Safe conversion of components
        for k, v in memory.components.items():
            if hasattr(v, 'type'):
                # It's a ComponentInfo object
                memory_dict['components'][k] = {
                    'type': v.type,
                    'pages_found': len(v.pages_found)
                }
            elif isinstance(v, dict):
                # It's already a dict
                memory_dict['components'][k] = {
                    'type': v.get('type', ''),
                    'pages_found': len(v.get('pages_found', []))
                }
        
        return jsonify(memory_dict)
        
    except Exception as e:
        logger.error(f"Error getting memory for {site_id}: {e}")
        return jsonify({'error': str(e)}), 500


@ai_bp.route('/memory/<site_id>', methods=['DELETE'])
def delete_memory(site_id):
    """Delete website memory"""
    try:
        memory_manager = WebsiteMemory()
        success = memory_manager.delete_memory(site_id)
        
        if success:
            return jsonify({'message': 'Memory deleted successfully'})
        else:
            return jsonify({'error': 'Memory not found or could not be deleted'}), 404
            
    except Exception as e:
        logger.error(f"Error deleting memory for {site_id}: {e}")
        return jsonify({'error': str(e)}), 500


@ai_bp.route('/analyze/<path:site_path>', methods=['POST'])
def analyze_site(site_path):
    """Analyze a converted site and create memory"""
    try:
        full_path = os.path.join('scraped_sites', site_path)
        if not os.path.exists(full_path) or not os.path.isdir(full_path):
            return jsonify({'error': 'Site not found'}), 404
        
        # Extract site URL from project data if available
        site_url = ""
        data = request.get_json() or {}
        site_url = data.get('site_url', '')
        
        # Create memory
        memory_manager = WebsiteMemory()
        memory = memory_manager.create_memory(full_path, site_url)
        
        return jsonify({
            'message': 'Site analyzed successfully',
            'site_id': memory.site_id,
            'pages_found': len(memory.pages),
            'components_detected': len(memory.components),
            'technology_stack': memory.technology_stack
        })
        
    except Exception as e:
        logger.error(f"Error analyzing site {site_path}: {e}")
        return jsonify({'error': str(e)}), 500


@ai_bp.route('/workflow/create', methods=['POST'])
def create_workflow():
    """Create new AI workflow session"""
    try:
        data = request.get_json()
        
        if not data or 'site_id' not in data or 'user_request' not in data:
            return jsonify({'error': 'site_id and user_request are required'}), 400
        
        site_id = data['site_id']
        user_request = data['user_request']
        
        # Initialize agentic engine
        engine = AgenticEngine(site_id)
        
        # Create workflow session
        session = engine.create_workflow_session(user_request)
        
        return jsonify({
            'session_id': session.session_id,
            'user_request': session.user_request,
            'tasks_count': len(session.tasks),
            'status': session.status,
            'tasks': [
                {
                    'id': task.id,
                    'description': task.description,
                    'task_type': task.task_type.value,
                    'priority': task.priority.value,
                    'estimated_complexity': task.estimated_complexity,
                    'files_affected': task.files_affected,
                    'dependencies': task.dependencies
                }
                for task in session.tasks
            ]
        })
        
    except Exception as e:
        logger.error(f"Error creating workflow: {e}")
        return jsonify({'error': str(e)}), 500


@ai_bp.route('/workflow/<session_id>/status')
def get_workflow_status(session_id):
    """Get workflow session status"""
    try:
        # We need to find which site this session belongs to
        # For now, we'll try to load from session storage
        from pathlib import Path
        sessions_dir = Path("ai_features/data/sessions")
        session_file = sessions_dir / f"{session_id}.json"
        
        if not session_file.exists():
            return jsonify({'error': 'Session not found'}), 404
        
        with open(session_file, 'r') as f:
            session_data = json.load(f)
        
        site_id = session_data.get('site_id')
        if not site_id:
            return jsonify({'error': 'Invalid session data'}), 500
        
        engine = AgenticEngine(site_id)
        engine.load_session(session_id)
        
        status = engine.get_session_status(session_id)
        return jsonify(status)
        
    except Exception as e:
        logger.error(f"Error getting workflow status for {session_id}: {e}")
        return jsonify({'error': str(e)}), 500


@ai_bp.route('/workflow/<session_id>/execute', methods=['POST'])
def execute_workflow(session_id):
    """Execute workflow session"""
    try:
        data = request.get_json() or {}
        auto_execute = data.get('auto_execute', False)
        
        # Load session to get site_id
        from pathlib import Path
        sessions_dir = Path("ai_features/data/sessions")
        session_file = sessions_dir / f"{session_id}.json"
        
        if not session_file.exists():
            return jsonify({'error': 'Session not found'}), 404
        
        with open(session_file, 'r') as f:
            session_data = json.load(f)
        
        site_id = session_data.get('site_id')
        engine = AgenticEngine(site_id)
        engine.load_session(session_id)
        
        # Execute workflow
        results = engine.execute_workflow_session(session_id, auto_execute)
        
        # Save session after execution
        engine.save_session(session_id)
        
        return jsonify(results)
        
    except Exception as e:
        logger.error(f"Error executing workflow {session_id}: {e}")
        return jsonify({'error': str(e)}), 500


@ai_bp.route('/workflow/<session_id>/task/<task_id>', methods=['PUT'])
def modify_task(session_id, task_id):
    """Modify a task in workflow session"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Load session to get site_id
        from pathlib import Path
        sessions_dir = Path("ai_features/data/sessions")
        session_file = sessions_dir / f"{session_id}.json"
        
        if not session_file.exists():
            return jsonify({'error': 'Session not found'}), 404
        
        with open(session_file, 'r') as f:
            session_data = json.load(f)
        
        site_id = session_data.get('site_id')
        engine = AgenticEngine(site_id)
        engine.load_session(session_id)
        
        # Modify task
        success = engine.modify_task(session_id, task_id, **data)
        
        if success:
            engine.save_session(session_id)
            return jsonify({'message': 'Task modified successfully'})
        else:
            return jsonify({'error': 'Task not found or could not be modified'}), 404
            
    except Exception as e:
        logger.error(f"Error modifying task {task_id} in session {session_id}: {e}")
        return jsonify({'error': str(e)}), 500


@ai_bp.route('/workflow/<session_id>/task', methods=['POST'])
def add_task(session_id):
    """Add new task to workflow session"""
    try:
        data = request.get_json()
        if not data or 'description' not in data:
            return jsonify({'error': 'Task description is required'}), 400
        
        # Load session to get site_id
        from pathlib import Path
        sessions_dir = Path("ai_features/data/sessions")
        session_file = sessions_dir / f"{session_id}.json"
        
        if not session_file.exists():
            return jsonify({'error': 'Session not found'}), 404
        
        with open(session_file, 'r') as f:
            session_data = json.load(f)
        
        site_id = session_data.get('site_id')
        engine = AgenticEngine(site_id)
        engine.load_session(session_id)
        
        # Add task
        success = engine.add_task(session_id, data)
        
        if success:
            engine.save_session(session_id)
            return jsonify({'message': 'Task added successfully'})
        else:
            return jsonify({'error': 'Could not add task'}), 500
            
    except Exception as e:
        logger.error(f"Error adding task to session {session_id}: {e}")
        return jsonify({'error': str(e)}), 500


@ai_bp.route('/workflow/<session_id>/task/<task_id>', methods=['DELETE'])
def delete_task(session_id, task_id):
    """Delete task from workflow session"""
    try:
        # Load session to get site_id
        from pathlib import Path
        sessions_dir = Path("ai_features/data/sessions")
        session_file = sessions_dir / f"{session_id}.json"
        
        if not session_file.exists():
            return jsonify({'error': 'Session not found'}), 404
        
        with open(session_file, 'r') as f:
            session_data = json.load(f)
        
        site_id = session_data.get('site_id')
        engine = AgenticEngine(site_id)
        engine.load_session(session_id)
        
        # Delete task
        success = engine.delete_task(session_id, task_id)
        
        if success:
            engine.save_session(session_id)
            return jsonify({'message': 'Task deleted successfully'})
        else:
            return jsonify({'error': 'Task not found or could not be deleted'}), 404
            
    except Exception as e:
        logger.error(f"Error deleting task {task_id} from session {session_id}: {e}")
        return jsonify({'error': str(e)}), 500


@ai_bp.route('/edit/<path:site_path>/smart', methods=['POST'])
def smart_edit_site(site_path):
    """Smart AI-powered site editing using the new system"""
    try:
        full_path = os.path.join('scraped_sites', site_path)
        if not os.path.exists(full_path) or not os.path.isdir(full_path):
            return jsonify({'error': 'Site not found'}), 404
        
        data = request.get_json()
        if not data or 'user_request' not in data:
            return jsonify({'error': 'user_request is required'}), 400
        
        user_request = data['user_request']
        
        # First, check if we have memory for this site
        memory_manager = WebsiteMemory()
        memories = memory_manager.list_memories()
        
        # Find memory for this site path
        site_memory = None
        for memory in memories:
            if memory['file_path'].endswith(f"{site_path.replace('/', '_')}.json"):
                site_memory = memory
                break
        
        # If no memory exists, create it
        if not site_memory:
            memory = memory_manager.create_memory(full_path)
            site_id = memory.site_id
        else:
            site_id = site_memory['site_id']
        
        # Create workflow session
        engine = AgenticEngine(site_id)
        session = engine.create_workflow_session(user_request)
        
        # Auto-execute if requested
        auto_execute = data.get('auto_execute', False)
        if auto_execute:
            results = engine.execute_workflow_session(session.session_id, auto_execute=True)
            engine.save_session(session.session_id)
            
            return jsonify({
                'message': 'Smart editing completed',
                'session_id': session.session_id,
                'execution_results': results
            })
        else:
            # Return session for user review
            return jsonify({
                'message': 'Workflow created - review tasks before execution',
                'session_id': session.session_id,
                'tasks': [
                    {
                        'id': task.id,
                        'description': task.description,
                        'task_type': task.task_type.value,
                        'priority': task.priority.value,
                        'files_affected': task.files_affected,
                        'estimated_complexity': task.estimated_complexity
                    }
                    for task in session.tasks
                ]
            })
        
    except Exception as e:
        logger.error(f"Error in smart edit for {site_path}: {e}")
        return jsonify({'error': str(e)}), 500


@ai_bp.route('/providers/test/<provider_name>', methods=['POST'])
def test_provider(provider_name):
    """Test LLM provider connection"""
    try:
        config = get_ai_config()
        provider_config = config.get_provider_config(provider_name)
        
        if not provider_config:
            return jsonify({'error': 'Provider not configured'}), 404
        
        # Create provider and test
        from ai_features.llm_providers import LLMProviderFactory
        provider = LLMProviderFactory.create_provider(provider_name, provider_config)
        
        # Test with simple message
        test_messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Say 'Hello, I am working correctly!' if you receive this message."}
        ]
        
        response = provider.chat_completion(test_messages, max_tokens=50)
        
        return jsonify({
            'status': 'success',
            'provider': provider_name,
            'model': response.model,
            'response': response.content,
            'response_time': response.response_time
        })
        
    except Exception as e:
        logger.error(f"Error testing provider {provider_name}: {e}")
        return jsonify({'error': str(e)}), 500


# SocketIO events for real-time updates
def init_ai_socketio(socketio):
    """Initialize AI-related SocketIO events"""
    
    @socketio.on('join_workflow_session')
    def handle_join_workflow(data):
        """Join a workflow session for real-time updates"""
        session_id = data.get('session_id')
        if session_id:
            # Join room for this session
            from flask_socketio import join_room
            join_room(f"workflow_{session_id}")
            emit('joined_workflow', {'session_id': session_id})
    
    @socketio.on('leave_workflow_session')
    def handle_leave_workflow(data):
        """Leave a workflow session"""
        session_id = data.get('session_id')
        if session_id:
            from flask_socketio import leave_room
            leave_room(f"workflow_{session_id}")
            emit('left_workflow', {'session_id': session_id})


def emit_workflow_update(session_id, update_data):
    """Emit workflow updates to connected clients"""
    try:
        from flask import current_app
        with current_app.app_context():
            from flask_socketio import emit
            emit('workflow_update', update_data, room=f"workflow_{session_id}")
    except Exception as e:
        logger.error(f"Error emitting workflow update: {e}")


# Template routes
@ai_bp.route('/')
def ai_interface():
    """Main AI interface page"""
    return render_template('ai_interface.html')


@ai_bp.route('/sites')
def get_available_sites():
    """Get list of available converted sites"""
    try:
        sites = []
        scraped_dir = 'scraped_sites'
        
        if os.path.exists(scraped_dir):
            for domain in os.listdir(scraped_dir):
                domain_path = os.path.join(scraped_dir, domain)
                if os.path.isdir(domain_path):
                    for timestamp in os.listdir(domain_path):
                        timestamp_path = os.path.join(domain_path, timestamp)
                        if os.path.isdir(timestamp_path):
                            # Check if index.html exists
                            index_path = os.path.join(timestamp_path, 'index.html')
                            if os.path.exists(index_path):
                                sites.append({
                                    'domain': domain,
                                    'timestamp': timestamp,
                                    'path': f"{domain}/{timestamp}",
                                    'display_name': f"{domain} ({timestamp})"
                                })
        
        return jsonify(sites)
        
    except Exception as e:
        logger.error(f"Error loading available sites: {e}")
        return jsonify({'error': str(e)}), 500


@ai_bp.route('/todo/<session_id>')
def todo_viewer(session_id):
    """Todo viewer for specific session"""
    return render_template('todo_viewer.html', session_id=session_id)


@ai_bp.route('/memory')
def memory_browser():
    """Memory browser page"""
    return render_template('memory_browser.html')


# Error handlers
@ai_bp.errorhandler(404)
def ai_not_found(error):
    return jsonify({'error': 'AI endpoint not found'}), 404


@ai_bp.errorhandler(500)
def ai_internal_error(error):
    logger.error(f"AI Blueprint internal error: {error}")
    return jsonify({'error': 'Internal AI system error'}), 500