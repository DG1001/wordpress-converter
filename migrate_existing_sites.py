#!/usr/bin/env python3
"""Migration tool to import existing scraped sites into the project database"""

import os
import sys
from datetime import datetime
from urllib.parse import urlparse
from pathlib import Path
from database import get_db, Project

def get_site_info_from_path(site_path):
    """Extract site information from directory structure"""
    try:
        # Parse domain and timestamp from path
        parts = site_path.split(os.sep)
        if len(parts) < 2:
            return None
            
        domain = parts[-2]  # domain folder
        timestamp_str = parts[-1]  # timestamp folder
        
        # Reconstruct URL (assume https)
        url = f"https://{domain}"
        
        # Parse timestamp
        try:
            created_at = datetime.strptime(timestamp_str, '%Y%m%d_%H%M%S')
        except ValueError:
            # Use directory creation time as fallback
            created_at = datetime.fromtimestamp(os.path.getctime(site_path))
        
        # Calculate site statistics
        total_pages = 0
        total_size = 0
        
        for root, dirs, files in os.walk(site_path):
            for file in files:
                file_path = os.path.join(root, file)
                if file.endswith('.html'):
                    total_pages += 1
                total_size += os.path.getsize(file_path)
        
        total_size_mb = total_size / (1024 * 1024)
        
        return {
            'domain': domain,
            'url': url,
            'timestamp': timestamp_str,
            'created_at': created_at,
            'total_pages': total_pages,
            'total_size_mb': total_size_mb,
            'path': site_path
        }
        
    except Exception as e:
        print(f"Error processing {site_path}: {e}")
        return None

def migrate_existing_sites():
    """Migrate all existing scraped sites to the database"""
    scraped_sites_dir = 'scraped_sites'
    
    if not os.path.exists(scraped_sites_dir):
        print("No scraped_sites directory found. Nothing to migrate.")
        return
    
    db = get_db()
    migrated_count = 0
    skipped_count = 0
    
    print("Starting migration of existing scraped sites...")
    print("=" * 50)
    
    # Walk through all scraped sites
    for domain in os.listdir(scraped_sites_dir):
        domain_path = os.path.join(scraped_sites_dir, domain)
        
        if not os.path.isdir(domain_path):
            continue
            
        print(f"\nProcessing domain: {domain}")
        
        # Check if project already exists for this domain
        url = f"https://{domain}"
        existing_project = db.get_project_by_url(url)
        
        if existing_project:
            print(f"  ⚠️  Project already exists for {url}")
            
            # Update project with latest scrape info if needed
            for timestamp in os.listdir(domain_path):
                timestamp_path = os.path.join(domain_path, timestamp)
                
                if not os.path.isdir(timestamp_path):
                    continue
                    
                site_info = get_site_info_from_path(timestamp_path)
                if not site_info:
                    continue
                
                # Update project stats if this is newer
                if (not existing_project.last_scraped_at or 
                    site_info['created_at'] > existing_project.last_scraped_at):
                    
                    existing_project.last_scraped_at = site_info['created_at']
                    existing_project.total_pages = site_info['total_pages']
                    existing_project.total_size_mb = site_info['total_size_mb']
                    
                    db.update_project(existing_project)
                    print(f"  ✅ Updated project stats for {url}")
                    
            skipped_count += 1
            continue
        
        # Create new project for this domain
        latest_scrape = None
        scrape_count = 0
        
        # Find all timestamp directories
        timestamps = []
        for timestamp in os.listdir(domain_path):
            timestamp_path = os.path.join(domain_path, timestamp)
            
            if not os.path.isdir(timestamp_path):
                continue
                
            # Check if it has an index.html (valid scrape)
            index_path = os.path.join(timestamp_path, 'index.html')
            if not os.path.exists(index_path):
                continue
                
            site_info = get_site_info_from_path(timestamp_path)
            if site_info:
                timestamps.append(site_info)
                scrape_count += 1
        
        if not timestamps:
            print(f"  ⚠️  No valid scrapes found for {domain}")
            continue
        
        # Use the latest scrape for project info
        latest_scrape = max(timestamps, key=lambda x: x['created_at'])
        
        # Create project
        project = Project(
            name=domain,
            url=latest_scrape['url'],
            description=f"Migrated project with {scrape_count} scrape(s)",
            created_at=min(timestamps, key=lambda x: x['created_at'])['created_at'],
            last_scraped_at=latest_scrape['created_at'],
            total_pages=latest_scrape['total_pages'],
            total_size_mb=latest_scrape['total_size_mb']
        )
        
        try:
            project_id = db.create_project(project)
            print(f"  ✅ Created project: {project.name}")
            print(f"     URL: {project.url}")
            print(f"     Pages: {project.total_pages}")
            print(f"     Size: {project.total_size_mb:.1f} MB")
            print(f"     Scrapes: {scrape_count}")
            
            migrated_count += 1
            
        except Exception as e:
            print(f"  ❌ Failed to create project for {domain}: {e}")
    
    print("\n" + "=" * 50)
    print(f"Migration completed!")
    print(f"  ✅ Migrated: {migrated_count} projects")
    print(f"  ⚠️  Skipped: {skipped_count} projects (already exist)")
    print(f"  📊 Total: {migrated_count + skipped_count} projects processed")

def main():
    """Main migration function"""
    print("WordPress Project Migration Tool")
    print("================================")
    print()
    
    if len(sys.argv) > 1 and sys.argv[1] == '--force':
        print("⚠️  Force mode enabled - will update existing projects")
        print()
    
    # Confirm migration
    response = input("Do you want to migrate existing scraped sites to the project database? (y/N): ")
    if response.lower() not in ['y', 'yes']:
        print("Migration cancelled.")
        return
    
    migrate_existing_sites()
    
    print()
    print("You can now view your migrated projects at: http://localhost:5000/projects")

if __name__ == '__main__':
    main()