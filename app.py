from flask import Flask, render_template, request, jsonify, send_file, url_for, redirect, send_from_directory, abort
from flask_socketio import SocketIO, emit
import os
import shutil
import zipfile
import threading
from datetime import datetime
from urllib.parse import urlparse
from scraper import WordPressScraper
import json
import mimetypes

app = Flask(__name__)
app.config['SECRET_KEY'] = 'wordpress-scraper-secret-key'
socketio = SocketIO(app, cors_allowed_origins="*")

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
    
    # Start scraping in background thread
    thread = threading.Thread(target=scrape_website, args=(url,))
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

@socketio.on('connect')
def handle_connect():
    emit('progress_update', scraping_progress)

def scrape_website(url):
    global scraping_progress
    
    # Reset progress
    scraping_progress.update({
        'active': True,
        'current_url': url,
        'total_pages': 0,
        'completed_pages': 0,
        'current_page': '',
        'output_dir': '',
        'logs': []
    })
    
    try:
        # Create output directory
        parsed_url = urlparse(url)
        domain = parsed_url.netloc.replace('www.', '')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        scraped_dir = os.path.join('scraped_sites', domain, timestamp)
        os.makedirs(scraped_dir, exist_ok=True)
        scraping_progress['output_dir'] = scraped_dir
        
        # Initialize scraper
        scraper = WordPressScraper(url, scraped_dir, progress_callback=update_progress)
        
        # Start scraping
        scraper.scrape()
        
        scraping_progress['active'] = False
        add_log(f"Scraping abgeschlossen! {scraping_progress['completed_pages']} Seiten erfasst.")
        
    except Exception as e:
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
