from flask import Flask, render_template, request, jsonify, send_file, url_for, redirect, send_from_directory, abort
from flask_socketio import SocketIO, emit
import os
import shutil
import zipfile
import threading
import subprocess
import subprocess
from datetime import datetime
from urllib.parse import urlparse
from scraper import WordPressScraper
import json
import mimetypes
import requests
from database import get_db, Project, ScrapingSession, ScrapingLog
from screenshot_service import generate_project_screenshot_sync, generate_local_project_screenshot_sync, screenshot_service

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not available, environment should be set manually

# Import AI routes
from ai_routes import ai_bp, init_ai_socketio

app = Flask(__name__)
app.config['SECRET_KEY'] = 'wordpress-scraper-secret-key'
socketio = SocketIO(app, cors_allowed_origins="*")

# Register AI blueprint
app.register_blueprint(ai_bp)

# Initialize AI SocketIO events
init_ai_socketio(socketio)

# Global variables for progress tracking
scraping_progress = {
    'active': False,
    'current_url': '',
    'total_pages': 0,
    'completed_pages': 0,
    'current_page': '',
    'output_dir': '',
    'logs': []
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/start_scraping', methods=['POST'])
def start_scraping():
    url = request.form.get('url', '').strip()
    name = request.form.get('name', '').strip()
    description = request.form.get('description', '').strip()
    
    if not url:
        return jsonify({'error': 'URL ist erforderlich'}), 400
    
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    # Validate URL
    try:
        parsed = urlparse(url)
        if not parsed.netloc:
            return jsonify({'error': 'Ungültige URL'}), 400
    except Exception:
        return jsonify({'error': 'Ungültige URL'}), 400
    
    # Check if scraping is already in progress
    if scraping_progress['active']:
        return jsonify({'error': 'Scraping läuft bereits'}), 400
    
    # Create or get project in database
    db = get_db()
    project = db.get_project_by_url(url)
    
    if not project:
        # Create new project
        if not name:
            # Generate name from URL if not provided
            parsed = urlparse(url)
            name = parsed.netloc.replace('www.', '')
        
        project = Project(name=name, url=url, description=description)
        project_id = db.create_project(project)
        project.id = project_id
    
    # Create scraping session
    session = ScrapingSession(project_id=project.id, status='pending')
    session_id = db.create_scraping_session(session)
    session.id = session_id
    
    # Store session in global progress tracker
    scraping_progress['session_id'] = session_id
    scraping_progress['project_id'] = project.id
    
    # Start scraping in background thread
    thread = threading.Thread(target=scrape_website, args=(project, session))
    thread.daemon = True
    thread.start()
    
    return redirect(url_for('progress'))

@app.route('/progress')
def progress():
    return render_template('progress.html')

@app.route('/result')
def result():
    if not scraping_progress['output_dir'] or not os.path.exists(scraping_progress['output_dir']):
        return redirect(url_for('index'))
    
    # Get directory contents
    files = []
    output_dir = scraping_progress['output_dir']
    
    for root, dirs, filenames in os.walk(output_dir):
        level = root.replace(output_dir, '').count(os.sep)
        indent = ' ' * 2 * level
        files.append({
            'name': os.path.basename(root) + '/',
            'path': root,
            'is_dir': True,
            'indent': indent
        })
        subindent = ' ' * 2 * (level + 1)
        for filename in filenames:
            file_path = os.path.join(root, filename)
            files.append({
                'name': filename,
                'path': file_path,
                'is_dir': False,
                'size': os.path.getsize(file_path),
                'indent': subindent
            })
    
    # Calculate total size
    total_size = sum(os.path.getsize(os.path.join(root, file))
                    for root, dirs, files in os.walk(output_dir)
                    for file in files)
    
    return render_template('result.html', 
                         files=files, 
                         total_pages=scraping_progress['completed_pages'],
                         total_size=format_size(total_size),
                         output_dir=output_dir)

@app.route('/download_zip')
def download_zip():
    if not scraping_progress['output_dir'] or not os.path.exists(scraping_progress['output_dir']):
        return redirect(url_for('index'))
    
    output_dir = scraping_progress['output_dir']
    site_name = os.path.basename(os.path.dirname(output_dir))
    timestamp = os.path.basename(output_dir)
    zip_filename = f"{site_name}_{timestamp}.zip"
    zip_path = os.path.join(os.path.dirname(output_dir), zip_filename)
    
    # Create ZIP file
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(output_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, output_dir)
                zipf.write(file_path, arcname)
    
    return send_file(zip_path, as_attachment=True, download_name=zip_filename)

@app.route('/api/progress')
def get_progress():
    return jsonify(scraping_progress)

@app.route('/cancel_scraping', methods=['POST'])
def cancel_scraping():
    # This would need to be implemented with proper thread cancellation
    # For MVP, we'll just mark as inactive
    scraping_progress['active'] = False
    return jsonify({'success': True})

# Project Management API Endpoints

@app.route('/api/projects', methods=['GET'])
def get_projects():
    """Get all projects"""
    db = get_db()
    favorites_only = request.args.get('favorites_only', 'false').lower() == 'true'
    search_query = request.args.get('search', '').strip()
    
    if search_query:
        projects = db.search_projects(search_query)
    else:
        projects = db.get_all_projects(favorites_only=favorites_only)
    
    # Convert to dict for JSON serialization
    projects_data = []
    for project in projects:
        project_dict = {
            'id': project.id,
            'name': project.name,
            'url': project.url,
            'description': project.description,
            'created_at': project.created_at.isoformat() if project.created_at else None,
            'updated_at': project.updated_at.isoformat() if project.updated_at else None,
            'favorite': project.favorite,
            'thumbnail_path': project.thumbnail_path,
            'last_scraped_at': project.last_scraped_at.isoformat() if project.last_scraped_at else None,
            'total_pages': project.total_pages,
            'total_size_mb': project.total_size_mb,
            'settings': project.settings
        }
        projects_data.append(project_dict)
    
    return jsonify(projects_data)

@app.route('/api/projects/<int:project_id>', methods=['GET'])
def get_project(project_id):
    """Get specific project"""
    db = get_db()
    project = db.get_project(project_id)
    
    if not project:
        return jsonify({'error': 'Project not found'}), 404
    
    project_dict = {
        'id': project.id,
        'name': project.name,
        'url': project.url,
        'description': project.description,
        'created_at': project.created_at.isoformat() if project.created_at else None,
        'updated_at': project.updated_at.isoformat() if project.updated_at else None,
        'favorite': project.favorite,
        'thumbnail_path': project.thumbnail_path,
        'last_scraped_at': project.last_scraped_at.isoformat() if project.last_scraped_at else None,
        'total_pages': project.total_pages,
        'total_size_mb': project.total_size_mb,
        'settings': project.settings
    }
    
    return jsonify(project_dict)

@app.route('/api/projects', methods=['POST'])
def create_project():
    """Create new project"""
    data = request.get_json()
    
    if not data or 'url' not in data:
        return jsonify({'error': 'URL is required'}), 400
    
    db = get_db()
    
    # Check if project with this URL already exists
    existing = db.get_project_by_url(data['url'])
    if existing:
        return jsonify({'error': 'Project with this URL already exists'}), 409
    
    project = Project(
        name=data.get('name', ''),
        url=data['url'],
        description=data.get('description', ''),
        favorite=data.get('favorite', False)
    )
    
    if project.settings_json:
        project.settings = data.get('settings', {})
    
    project_id = db.create_project(project)
    project.id = project_id
    
    return jsonify({'id': project_id, 'message': 'Project created successfully'}), 201

@app.route('/api/projects/<int:project_id>', methods=['PUT'])
def update_project(project_id):
    """Update existing project"""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    db = get_db()
    project = db.get_project(project_id)
    
    if not project:
        return jsonify({'error': 'Project not found'}), 404
    
    # Update fields
    if 'name' in data:
        project.name = data['name']
    if 'url' in data:
        project.url = data['url']
    if 'description' in data:
        project.description = data['description']
    if 'favorite' in data:
        project.favorite = data['favorite']
    if 'settings' in data:
        project.settings = data['settings']
    
    success = db.update_project(project)
    
    if success:
        return jsonify({'message': 'Project updated successfully'})
    else:
        return jsonify({'error': 'Failed to update project'}), 500

@app.route('/api/projects/<int:project_id>', methods=['DELETE'])
def delete_project(project_id):
    """Delete project"""
    db = get_db()
    
    # Get project to check if it exists and get file paths
    project = db.get_project(project_id)
    if not project:
        return jsonify({'error': 'Project not found'}), 404
    
    # Delete project screenshots first
    try:
        screenshot_service.cleanup_project_screenshots(project_id)
        print(f"Cleaned up screenshots for project {project_id}")
    except Exception as e:
        print(f"Error deleting project screenshots: {e}")
    
    # Delete project files if they exist
    try:
        parsed_url = urlparse(project.url)
        domain = parsed_url.netloc.replace('www.', '')
        domain_dir = os.path.join('scraped_sites', domain)
        
        if os.path.exists(domain_dir):
            shutil.rmtree(domain_dir)
            print(f"Deleted project files: {domain_dir}")
    except Exception as e:
        print(f"Error deleting project files: {e}")
    
    # Delete from database
    success = db.delete_project(project_id)
    
    if success:
        return jsonify({'message': 'Project deleted successfully'})
    else:
        return jsonify({'error': 'Failed to delete project'}), 500

@app.route('/api/projects/<int:project_id>/sessions', methods=['GET'])
def get_project_sessions(project_id):
    """Get scraping sessions for project"""
    db = get_db()
    sessions = db.get_project_sessions(project_id)
    
    sessions_data = []
    for session in sessions:
        session_dict = {
            'id': session.id,
            'project_id': session.project_id,
            'timestamp': session.timestamp.isoformat() if session.timestamp else None,
            'status': session.status,
            'pages_count': session.pages_count,
            'file_size_mb': session.file_size_mb,
            'output_path': session.output_path,
            'duration_seconds': session.duration_seconds
        }
        sessions_data.append(session_dict)
    
    return jsonify(sessions_data)

@app.route('/api/projects/<int:project_id>/screenshot', methods=['POST'])
def regenerate_screenshot(project_id):
    """Regenerate screenshot for project"""
    db = get_db()
    project = db.get_project(project_id)
    
    if not project:
        return jsonify({'error': 'Project not found'}), 404
    
    try:
        # Clean up old screenshots first
        screenshot_service.cleanup_project_screenshots(project_id)
        
        # Try to find the latest scraped version first
        parsed_url = urlparse(project.url)
        domain = parsed_url.netloc.replace('www.', '')
        domain_dir = os.path.join('scraped_sites', domain)
        
        thumbnail_path = None
        
        if os.path.exists(domain_dir):
            # Find the most recent scrape
            timestamps = [d for d in os.listdir(domain_dir) 
                         if os.path.isdir(os.path.join(domain_dir, d))]
            if timestamps:
                latest_timestamp = sorted(timestamps, reverse=True)[0]
                index_path = os.path.join(domain_dir, latest_timestamp, 'index.html')
                
                if os.path.exists(index_path):
                    thumbnail_path = generate_local_project_screenshot_sync(index_path, project_id)
        
        # Fallback to live URL if no local version found
        if not thumbnail_path:
            thumbnail_path = generate_project_screenshot_sync(project.url, project_id)
        
        # Update project with new thumbnail
        project.thumbnail_path = thumbnail_path
        db.update_project(project)
        
        return jsonify({
            'message': 'Screenshot regenerated successfully',
            'thumbnail_path': thumbnail_path
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to regenerate screenshot: {str(e)}'}), 500

@app.route('/api/edit/<path:site_path>', methods=['POST'])
def api_edit_site(site_path):
    """API endpoint to handle AI-powered edits"""
    full_path = os.path.join('scraped_sites', site_path)
    if not os.path.exists(full_path) or not os.path.isdir(full_path):
        return jsonify({'error': 'Site not found'}), 404

    data = request.get_json()
    prompt = data.get('prompt')

    if not prompt:
        return jsonify({'error': 'Prompt is required'}), 400

    # 1. Initialize git repo if not exists
    git_path = os.path.join(full_path, '.git')
    if not os.path.exists(git_path):
        try:
            # Run 'git init'
            subprocess.run(['git', 'init'], cwd=full_path, check=True)
            # Run 'git add .'
            subprocess.run(['git', 'add', '.'], cwd=full_path, check=True)
            # Run 'git commit'
            subprocess.run(['git', 'commit', '-m', 'Initial commit'], cwd=full_path, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            return jsonify({'error': f'Failed to initialize git repository: {e}'}), 500

    # 2. Read files (limit content to avoid token limits)
    files_content = {}
    MAX_FILE_SIZE = 5000   # Limit each file to ~5k characters
    MAX_TOTAL_SIZE = 20000  # Limit total content to ~20k characters
    total_size = 0
    
    # Prioritize index.html and main CSS files
    priority_files = []
    other_files = []
    
    for root, dirs, files in os.walk(full_path):
        for file in files:
            if file.endswith(('.html', '.css')):
                file_path = os.path.join(root, file)
                if file == 'index.html' or 'main' in file.lower() or 'style' in file.lower():
                    priority_files.append(file_path)
                else:
                    other_files.append(file_path)
    
    # Process priority files first
    for file_path in priority_files + other_files:
        if total_size >= MAX_TOTAL_SIZE:
            break
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                # Truncate if too large
                if len(content) > MAX_FILE_SIZE:
                    content = content[:MAX_FILE_SIZE] + "\n... [content truncated]"
                
                files_content[file_path] = content
                total_size += len(content)
        except UnicodeDecodeError:
            # Skip binary files
            continue

    # 3. Call DeepSeek LLM
    try:
        api_key = os.environ.get("DEEPSEEK_API_KEY", "YOUR_DEEPSEEK_API_KEY")
        if api_key == "YOUR_DEEPSEEK_API_KEY":
            # Return a simulation if the API key is not set
            index_html_path = os.path.join(full_path, 'index.html')
            if index_html_path in files_content:
                files_content[index_html_path] += f'<!-- AI-generated change based on prompt: {prompt} -->'
        else:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            }

            # Construct the prompt for the LLM
            llm_prompt = f"The user wants to modify a static website. Their instruction is: '{prompt}'.\n\n"
            llm_prompt += "Here are the contents of the relevant files:\n\n"
            for file_path, content in files_content.items():
                relative_path = os.path.relpath(file_path, full_path)
                llm_prompt += f"--- {relative_path} ---\n{content}\n\n"

            llm_prompt += "IMPORTANT: You must respond with ONLY a valid JSON object. No other text before or after.\n"
            llm_prompt += "The JSON should have file paths as keys and the new file contents as values.\n"
            llm_prompt += "Only include files that need to be changed.\n"
            llm_prompt += "Example format: {\"index.html\": \"<html>new content</html>\", \"style.css\": \"body { background: blue; }\"}\n"
            llm_prompt += "If no changes are needed, return an empty object: {}"

            data = {
                "model": "deepseek-chat",
                "messages": [
                    {"role": "system", "content": "You are a helpful AI assistant that modifies website code."},
                    {"role": "user", "content": llm_prompt},
                ],
                "temperature": 0.7,
                "max_tokens": 8192,
            }

            response = requests.post("https://api.deepseek.com/v1/chat/completions", headers=headers, json=data)
            
            # Add debug logging
            if response.status_code != 200:
                print(f"DeepSeek API Error: {response.status_code}")
                print(f"Response: {response.text}")
                return jsonify({'error': f'DeepSeek API Error: {response.status_code} - {response.text}'}), 500
                
            response.raise_for_status()

            llm_response = response.json()
            if 'choices' in llm_response and llm_response['choices']:
                content_to_update = llm_response['choices'][0]['message']['content'].strip()
                
                # Try to extract JSON if it's wrapped in code blocks
                if content_to_update.startswith('```'):
                    lines = content_to_update.split('\n')
                    json_lines = []
                    in_json = False
                    for line in lines:
                        if line.startswith('```') and not in_json:
                            in_json = True
                            continue
                        elif line.startswith('```') and in_json:
                            break
                        elif in_json:
                            json_lines.append(line)
                    content_to_update = '\n'.join(json_lines)
                
                try:
                    updated_files = json.loads(content_to_update)
                    if not isinstance(updated_files, dict):
                        return jsonify({'error': 'LLM response is not a JSON object.'}), 500
                        
                    for file_path, new_content in updated_files.items():
                        full_file_path = os.path.join(full_path, file_path)
                        if os.path.exists(full_file_path):
                             files_content[full_file_path] = new_content
                except json.JSONDecodeError as e:
                    print(f"JSON decode error: {e}")
                    print(f"LLM response length: {len(content_to_update)}")
                    print(f"LLM response: {content_to_update}")
                    
                    # Try to fix common JSON issues
                    fixed_content = content_to_update
                    
                    # If response appears truncated, try to close the JSON
                    if not fixed_content.rstrip().endswith('}'):
                        # Count open braces vs close braces
                        open_braces = fixed_content.count('{')
                        close_braces = fixed_content.count('}')
                        
                        # If we're missing closing braces, add them
                        if open_braces > close_braces:
                            # Find the last complete string and truncate there
                            last_quote_pos = fixed_content.rfind('",')
                            if last_quote_pos > 0:
                                fixed_content = fixed_content[:last_quote_pos + 1]
                            
                            # Add missing closing braces
                            for _ in range(open_braces - close_braces):
                                fixed_content += '}'
                    
                    try:
                        updated_files = json.loads(fixed_content)
                        print("Successfully fixed JSON!")
                        if not isinstance(updated_files, dict):
                            return jsonify({'error': 'LLM response is not a JSON object.'}), 500
                            
                        for file_path, new_content in updated_files.items():
                            full_file_path = os.path.join(full_path, file_path)
                            if os.path.exists(full_file_path):
                                 files_content[full_file_path] = new_content
                    except json.JSONDecodeError:
                        return jsonify({'error': f'Failed to decode LLM response as JSON: {str(e)}. Response may be truncated.'}), 500

    except requests.exceptions.RequestException as e:
        return jsonify({'error': f'Failed to call LLM: {e}'}), 500
    except Exception as e:
        return jsonify({'error': f'An unexpected error occurred: {e}'}), 500


    # 4. Apply changes
    for file_path, content in files_content.items():
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

    # 5. Commit changes
    try:
        subprocess.run(['git', 'add', '.'], cwd=full_path, check=True)
        subprocess.run(['git', 'commit', '-m', prompt], cwd=full_path, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        return jsonify({'error': f'Failed to commit changes: {e}'}), 500


    return jsonify({'message': 'Changes generated successfully', 'prompt': prompt})

@app.route('/api/history/<path:site_path>')
def api_history(site_path):
    """API endpoint to get the git commit history for a site"""
    full_path = os.path.join('scraped_sites', site_path)
    if not os.path.exists(full_path) or not os.path.isdir(full_path):
        return jsonify({'error': 'Site not found'}), 404

    git_path = os.path.join(full_path, '.git')
    if not os.path.exists(git_path):
        return jsonify({'history': []})

    try:
        # Get git log with a custom format
        log_format = "%H|%an|%ar|%s"
        result = subprocess.run(
            ['git', 'log', f'--pretty=format:{log_format}'],
            cwd=full_path,
            check=True,
            capture_output=True,
            text=True
        )

        log_output = result.stdout.strip()

        if not log_output:
            return jsonify([])

        commits = []
        for line in log_output.split('\n'):
            parts = line.split('|')
            if len(parts) == 4:
                commit = {
                    'hash': parts[0],
                    'author': parts[1],
                    'date': parts[2],
                    'message': parts[3]
                }
                commits.append(commit)

        return jsonify(commits)

    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        return jsonify({'error': f'Failed to get git history: {e}'}), 500



@app.route('/preview')
def preview_index():
    """Show available scraped sites for preview"""
    if not os.path.exists('scraped_sites'):
        return render_template('preview_index.html', sites=[])
    
    sites = []
    for domain in os.listdir('scraped_sites'):
        domain_path = os.path.join('scraped_sites', domain)
        if os.path.isdir(domain_path):
            timestamps = []
            for timestamp in os.listdir(domain_path):
                timestamp_path = os.path.join(domain_path, timestamp)
                if os.path.isdir(timestamp_path):
                    # Check if index.html exists
                    index_path = os.path.join(timestamp_path, 'index.html')
                    if os.path.exists(index_path):
                        # Get creation time and size
                        stat = os.stat(timestamp_path)
                        size = sum(os.path.getsize(os.path.join(root, file))
                                 for root, dirs, files in os.walk(timestamp_path)
                                 for file in files)
                        timestamps.append({
                            'timestamp': timestamp,
                            'path': f"{domain}/{timestamp}",
                            'created': datetime.fromtimestamp(stat.st_ctime),
                            'size': format_size(size)
                        })
            
            if timestamps:
                timestamps.sort(key=lambda x: x['created'], reverse=True)
                sites.append({
                    'domain': domain,
                    'timestamps': timestamps
                })
    
    return render_template('preview_index.html', sites=sites)

@app.route('/preview/<path:site_path>')
def preview_site(site_path):
    """Serve scraped site files for preview"""
    # Validate the path to prevent directory traversal
    if '..' in site_path or site_path.startswith('/'):
        abort(403)
    
    # Check if it's a request for the root of a site (redirect to index.html)
    full_path = os.path.join('scraped_sites', site_path)
    
    if os.path.isdir(full_path):
        # Check for index.html in the directory
        index_path = os.path.join(full_path, 'index.html')
        if os.path.exists(index_path):
            return send_file(index_path)
        else:
            # Return directory listing if no index.html
            return preview_directory_listing(site_path)
    
    if os.path.exists(full_path):
        # Determine mimetype
        mimetype = mimetypes.guess_type(full_path)[0]
        return send_file(full_path, mimetype=mimetype)
    
    abort(404)

@app.route('/preview/<path:site_path>/')
def preview_site_with_slash(site_path):
    """Handle requests with trailing slash"""
    return preview_site(site_path)

def preview_directory_listing(site_path):
    """Generate a simple directory listing for preview"""
    full_path = os.path.join('scraped_sites', site_path)
    if not os.path.exists(full_path):
        abort(404)
    
    items = []
    for item in os.listdir(full_path):
        item_path = os.path.join(full_path, item)
        is_dir = os.path.isdir(item_path)
        size = 0 if is_dir else os.path.getsize(item_path)
        
        items.append({
            'name': item,
            'is_dir': is_dir,
            'size': format_size(size) if not is_dir else '',
            'url': f"/preview/{site_path}/{item}" if not is_dir else f"/preview/{site_path}/{item}/"
        })
    
    # Sort: directories first, then files
    items.sort(key=lambda x: (not x['is_dir'], x['name'].lower()))
    
    return render_template('preview_directory.html', 
                         path=site_path, 
                         items=items,
                         parent_url=f"/preview/{'/'.join(site_path.split('/')[:-1])}" if '/' in site_path else '/preview')

@app.route('/edit/<path:site_path>')
def edit_site(site_path):
    """Show the AI editing interface for a scraped site"""
    full_path = os.path.join('scraped_sites', site_path)
    if not os.path.exists(full_path) or not os.path.isdir(full_path):
        abort(404)

    return render_template('edit.html', site_path=site_path)



@app.route('/api/files/<path:site_path>')
def api_files(site_path):
    """API endpoint to get the file list for a site"""
    full_path = os.path.join('scraped_sites', site_path)
    if not os.path.exists(full_path) or not os.path.isdir(full_path):
        return jsonify({'error': 'Site not found'}), 404

    files = []
    for root, dirs, filenames in os.walk(full_path):
        # Exclude the .git directory
        if '.git' in dirs:
            dirs.remove('.git')

        level = root.replace(full_path, '').count(os.sep)
        indent = ' ' * 2 * level

        # Add directory
        files.append({
            'name': os.path.basename(root) + '/',
            'path': root.replace(full_path, ''),
            'is_dir': True,
            'indent': indent
        })

        subindent = ' ' * 2 * (level + 1)
        for filename in filenames:
            file_path = os.path.join(root, filename)
            files.append({
                'name': filename,
                'path': file_path.replace(full_path, ''),
                'is_dir': False,
                'size': os.path.getsize(file_path),
                'indent': subindent
            })

    return jsonify({'files': files})

@socketio.on('connect')
def handle_connect():
    emit('progress_update', scraping_progress)

def scrape_website(project: Project, session: ScrapingSession):
    global scraping_progress
    
    db = get_db()
    start_time = datetime.now()
    
    # Reset progress
    scraping_progress.update({
        'active': True,
        'current_url': project.url,
        'total_pages': 0,
        'completed_pages': 0,
        'current_page': '',
        'output_dir': '',
        'logs': []
    })
    
    try:
        # Update session status
        session.status = 'running'
        db.update_scraping_session(session)
    
        # Create output directory
        parsed_url = urlparse(project.url)
        domain = parsed_url.netloc.replace('www.', '')
        timestamp = start_time.strftime('%Y%m%d_%H%M%S')
        
        scraped_dir = os.path.join('scraped_sites', domain, timestamp)
        os.makedirs(scraped_dir, exist_ok=True)
        scraping_progress['output_dir'] = scraped_dir
        
        # Update session with output path
        session.output_path = scraped_dir
        db.update_scraping_session(session)
        
        # Initialize scraper
        scraper = WordPressScraper(project.url, scraped_dir, progress_callback=update_progress)
        
        # Start scraping
        scraper.scrape()
        
        # Calculate final stats
        end_time = datetime.now()
        duration = int((end_time - start_time).total_seconds())
        
        # Calculate directory size
        total_size = 0
        for root, dirs, files in os.walk(scraped_dir):
            for file in files:
                total_size += os.path.getsize(os.path.join(root, file))
        
        # Update session completion
        session.status = 'completed'
        session.pages_count = scraping_progress['completed_pages']
        session.file_size_mb = total_size / (1024 * 1024)
        session.duration_seconds = duration
        db.update_scraping_session(session)
        
        # Generate screenshot/thumbnail
        add_log("Erstelle Screenshot...")
        try:
            # Try to capture from the scraped index.html first
            index_path = os.path.join(scraped_dir, 'index.html')
            if os.path.exists(index_path):
                thumbnail_path = generate_local_project_screenshot_sync(index_path, project.id)
            else:
                # Fallback to original URL
                thumbnail_path = generate_project_screenshot_sync(project.url, project.id)
            
            project.thumbnail_path = thumbnail_path
            add_log("Screenshot erstellt")
        except Exception as e:
            add_log(f"Screenshot-Erstellung fehlgeschlagen: {str(e)}")
            print(f"Screenshot error: {e}")
        
        # Update project stats
        project.last_scraped_at = end_time
        project.total_pages = scraping_progress['completed_pages']
        project.total_size_mb = session.file_size_mb
        db.update_project(project)
        
        scraping_progress['active'] = False
        add_log(f"Scraping abgeschlossen! {scraping_progress['completed_pages']} Seiten erfasst.")
        
    except Exception as e:
        # Update session as failed
        session.status = 'failed'
        session.duration_seconds = int((datetime.now() - start_time).total_seconds())
        db.update_scraping_session(session)
        
        scraping_progress['active'] = False
        add_log(f"Fehler beim Scraping: {str(e)}")
        print(f"Scraping error: {e}")

def update_progress(data):
    global scraping_progress
    
    if 'total_pages' in data:
        scraping_progress['total_pages'] = data['total_pages']
    if 'completed_pages' in data:
        scraping_progress['completed_pages'] = data['completed_pages']
    if 'current_page' in data:
        scraping_progress['current_page'] = data['current_page']
    if 'log' in data:
        add_log(data['log'])
    
    # Emit to all connected clients
    socketio.emit('progress_update', scraping_progress)

def add_log(message):
    timestamp = datetime.now().strftime('%H:%M:%S')
    log_entry = f"[{timestamp}] {message}"
    scraping_progress['logs'].append(log_entry)
    
    # Keep only last 100 log entries
    if len(scraping_progress['logs']) > 100:
        scraping_progress['logs'] = scraping_progress['logs'][-100:]

def format_size(size_bytes):
    if size_bytes == 0:
        return "0B"
    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    while size_bytes >= 1024.0 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    return f"{size_bytes:.1f} {size_names[i]}"

if __name__ == '__main__':
    # Create scraped_sites directory
    os.makedirs('scraped_sites', exist_ok=True)
    
    socketio.run(app, debug=True, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)
