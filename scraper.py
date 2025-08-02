from playwright.sync_api import sync_playwright
import os
import re
import time
import requests
from urllib.parse import urljoin, urlparse, urlunparse
from bs4 import BeautifulSoup
import mimetypes
from pathlib import Path

class WordPressScraper:
    def __init__(self, base_url, output_dir, progress_callback=None):
        self.base_url = base_url.rstrip('/')
        self.output_dir = output_dir
        self.progress_callback = progress_callback
        self.visited_urls = set()
        self.discovered_urls = set()
        self.assets = set()
        self.scraped_pages = set()  # Track URLs that are actual pages to avoid asset conflicts
        self.domain = urlparse(base_url).netloc
        
        # Create necessary directories
        os.makedirs(output_dir, exist_ok=True)
        
    def log(self, message):
        if self.progress_callback:
            self.progress_callback({'log': message})
        print(message)
    
    def update_progress(self, data):
        if self.progress_callback:
            self.progress_callback(data)
    
    def scrape(self):
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            
            try:
                self.log("Starte WordPress Scraping...")
                
                # Discover URLs from sitemap first
                self.discover_sitemap_urls()
                
                # Add base URL to discovered URLs
                self.discovered_urls.add(self.base_url)
                
                # Start with homepage and discover more URLs
                self.discover_urls_from_page(context, self.base_url)
                
                total_urls = len(self.discovered_urls)
                self.update_progress({'total_pages': total_urls})
                self.log(f"Gefunden: {total_urls} URLs zum Scraping")
                
                # Scrape all discovered URLs
                for i, url in enumerate(self.discovered_urls):
                    if url not in self.visited_urls:
                        self.log(f"Scraping: {url}")
                        self.update_progress({
                            'current_page': url,
                            'completed_pages': i
                        })
                        
                        self.scrape_page(context, url)
                        self.visited_urls.add(url)
                        time.sleep(0.5)  # Be respectful
                
                # Download assets
                self.log("Lade Assets herunter...")
                self.download_assets()
                
                self.update_progress({'completed_pages': len(self.visited_urls)})
                self.log(f"Scraping abgeschlossen: {len(self.visited_urls)} Seiten gespeichert")
                
            except Exception as e:
                self.log(f"Fehler beim Scraping: {str(e)}")
                raise
            finally:
                browser.close()
    
    def discover_sitemap_urls(self):
        sitemap_urls = [
            f"{self.base_url}/sitemap.xml",
            f"{self.base_url}/wp-sitemap.xml",
            f"{self.base_url}/sitemap_index.xml"
        ]
        
        for sitemap_url in sitemap_urls:
            try:
                response = requests.get(sitemap_url, timeout=10)
                if response.status_code == 200:
                    self.log(f"Sitemap gefunden: {sitemap_url}")
                    self.parse_sitemap(response.content)
                    break
            except:
                continue
    
    def parse_sitemap(self, sitemap_content):
        try:
            soup = BeautifulSoup(sitemap_content, 'xml')
            
            # Handle sitemap index
            sitemaps = soup.find_all('sitemap')
            for sitemap in sitemaps:
                loc = sitemap.find('loc')
                if loc:
                    try:
                        response = requests.get(loc.text, timeout=10)
                        if response.status_code == 200:
                            self.parse_sitemap(response.content)
                    except:
                        continue
            
            # Handle URL entries
            urls = soup.find_all('url')
            for url in urls:
                loc = url.find('loc')
                if loc and self.is_same_domain(loc.text):
                    normalized_url = self.normalize_url(loc.text)
                    self.discovered_urls.add(normalized_url)
                    
        except Exception as e:
            self.log(f"Fehler beim Parsen der Sitemap: {e}")
    
    def normalize_url(self, url):
        """Normalize URL to avoid conflicts between /path and /path/"""
        url = url.rstrip('/')
        if url.endswith('.html') or url.endswith('.htm'):
            return url
        # For other URLs, we'll treat them consistently
        return url
    
    def discover_urls_from_page(self, context, url):
        try:
            page = context.new_page()
            page.set_default_timeout(30000)
            page.goto(url, wait_until='networkidle')
            
            # Extract all internal links
            links = page.evaluate('''() => {
                const links = Array.from(document.querySelectorAll('a[href]'));
                return links.map(link => link.href).filter(href => href);
            }''')
            
            for link in links:
                normalized_link = self.normalize_url(link)
                if self.is_same_domain(normalized_link) and normalized_link not in self.discovered_urls:
                    self.discovered_urls.add(normalized_link)
            
            page.close()
            
        except Exception as e:
            self.log(f"Fehler beim Entdecken von URLs auf {url}: {e}")
    
    def scrape_page(self, context, url):
        try:
            page = context.new_page()
            page.set_default_timeout(30000)
            page.goto(url, wait_until='networkidle')
            
            # Get page content
            content = page.content()
            
            # Mark this URL as a scraped page to avoid asset conflicts
            self.mark_as_page(url)
            
            # Process HTML and extract assets
            soup = BeautifulSoup(content, 'html.parser')
            self.process_html_assets(soup, url)
            
            # Save processed HTML
            self.save_html_file(url, str(soup))
            
            page.close()
            
        except Exception as e:
            self.log(f"Fehler beim Scraping von {url}: {e}")
    
    def mark_as_page(self, url):
        """Mark a URL as a scraped page to avoid treating it as an asset"""
        if not hasattr(self, 'scraped_pages'):
            self.scraped_pages = set()
        self.scraped_pages.add(url)
    
    def process_html_assets(self, soup, page_url):
        # Remove cookie banners first
        self.remove_cookie_banners(soup)
        
        # Process images
        for img in soup.find_all('img', src=True):
            src = img['src']
            absolute_url = urljoin(page_url, src)
            if self.is_same_domain(absolute_url) and self.is_valid_asset(absolute_url):
                self.assets.add(absolute_url)
                img['src'] = self.convert_to_relative_path(absolute_url, page_url)
        
        # Process all link elements (CSS, favicon, preload, etc.)
        for link in soup.find_all('link', href=True):
            href = link['href']
            absolute_url = urljoin(page_url, href)
            if self.is_same_domain(absolute_url) and self.is_valid_asset(absolute_url):
                self.assets.add(absolute_url)
                link['href'] = self.convert_to_relative_path(absolute_url, page_url)
        
        # Process JavaScript
        for script in soup.find_all('script', src=True):
            src = script['src']
            absolute_url = urljoin(page_url, src)
            if self.is_same_domain(absolute_url) and self.is_valid_asset(absolute_url):
                self.assets.add(absolute_url)
                script['src'] = self.convert_to_relative_path(absolute_url, page_url)
        
        # Process internal links
        for a in soup.find_all('a', href=True):
            href = a['href']
            if not href.startswith(('#', 'mailto:', 'tel:', 'javascript:')):
                absolute_url = urljoin(page_url, href)
                if self.is_same_domain(absolute_url):
                    # Convert to relative path
                    relative_path = self.convert_to_relative_path(absolute_url, page_url)
                    a['href'] = relative_path
        
        # Process other elements with src attributes (video, audio, iframe, etc.)
        for element in soup.find_all(['video', 'audio', 'source', 'track'], src=True):
            src = element['src']
            absolute_url = urljoin(page_url, src)
            if self.is_same_domain(absolute_url) and self.is_valid_asset(absolute_url):
                self.assets.add(absolute_url)
                element['src'] = self.convert_to_relative_path(absolute_url, page_url)
        
        # Process elements with poster attributes (video)
        for element in soup.find_all(['video'], poster=True):
            poster = element['poster']
            absolute_url = urljoin(page_url, poster)
            if self.is_same_domain(absolute_url) and self.is_valid_asset(absolute_url):
                self.assets.add(absolute_url)
                element['poster'] = self.convert_to_relative_path(absolute_url, page_url)
        
        # Disable forms
        for form in soup.find_all('form'):
            form['action'] = ''
            form['method'] = 'get'
            for input_tag in form.find_all('input', type='submit'):
                input_tag['type'] = 'button'
    
    def remove_cookie_banners(self, soup):
        """Remove common cookie banner elements from the HTML"""
        removed_count = 0
        
        # Common cookie banner selectors (ID and class patterns)
        cookie_selectors = [
            # Common IDs
            '#cookie-banner', '#cookie-consent', '#cookie-notice', '#cookie-bar',
            '#cookiebar', '#cookie-popup', '#cookie-overlay', '#cookie-policy',
            '#gdpr-banner', '#gdpr-consent', '#privacy-banner', '#privacy-notice',
            '#cc-banner', '#cookieConsent', '#cookieBar', '#CookieConsent',
            
            # Common classes
            '.cookie-banner', '.cookie-consent', '.cookie-notice', '.cookie-bar',
            '.cookiebar', '.cookie-popup', '.cookie-overlay', '.cookie-policy',
            '.gdpr-banner', '.gdpr-consent', '.privacy-banner', '.privacy-notice',
            '.cookie-warning', '.cookie-alert', '.cookie-info', '.cookie-dialog',
            '.cc-banner', '.cc-window', '.cc-compliance', '.cookieConsent',
            '.cookie-consent-banner', '.cookie-notification', '.cookies-notice',
            
            # Popular cookie plugins
            '.cookie-law-info-bar', '.cli-bar-container', '.moove_gdpr_cookie_info_bar',
            '.gdpr-cookie-consent-banner', '.wp-gdpr-cookie-notice', '.catapult-cookie-bar',
            '.borlabs-cookie-banner', '.real-cookie-banner', '.cookiebot-banner',
            '.iubenda-cookie-banner', '.complianz-cookie-banner', '.cmplz-cookiebanner',
            '.uk-cookie-consent', '.eu-cookie-law', '.cookie-choices-info',
            
            # Generic patterns
            '[class*="cookie"]', '[class*="gdpr"]', '[class*="privacy"]',
            '[id*="cookie"]', '[id*="gdpr"]', '[id*="privacy"]'
        ]
        
        # Remove elements by common selectors
        for selector in cookie_selectors:
            try:
                elements = soup.select(selector)
                for element in elements:
                    if self.is_likely_cookie_banner(element):
                        element.decompose()
                        removed_count += 1
            except Exception:
                continue
        
        # Additional text-based detection for elements that might not have obvious classes
        all_elements = soup.find_all(['div', 'section', 'aside', 'header', 'footer', 'nav'])
        for element in all_elements:
            if self.is_likely_cookie_banner_by_text(element):
                element.decompose()
                removed_count += 1
        
        if removed_count > 0:
            self.log(f"Cookie-Banner entfernt: {removed_count} Elemente")
    
    def is_likely_cookie_banner(self, element):
        """Check if an element is likely a cookie banner based on attributes and content"""
        # Check attributes
        attrs_text = ' '.join([
            element.get('id', '').lower(),
            element.get('class', '') if isinstance(element.get('class'), str) else ' '.join(element.get('class', [])),
            element.get('role', '').lower(),
            element.get('aria-label', '').lower()
        ])
        
        cookie_keywords = [
            'cookie', 'gdpr', 'privacy', 'consent', 'tracking', 'analytics',
            'datenschutz', 'einverstanden', 'zustimm', 'akzeptier'
        ]
        
        return any(keyword in attrs_text for keyword in cookie_keywords)
    
    def is_likely_cookie_banner_by_text(self, element):
        """Check if an element is likely a cookie banner based on text content"""
        if not element.get_text(strip=True):
            return False
        
        text = element.get_text().lower()
        
        # Must contain cookie-related terms
        cookie_terms = ['cookie', 'gdpr', 'datenschutz', 'privacy', 'consent']
        has_cookie_term = any(term in text for term in cookie_terms)
        
        if not has_cookie_term:
            return False
        
        # And contain action terms
        action_terms = [
            'akzeptieren', 'zustimmen', 'einverstanden', 'ablehnen', 'mehr erfahren',
            'accept', 'agree', 'consent', 'decline', 'learn more', 'settings',
            'konfigurieren', 'anpassen', 'verwalten', 'manage', 'configure'
        ]
        has_action = any(term in text for term in action_terms)
        
        # Check if it's positioned like a banner (common attributes)
        style = element.get('style', '').lower()
        class_text = ' '.join(element.get('class', [])) if element.get('class') else ''
        id_text = element.get('id', '').lower()
        
        is_positioned = any(pos in style for pos in ['fixed', 'sticky', 'absolute']) or \
                       any(pos in class_text.lower() for pos in ['top', 'bottom', 'overlay', 'modal']) or \
                       any(pos in id_text for pos in ['top', 'bottom', 'overlay', 'modal'])
        
        # Short text with both cookie terms and actions is likely a banner
        return has_cookie_term and has_action and (is_positioned or len(text) < 1000)
    
    def convert_to_relative_path(self, target_url, current_page_url):
        """Convert absolute URL to relative path from current page location"""
        target_parsed = urlparse(target_url)
        current_parsed = urlparse(current_page_url)
        
        target_path = target_parsed.path
        current_path = current_parsed.path
        
        # Determine the directory depth of the current page
        if not current_path or current_path == '/':
            # Root page (index.html)
            current_dir = ''
            depth = 0
        elif current_path.endswith('/'):
            # Directory with trailing slash
            current_dir = current_path.strip('/')
            depth = len(current_dir.split('/')) if current_dir else 0
        else:
            # Page without trailing slash - treat as directory
            current_dir = current_path.strip('/')
            depth = len(current_dir.split('/')) if current_dir else 0
        
        # Build relative prefix based on depth
        relative_prefix = '../' * depth if depth > 0 else './'
        
        # Handle target path
        if not target_path or target_path == '/':
            return relative_prefix + 'index.html'
        
        if target_path.endswith('/'):
            return relative_prefix + target_path.strip('/') + '/index.html'
        
        # Check if it's an asset (has file extension)
        if any(target_path.lower().endswith(ext) for ext in [
            '.jpg', '.jpeg', '.png', '.gif', '.svg', '.ico', '.webp',  # Images
            '.css', '.js',  # Stylesheets and scripts
            '.pdf', '.zip', '.doc', '.docx',  # Documents
            '.woff', '.woff2', '.ttf', '.eot',  # Fonts
            '.mp4', '.avi', '.mov', '.mp3', '.wav',  # Media
            '.xml', '.json', '.txt'  # Data files
        ]):
            return relative_prefix + target_path.strip('/')
        
        # Regular page - treat as directory with index.html
        if target_path.endswith('.html') or target_path.endswith('.htm'):
            return relative_prefix + target_path.strip('/')
        else:
            return relative_prefix + target_path.strip('/') + '/index.html'
    
    def save_html_file(self, url, content):
        parsed = urlparse(url)
        path = parsed.path
        
        if not path or path == '/':
            file_path = os.path.join(self.output_dir, 'index.html')
        elif path.endswith('/'):
            dir_path = os.path.join(self.output_dir, path.strip('/'))
            os.makedirs(dir_path, exist_ok=True)
            file_path = os.path.join(dir_path, 'index.html')
        else:
            # Check if it's a known file extension
            if any(path.lower().endswith(ext) for ext in ['.html', '.htm', '.php', '.asp', '.aspx']):
                dir_path = os.path.dirname(os.path.join(self.output_dir, path.strip('/')))
                if dir_path and dir_path != self.output_dir:
                    os.makedirs(dir_path, exist_ok=True)
                file_path = os.path.join(self.output_dir, path.strip('/'))
                # Ensure it ends with .html
                if not file_path.endswith('.html'):
                    file_path += '.html'
            else:
                # Treat as a page that needs a directory structure
                dir_path = os.path.join(self.output_dir, path.strip('/'))
                os.makedirs(dir_path, exist_ok=True)
                file_path = os.path.join(dir_path, 'index.html')
        
        # Ensure parent directory exists
        parent_dir = os.path.dirname(file_path)
        if parent_dir and parent_dir != self.output_dir:
            os.makedirs(parent_dir, exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    def download_assets(self):
        # Convert to list to avoid "set changed size during iteration" error
        assets_to_download = list(self.assets)
        for asset_url in assets_to_download:
            try:
                self.download_asset(asset_url)
            except Exception as e:
                self.log(f"Fehler beim Download von {asset_url}: {e}")
    
    def download_asset(self, url):
        try:
            response = requests.get(url, timeout=10, stream=True)
            response.raise_for_status()
            
            parsed = urlparse(url)
            asset_path = parsed.path.strip('/')
            
            if not asset_path:
                return
            
            file_path = os.path.join(self.output_dir, asset_path)
            dir_path = os.path.dirname(file_path)
            
            # Check if the target path already exists as a directory
            if os.path.isdir(file_path):
                # This happens when a URL exists both as a page and referenced as an asset
                base_name = os.path.basename(asset_path)
                if '.' in base_name:
                    name, ext = os.path.splitext(base_name)
                    new_name = f"{name}_asset{ext}"
                else:
                    new_name = f"{base_name}_asset"
                file_path = os.path.join(dir_path, new_name)
                self.log(f"⚠️  Pfad-Konflikt: '{asset_path}' existiert als Seite und Asset - Asset gespeichert als '{new_name}'")
            
            # Ensure parent directory exists
            if dir_path:
                os.makedirs(dir_path, exist_ok=True)
            
            # Check again if something was created in the meantime
            if os.path.isdir(file_path):
                self.log(f"Kann Asset nicht speichern, Pfad ist Verzeichnis: {asset_path}")
                return
            
            # Download and save the file
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            # Process CSS files to fix internal references
            if file_path.lower().endswith('.css'):
                self.process_css_file(file_path, url)
                    
        except Exception as e:
            self.log(f"Download fehlgeschlagen für {url}: {e}")
    
    def process_css_file(self, file_path, css_url):
        """Process CSS files to fix internal references"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Find and replace url() references
            import re
            url_pattern = r'url\(["\']?([^"\')\s]+)["\']?\)'
            new_assets = set()
            
            def replace_url(match):
                url = match.group(1)
                if not url.startswith(('http://', 'https://', 'data:', '//')):
                    # Resolve relative URL in CSS context
                    absolute_url = urljoin(css_url, url)
                    if self.is_same_domain(absolute_url) and self.is_valid_asset(absolute_url):
                        # Collect new assets instead of adding directly to avoid iterator issues
                        new_assets.add(absolute_url)
                        # Convert to relative path from CSS file location
                        relative_to_css = self.convert_to_relative_path(absolute_url, css_url).lstrip('./')
                        return f'url({relative_to_css})'
                return match.group(0)
            
            modified_content = re.sub(url_pattern, replace_url, content)
            
            # Add new assets after processing
            self.assets.update(new_assets)
            
            # Write back if changed
            if modified_content != content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(modified_content)
                    
        except Exception as e:
            self.log(f"Fehler beim Verarbeiten der CSS-Datei {file_path}: {e}")
    
    def is_valid_asset(self, url):
        """Check if URL is a valid asset to download"""
        # Check if this URL is already a scraped page
        if hasattr(self, 'scraped_pages') and url in self.scraped_pages:
            return False
        
        # Check if this URL is in our discovered URLs (pages to scrape)
        if url in self.discovered_urls:
            return False
        
        # Filter out WordPress API calls and other non-asset URLs
        invalid_paths = [
            '/wp-json/',
            '/wp-admin/',
            '?',  # Query parameters usually indicate dynamic content
            '/feed/',
            '/xmlrpc.php',
            '/wp-login.php'
        ]
        
        # Check if it has a clear asset extension
        asset_extensions = [
            '.jpg', '.jpeg', '.png', '.gif', '.svg', '.ico', '.webp',  # Images
            '.css', '.js',  # Stylesheets and scripts
            '.pdf', '.zip', '.doc', '.docx',  # Documents
            '.woff', '.woff2', '.ttf', '.eot',  # Fonts
            '.mp4', '.avi', '.mov', '.mp3', '.wav',  # Media
            '.xml', '.json', '.txt'  # Data files (but not if they're API endpoints)
        ]
        
        # If it has a clear asset extension, it's likely an asset
        parsed_url = urlparse(url)
        path = parsed_url.path.lower()
        has_asset_extension = any(path.endswith(ext) for ext in asset_extensions)
        
        # If it has an asset extension and no invalid paths, it's valid
        if has_asset_extension:
            return not any(invalid_path in url for invalid_path in invalid_paths)
        
        # If no extension, it's probably a page, not an asset
        return False
    
    def is_same_domain(self, url):
        try:
            parsed = urlparse(url)
            return parsed.netloc == self.domain or parsed.netloc == f"www.{self.domain}" or parsed.netloc == self.domain.replace('www.', '')
        except:
            return False