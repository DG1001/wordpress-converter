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
                    self.discovered_urls.add(loc.text)
                    
        except Exception as e:
            self.log(f"Fehler beim Parsen der Sitemap: {e}")
    
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
                if self.is_same_domain(link) and link not in self.discovered_urls:
                    self.discovered_urls.add(link)
            
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
            
            # Process HTML and extract assets
            soup = BeautifulSoup(content, 'html.parser')
            self.process_html_assets(soup, url)
            
            # Save processed HTML
            self.save_html_file(url, str(soup))
            
            page.close()
            
        except Exception as e:
            self.log(f"Fehler beim Scraping von {url}: {e}")
    
    def process_html_assets(self, soup, page_url):
        # Process images
        for img in soup.find_all('img', src=True):
            src = img['src']
            absolute_url = urljoin(page_url, src)
            if self.is_same_domain(absolute_url):
                self.assets.add(absolute_url)
                img['src'] = self.convert_to_relative_path(absolute_url)
        
        # Process CSS links
        for link in soup.find_all('link', href=True):
            if link.get('rel') and 'stylesheet' in link.get('rel'):
                href = link['href']
                absolute_url = urljoin(page_url, href)
                if self.is_same_domain(absolute_url):
                    self.assets.add(absolute_url)
                    link['href'] = self.convert_to_relative_path(absolute_url)
        
        # Process JavaScript
        for script in soup.find_all('script', src=True):
            src = script['src']
            absolute_url = urljoin(page_url, src)
            if self.is_same_domain(absolute_url):
                self.assets.add(absolute_url)
                script['src'] = self.convert_to_relative_path(absolute_url)
        
        # Process internal links
        for a in soup.find_all('a', href=True):
            href = a['href']
            if not href.startswith(('#', 'mailto:', 'tel:', 'javascript:')):
                absolute_url = urljoin(page_url, href)
                if self.is_same_domain(absolute_url):
                    a['href'] = self.convert_to_relative_path(absolute_url)
        
        # Disable forms
        for form in soup.find_all('form'):
            form['action'] = ''
            form['method'] = 'get'
            for input_tag in form.find_all('input', type='submit'):
                input_tag['type'] = 'button'
    
    def convert_to_relative_path(self, url):
        parsed = urlparse(url)
        path = parsed.path
        
        if not path or path == '/':
            return './index.html'
        
        if path.endswith('/'):
            return '.' + path + 'index.html'
        
        # Check if it's an asset
        if any(path.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif', '.css', '.js', '.svg', '.ico', '.pdf', '.woff', '.woff2', '.ttf']):
            return '.' + path
        
        # Regular page
        return '.' + path + ('/index.html' if not path.endswith('.html') else '')
    
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
            if not path.endswith('.html'):
                dir_path = os.path.join(self.output_dir, path.strip('/'))
                os.makedirs(dir_path, exist_ok=True)
                file_path = os.path.join(dir_path, 'index.html')
            else:
                dir_path = os.path.dirname(os.path.join(self.output_dir, path.strip('/')))
                if dir_path:
                    os.makedirs(dir_path, exist_ok=True)
                file_path = os.path.join(self.output_dir, path.strip('/'))
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    def download_assets(self):
        for asset_url in self.assets:
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
            
            if dir_path:
                os.makedirs(dir_path, exist_ok=True)
            
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
                    
        except Exception as e:
            self.log(f"Download fehlgeschlagen für {url}: {e}")
    
    def is_same_domain(self, url):
        try:
            parsed = urlparse(url)
            return parsed.netloc == self.domain or parsed.netloc == f"www.{self.domain}" or parsed.netloc == self.domain.replace('www.', '')
        except:
            return False