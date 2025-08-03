#!/usr/bin/env python3
"""Database models and operations for WordPress Project Management System"""

import sqlite3
import json
import os
from datetime import datetime
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from pathlib import Path

DATABASE_PATH = 'projects.db'

@dataclass
class Project:
    """Project data model"""
    id: Optional[int] = None
    name: str = ""
    url: str = ""
    description: str = ""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    favorite: bool = False
    thumbnail_path: Optional[str] = None
    last_scraped_at: Optional[datetime] = None
    total_pages: int = 0
    total_size_mb: float = 0.0
    settings_json: str = "{}"
    
    @property
    def settings(self) -> Dict[str, Any]:
        """Parse settings JSON"""
        try:
            return json.loads(self.settings_json)
        except:
            return {}
    
    @settings.setter
    def settings(self, value: Dict[str, Any]):
        """Set settings as JSON"""
        self.settings_json = json.dumps(value)

@dataclass
class ScrapingSession:
    """Scraping session data model"""
    id: Optional[int] = None
    project_id: int = 0
    timestamp: Optional[datetime] = None
    status: str = "pending"  # pending, running, completed, failed
    pages_count: int = 0
    file_size_mb: float = 0.0
    output_path: str = ""
    duration_seconds: int = 0

@dataclass
class ScrapingLog:
    """Scraping log entry model"""
    id: Optional[int] = None
    session_id: int = 0
    log_level: str = "info"  # debug, info, warning, error
    message: str = ""
    timestamp: Optional[datetime] = None

@dataclass
class ProjectTag:
    """Project tag model"""
    id: Optional[int] = None
    project_id: int = 0
    tag_name: str = ""

@dataclass
class ProjectBackup:
    """Project backup model"""
    id: Optional[int] = None
    project_id: int = 0
    backup_path: str = ""
    created_at: Optional[datetime] = None
    size_mb: float = 0.0

class DatabaseManager:
    """Database operations manager"""
    
    def __init__(self, db_path: str = DATABASE_PATH):
        self.db_path = db_path
        self.init_database()
    
    def get_connection(self) -> sqlite3.Connection:
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable dict-like access
        return conn
    
    def init_database(self):
        """Initialize database with all tables"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Projects table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS projects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    url TEXT NOT NULL UNIQUE,
                    description TEXT DEFAULT '',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    favorite BOOLEAN DEFAULT 0,
                    thumbnail_path TEXT,
                    last_scraped_at TIMESTAMP,
                    total_pages INTEGER DEFAULT 0,
                    total_size_mb REAL DEFAULT 0.0,
                    settings_json TEXT DEFAULT '{}'
                )
            ''')
            
            # Scraping sessions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS scraping_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id INTEGER NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'pending',
                    pages_count INTEGER DEFAULT 0,
                    file_size_mb REAL DEFAULT 0.0,
                    output_path TEXT DEFAULT '',
                    duration_seconds INTEGER DEFAULT 0,
                    FOREIGN KEY (project_id) REFERENCES projects (id) ON DELETE CASCADE
                )
            ''')
            
            # Scraping logs table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS scraping_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER NOT NULL,
                    log_level TEXT DEFAULT 'info',
                    message TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES scraping_sessions (id) ON DELETE CASCADE
                )
            ''')
            
            # Project tags table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS project_tags (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id INTEGER NOT NULL,
                    tag_name TEXT NOT NULL,
                    FOREIGN KEY (project_id) REFERENCES projects (id) ON DELETE CASCADE,
                    UNIQUE(project_id, tag_name)
                )
            ''')
            
            # Project backups table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS project_backups (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id INTEGER NOT NULL,
                    backup_path TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    size_mb REAL DEFAULT 0.0,
                    FOREIGN KEY (project_id) REFERENCES projects (id) ON DELETE CASCADE
                )
            ''')
            
            # Create indexes for better performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_projects_url ON projects (url)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_projects_updated_at ON projects (updated_at)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_projects_favorite ON projects (favorite)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_sessions_project_id ON scraping_sessions (project_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_sessions_timestamp ON scraping_sessions (timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_logs_session_id ON scraping_logs (session_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_tags_project_id ON project_tags (project_id)')
            
            conn.commit()
    
    # Project CRUD operations
    def create_project(self, project: Project) -> int:
        """Create a new project"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO projects (name, url, description, favorite, settings_json)
                VALUES (?, ?, ?, ?, ?)
            ''', (project.name, project.url, project.description, project.favorite, project.settings_json))
            conn.commit()
            return cursor.lastrowid
    
    def get_project(self, project_id: int) -> Optional[Project]:
        """Get project by ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM projects WHERE id = ?', (project_id,))
            row = cursor.fetchone()
            if row:
                return self._row_to_project(row)
            return None
    
    def get_project_by_url(self, url: str) -> Optional[Project]:
        """Get project by URL"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM projects WHERE url = ?', (url,))
            row = cursor.fetchone()
            if row:
                return self._row_to_project(row)
            return None
    
    def get_all_projects(self, favorites_only: bool = False) -> List[Project]:
        """Get all projects"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if favorites_only:
                cursor.execute('SELECT * FROM projects WHERE favorite = 1 ORDER BY updated_at DESC')
            else:
                cursor.execute('SELECT * FROM projects ORDER BY updated_at DESC')
            
            projects = []
            for row in cursor.fetchall():
                projects.append(self._row_to_project(row))
            return projects
    
    def update_project(self, project: Project) -> bool:
        """Update existing project"""
        if not project.id:
            return False
            
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE projects 
                SET name = ?, url = ?, description = ?, favorite = ?, 
                    thumbnail_path = ?, last_scraped_at = ?, total_pages = ?, 
                    total_size_mb = ?, settings_json = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (project.name, project.url, project.description, project.favorite,
                  project.thumbnail_path, project.last_scraped_at, project.total_pages,
                  project.total_size_mb, project.settings_json, project.id))
            conn.commit()
            return cursor.rowcount > 0
    
    def delete_project(self, project_id: int) -> bool:
        """Delete project and all related data"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM projects WHERE id = ?', (project_id,))
            conn.commit()
            return cursor.rowcount > 0
    
    def search_projects(self, query: str) -> List[Project]:
        """Search projects by name, URL, or description"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM projects 
                WHERE name LIKE ? OR url LIKE ? OR description LIKE ?
                ORDER BY updated_at DESC
            ''', (f'%{query}%', f'%{query}%', f'%{query}%'))
            
            projects = []
            for row in cursor.fetchall():
                projects.append(self._row_to_project(row))
            return projects
    
    # Scraping session operations
    def create_scraping_session(self, session: ScrapingSession) -> int:
        """Create a new scraping session"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO scraping_sessions (project_id, status, output_path)
                VALUES (?, ?, ?)
            ''', (session.project_id, session.status, session.output_path))
            conn.commit()
            return cursor.lastrowid
    
    def update_scraping_session(self, session: ScrapingSession) -> bool:
        """Update scraping session"""
        if not session.id:
            return False
            
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE scraping_sessions 
                SET status = ?, pages_count = ?, file_size_mb = ?, duration_seconds = ?
                WHERE id = ?
            ''', (session.status, session.pages_count, session.file_size_mb, 
                  session.duration_seconds, session.id))
            conn.commit()
            return cursor.rowcount > 0
    
    def get_project_sessions(self, project_id: int) -> List[ScrapingSession]:
        """Get all scraping sessions for a project"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM scraping_sessions 
                WHERE project_id = ? 
                ORDER BY timestamp DESC
            ''', (project_id,))
            
            sessions = []
            for row in cursor.fetchall():
                sessions.append(self._row_to_session(row))
            return sessions
    
    # Helper methods
    def _row_to_project(self, row) -> Project:
        """Convert database row to Project object"""
        return Project(
            id=row['id'],
            name=row['name'],
            url=row['url'],
            description=row['description'],
            created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None,
            updated_at=datetime.fromisoformat(row['updated_at']) if row['updated_at'] else None,
            favorite=bool(row['favorite']),
            thumbnail_path=row['thumbnail_path'],
            last_scraped_at=datetime.fromisoformat(row['last_scraped_at']) if row['last_scraped_at'] else None,
            total_pages=row['total_pages'],
            total_size_mb=row['total_size_mb'],
            settings_json=row['settings_json']
        )
    
    def _row_to_session(self, row) -> ScrapingSession:
        """Convert database row to ScrapingSession object"""
        return ScrapingSession(
            id=row['id'],
            project_id=row['project_id'],
            timestamp=datetime.fromisoformat(row['timestamp']) if row['timestamp'] else None,
            status=row['status'],
            pages_count=row['pages_count'],
            file_size_mb=row['file_size_mb'],
            output_path=row['output_path'],
            duration_seconds=row['duration_seconds']
        )

# Global database instance
db = DatabaseManager()

def get_db() -> DatabaseManager:
    """Get database instance"""
    return db