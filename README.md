# WordPress to Static Site Converter

A comprehensive Flask web application that converts WordPress websites into fully functional static copies with advanced asset handling and cookie banner removal.

*🤖 This application was developed using [XaresAICoder](https://github.com/DG1001/XaresAICoder) and Claude Code*

📖 **[Deutsche Dokumentation](README_de.md)** | 🌍 **English Documentation**

## Features

- 🌐 **Complete Website Capture**: All public pages, posts, and categories
- 📱 **Asset Download**: Automatic download of images, CSS, JavaScript, and fonts
- 🔗 **Two-Phase Domain Replacement**: 100% conversion to relative paths
- 📱 **Srcset Support**: Responsive images with all resolution variants
- 🚫 **Advanced Cookiebot Removal**: Complete banner removal (85+ elements)
- ⚙️ **JavaScript Navigation Protection**: Preserves functional website navigation
- 📊 **Live Progress**: Real-time updates during scraping process
- 📁 **File Browser**: Navigate through complete website structure
- 📦 **ZIP Export**: Download complete static website
- 🎨 **Responsive Design**: Modern UI with TailwindCSS
- ⚡ **Query Parameter Support**: Correct handling of CSS/JS versioning

## Installation

1. **Clone or download the repository**
   ```bash
   git clone <repository-url>
   cd wordpress-static-converter
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install Playwright browser**
   ```bash
   playwright install chromium
   ```

4. **Start the application**
   ```bash
   python app.py
   ```

5. **Open in browser**
   ```
   http://localhost:5000
   ```

## How It Works

### 1. URL Discovery
- Automatic sitemap parsing (`sitemap.xml`, `wp-sitemap.xml`)
- Link extraction from homepage and discovered pages
- WordPress-specific URL patterns recognition
- Intelligent filtering of admin and API endpoints

### 2. Asset Collection
- JavaScript-enabled scraping with Playwright
- Comprehensive asset detection (images, CSS, JS, fonts, videos)
- Srcset processing for responsive images
- Download of all media files within domain
- HTML path adjustment for local navigation
- Preservation of original folder structure

### 3. HTML Processing & Domain Replacement

**Two-Phase Approach:**
- **Phase 1**: Complete asset discovery and download
- **Phase 2**: Post-processing of all HTML files for local references

**Intelligent Path Conversion:**
- Root pages: `./wp-content/uploads/image.jpg`
- Sub pages: `../wp-content/uploads/image.jpg`  
- Deep pages: `../../wp-content/uploads/image.jpg`
- Srcset attributes: `./image-300w.jpg 300w, ./image-150w.jpg 150w`

**Advanced Cookiebot Removal:**
- External Cookiebot scripts (`cookiebot.com`)
- Inline scripts with >80% Cookiebot content
- Cookiebot IDs, classes, and data attributes
- Preservation of functional navigation scripts

**Additional Improvements:**
- Query parameter handling (`style.css?ver=1.2.3`)
- Contact form deactivation
- Preservation of original structure and formatting

## Output Structure

```
scraped_site/
├── index.html
├── about/
│   └── index.html
├── wp-content/
│   ├── themes/
│   │   └── theme-name/
│   │       ├── style.css
│   │       └── assets/
│   └── uploads/
│       └── 2024/
│           └── images/
└── other-pages/
    └── index.html
```

## Limitations

- Only captures publicly accessible content
- Dynamic content requiring database queries is not included
- Contact forms are deactivated for static use
- WordPress admin area is not included

## Example Workflow

1. User opens `http://localhost:5000`
2. Enters WordPress URL: `https://example-wordpress-site.com`
3. Clicks "Start Scraping"
4. Views live progress with detailed logs
5. After completion: Results page with statistics
6. **Browse Files**: Navigate through website structure in browser
7. **ZIP Download**: Download complete static site
8. **Quality Control**: Test pages before final deployment

## Recent Improvements (v2.1)

### ✅ Two-Phase Domain Replacement
- **Implemented**: Complete overhaul of domain reference handling
- **Phase 1**: Discover and download all assets completely
- **Phase 2**: HTML post-processing for local path replacement
- **Result**: 100% domain references replaced with relative paths

### ✅ Advanced Cookiebot Removal
- **Problem Solved**: Cookiebot banners were not completely removed
- **New Technique**: Aggressive removal (85+ elements vs. previous 6)
- **Intelligent Filtering**: Navigation JavaScript remains functional
- **Result**: Complete Cookiebot removal without functionality loss

### ✅ JavaScript Navigation Protection
- **Problem Fixed**: Navigation menus didn't work after scraping
- **Solution**: Conservative script analysis (only >80% Cookiebot content removed)
- **Preservation**: Responsive navigation and hamburger menus remain functional
- **Result**: Perfect navigation functionality in static sites

### ✅ Srcset Support
- **New**: Complete responsive image support
- **Function**: All image variants (300w, 150w, etc.) found and downloaded
- **Relative Paths**: Correct srcset processing for all page levels
- **Result**: Responsive images work perfectly offline

### ✅ Enhanced Asset Recognition
- **Enhancement**: Query parameter handling (style.css?ver=1.2.3)
- **Intelligence**: File extension-based asset recognition
- **Coverage**: CSS, JS, images, fonts, videos fully supported
- **Result**: No missing assets anymore

### ✅ UI & Workflow Improvements  
- **Removed**: Broken preview buttons that didn't work
- **Improved**: File browser as central navigation
- **Workflow**: Clear 8-step process with quality control
- **Result**: Intuitive user guidance with working navigation

## Troubleshooting

### Playwright Installation
If Playwright errors occur:
```bash
playwright install --force chromium
```

### Large Websites
For large sites, increase timeout values in `scraper.py`:
```python
page.set_default_timeout(60000)  # 60 seconds
```

### Memory Issues
For memory-intensive sites:
```bash
export PYTHONHASHSEED=0
python app.py
```

## Development

This application was developed using:
- **[XaresAICoder](https://github.com/DG1001/XaresAICoder)**: AI-powered development environment
- **Claude Code**: Advanced AI coding assistant
- **Collaborative AI Development**: Iterative improvement through AI-human collaboration

### Technology Stack
- **Backend**: Flask with SocketIO for real-time communication
- **Scraping**: Playwright for JavaScript-enabled browsing
- **HTML Processing**: BeautifulSoup for content manipulation
- **Frontend**: TailwindCSS for responsive design
- **Asset Handling**: Custom logic for WordPress-specific patterns

### Key Technical Innovations
- Two-phase domain replacement architecture
- Conservative JavaScript filtering for navigation preservation
- Intelligent asset validation with conflict resolution
- Real-time progress tracking with WebSocket communication

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Test thoroughly with real WordPress sites
4. Submit a pull request with detailed description

## License

This project is open source. Please check the license file for details.

---

*Developed with ❤️ using AI-powered development tools*