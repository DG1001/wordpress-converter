#!/usr/bin/env python3
"""Screenshot generation service for project thumbnails"""

import os
import asyncio
from pathlib import Path
from urllib.parse import urlparse
from playwright.async_api import async_playwright
from PIL import Image, ImageDraw, ImageFont
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ScreenshotService:
    """Service for generating website screenshots and thumbnails"""
    
    def __init__(self, screenshots_dir='static/screenshots'):
        self.screenshots_dir = Path(screenshots_dir)
        self.screenshots_dir.mkdir(parents=True, exist_ok=True)
        
        # Screenshot settings
        self.viewport_width = 1280
        self.viewport_height = 720
        self.thumbnail_width = 400
        self.thumbnail_height = 225
        
    async def capture_website_screenshot(self, url: str, project_id: int) -> str:
        """Capture screenshot of a website and generate thumbnail"""
        try:
            async with async_playwright() as p:
                # Launch browser
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context(
                    viewport={'width': self.viewport_width, 'height': self.viewport_height}
                )
                page = await context.new_page()
                
                # Set timeout and user agent
                page.set_default_timeout(30000)  # 30 seconds
                await page.set_extra_http_headers({
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                })
                
                # Navigate to page
                logger.info(f"Capturing screenshot for: {url}")
                await page.goto(url, wait_until='networkidle')
                
                # Wait a bit more for dynamic content
                await page.wait_for_timeout(2000)
                
                # Take screenshot
                screenshot_filename = f"project_{project_id}_full.png"
                screenshot_path = self.screenshots_dir / screenshot_filename
                
                await page.screenshot(path=str(screenshot_path), full_page=False)
                
                # Close browser
                await browser.close()
                
                # Generate thumbnail
                thumbnail_path = await self.generate_thumbnail(screenshot_path, project_id)
                
                logger.info(f"Screenshot saved: {screenshot_path}")
                logger.info(f"Thumbnail saved: {thumbnail_path}")
                
                return str(thumbnail_path.relative_to('static'))
                
        except Exception as e:
            logger.error(f"Error capturing screenshot for {url}: {e}")
            # Generate fallback thumbnail
            return await self.generate_fallback_thumbnail(url, project_id)
    
    async def capture_local_screenshot(self, local_path: str, project_id: int) -> str:
        """Capture screenshot of a local HTML file"""
        try:
            if not os.path.exists(local_path):
                raise FileNotFoundError(f"Local file not found: {local_path}")
            
            # Convert to file URL
            file_url = f"file://{os.path.abspath(local_path)}"
            
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context(
                    viewport={'width': self.viewport_width, 'height': self.viewport_height}
                )
                page = await context.new_page()
                
                logger.info(f"Capturing local screenshot: {file_url}")
                await page.goto(file_url, wait_until='networkidle')
                await page.wait_for_timeout(1000)
                
                # Take screenshot
                screenshot_filename = f"project_{project_id}_local.png"
                screenshot_path = self.screenshots_dir / screenshot_filename
                
                await page.screenshot(path=str(screenshot_path), full_page=False)
                await browser.close()
                
                # Generate thumbnail
                thumbnail_path = await self.generate_thumbnail(screenshot_path, project_id)
                
                return str(thumbnail_path.relative_to('static'))
                
        except Exception as e:
            logger.error(f"Error capturing local screenshot: {e}")
            return await self.generate_fallback_thumbnail("Local Site", project_id)
    
    async def generate_thumbnail(self, screenshot_path: Path, project_id: int) -> Path:
        """Generate thumbnail from full screenshot"""
        try:
            # Open and resize image
            with Image.open(screenshot_path) as img:
                # Calculate dimensions to maintain aspect ratio
                img_ratio = img.width / img.height
                thumb_ratio = self.thumbnail_width / self.thumbnail_height
                
                if img_ratio > thumb_ratio:
                    # Image is wider, crop sides
                    new_height = img.height
                    new_width = int(new_height * thumb_ratio)
                    left = (img.width - new_width) // 2
                    img = img.crop((left, 0, left + new_width, new_height))
                else:
                    # Image is taller, crop top/bottom
                    new_width = img.width
                    new_height = int(new_width / thumb_ratio)
                    top = (img.height - new_height) // 2
                    img = img.crop((0, top, new_width, top + new_height))
                
                # Resize to thumbnail size
                img = img.resize((self.thumbnail_width, self.thumbnail_height), Image.Resampling.LANCZOS)
                
                # Save thumbnail
                thumbnail_filename = f"project_{project_id}_thumb.png"
                thumbnail_path = self.screenshots_dir / thumbnail_filename
                img.save(thumbnail_path, 'PNG', optimize=True)
                
                return thumbnail_path
                
        except Exception as e:
            logger.error(f"Error generating thumbnail: {e}")
            return await self.generate_fallback_thumbnail("", project_id)
    
    async def generate_fallback_thumbnail(self, text: str, project_id: int) -> str:
        """Generate a fallback thumbnail with text"""
        try:
            # Create gradient background
            img = Image.new('RGB', (self.thumbnail_width, self.thumbnail_height), color='#f3f4f6')
            draw = ImageDraw.Draw(img)
            
            # Create gradient effect
            for y in range(self.thumbnail_height):
                r = int(59 + (139 - 59) * y / self.thumbnail_height)
                g = int(130 + (69 - 130) * y / self.thumbnail_height)  
                b = int(246 + (19 - 246) * y / self.thumbnail_height)
                color = (r, g, b)
                draw.line([(0, y), (self.thumbnail_width, y)], fill=color)
            
            # Add text
            try:
                # Try to use a nice font
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
                small_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
            except:
                # Fallback to default font
                font = ImageFont.load_default()
                small_font = ImageFont.load_default()
            
            # Draw main text
            main_text = "WordPress Site"
            if text and text != "Local Site":
                try:
                    domain = urlparse(text).hostname or text
                    main_text = domain.replace('www.', '').title()
                except:
                    main_text = text[:20] + "..." if len(text) > 20 else text
            
            # Calculate text position
            bbox = draw.textbbox((0, 0), main_text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            x = (self.thumbnail_width - text_width) // 2
            y = (self.thumbnail_height - text_height) // 2 - 10
            
            # Draw text with shadow
            draw.text((x + 2, y + 2), main_text, fill='rgba(0,0,0,50)', font=font)
            draw.text((x, y), main_text, fill='white', font=font)
            
            # Draw subtitle
            subtitle = "Static Copy"
            bbox = draw.textbbox((0, 0), subtitle, font=small_font)
            sub_width = bbox[2] - bbox[0]
            sub_x = (self.thumbnail_width - sub_width) // 2
            sub_y = y + text_height + 10
            
            draw.text((sub_x + 1, sub_y + 1), subtitle, fill='rgba(0,0,0,30)', font=small_font)
            draw.text((sub_x, sub_y), subtitle, fill='rgba(255,255,255,200)', font=small_font)
            
            # Add website icon
            icon_size = 40
            icon_x = (self.thumbnail_width - icon_size) // 2
            icon_y = y - icon_size - 20
            
            # Simple website icon
            draw.ellipse([icon_x, icon_y, icon_x + icon_size, icon_y + icon_size], 
                        fill='rgba(255,255,255,100)', outline='rgba(255,255,255,150)', width=2)
            
            # Globe lines
            draw.arc([icon_x + 8, icon_y + 8, icon_x + icon_size - 8, icon_y + icon_size - 8], 
                    0, 360, fill='rgba(255,255,255,150)', width=2)
            draw.line([icon_x + icon_size//2, icon_y + 8, icon_x + icon_size//2, icon_y + icon_size - 8], 
                     fill='rgba(255,255,255,150)', width=2)
            draw.arc([icon_x + 12, icon_y + 12, icon_x + icon_size - 12, icon_y + icon_size - 12], 
                    0, 360, fill='rgba(255,255,255,150)', width=1)
            
            # Save thumbnail
            thumbnail_filename = f"project_{project_id}_fallback.png"
            thumbnail_path = self.screenshots_dir / thumbnail_filename
            img.save(thumbnail_path, 'PNG', optimize=True)
            
            return str(thumbnail_path.relative_to('static'))
            
        except Exception as e:
            logger.error(f"Error generating fallback thumbnail: {e}")
            return "screenshots/default.png"  # Return default path
    
    def cleanup_project_screenshots(self, project_id: int):
        """Clean up all screenshots for a project"""
        patterns = [
            f"project_{project_id}_*.png"
        ]
        
        for pattern in patterns:
            for file_path in self.screenshots_dir.glob(pattern):
                try:
                    file_path.unlink()
                    logger.info(f"Deleted screenshot: {file_path}")
                except Exception as e:
                    logger.error(f"Error deleting {file_path}: {e}")

# Global screenshot service instance
screenshot_service = ScreenshotService()

async def generate_project_screenshot(url: str, project_id: int) -> str:
    """Generate screenshot for a project (async function)"""
    return await screenshot_service.capture_website_screenshot(url, project_id)

async def generate_local_project_screenshot(local_path: str, project_id: int) -> str:
    """Generate screenshot for a local project (async function)"""
    return await screenshot_service.capture_local_screenshot(local_path, project_id)

def generate_project_screenshot_sync(url: str, project_id: int) -> str:
    """Generate screenshot for a project (sync wrapper)"""
    return asyncio.run(generate_project_screenshot(url, project_id))

def generate_local_project_screenshot_sync(local_path: str, project_id: int) -> str:
    """Generate screenshot for a local project (sync wrapper)"""
    return asyncio.run(generate_local_project_screenshot(local_path, project_id))

if __name__ == '__main__':
    # Test script
    import sys
    
    if len(sys.argv) != 3:
        print("Usage: python screenshot_service.py <url> <project_id>")
        sys.exit(1)
    
    url = sys.argv[1]
    project_id = int(sys.argv[2])
    
    print(f"Generating screenshot for: {url}")
    result = generate_project_screenshot_sync(url, project_id)
    print(f"Screenshot saved: {result}")