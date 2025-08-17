#!/usr/bin/env python3
"""
Basic integration test for AI features
"""

import os
import sys
import json
from pathlib import Path

def test_ai_modules_import():
    """Test that AI modules can be imported"""
    print("Testing AI module imports...")
    
    try:
        from ai_features import LLMProviderFactory, WebsiteMemory, AgenticEngine, SmartEditor
        from ai_features.ai_config import get_ai_config
        print("✅ All AI modules imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_ai_config():
    """Test AI configuration"""
    print("\nTesting AI configuration...")
    
    try:
        from ai_features.ai_config import get_ai_config
        config = get_ai_config()
        
        # Check basic config structure
        assert 'providers' in config.config
        assert 'memory' in config.config  
        assert 'workflow' in config.config
        
        providers = config.config['providers']
        assert 'openai' in providers
        assert 'anthropic' in providers
        assert 'ollama' in providers
        
        print("✅ AI configuration loaded successfully")
        print(f"   Active provider: {config.get_active_provider()}")
        print(f"   Configured providers: {list(providers.keys())}")
        return True
        
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False

def test_website_memory():
    """Test website memory system"""
    print("\nTesting website memory system...")
    
    try:
        from ai_features.website_memory import WebsiteMemory
        
        memory_manager = WebsiteMemory()
        memories = memory_manager.list_memories()
        
        print("✅ Website memory system working")
        print(f"   Found {len(memories)} existing memories")
        return True
        
    except Exception as e:
        print(f"❌ Memory system error: {e}")
        return False

def test_data_directories():
    """Test that data directories exist"""
    print("\nTesting data directories...")
    
    required_dirs = [
        "ai_features/data/memory",
        "ai_features/data/sessions", 
        "ai_features/data/backups"
    ]
    
    all_exist = True
    for dir_path in required_dirs:
        if os.path.exists(dir_path):
            print(f"✅ {dir_path} exists")
        else:
            print(f"❌ {dir_path} missing")
            all_exist = False
    
    return all_exist

def test_flask_routes():
    """Test that Flask routes are properly registered"""
    print("\nTesting Flask routes registration...")
    
    try:
        from ai_routes import ai_bp
        
        # Check that blueprint has routes
        routes = [rule.rule for rule in ai_bp.url_map.iter_rules()]
        
        expected_routes = [
            '/ai/',
            '/ai/status',
            '/ai/config',
            '/ai/memory',
            '/ai/workflow/create'
        ]
        
        missing_routes = []
        for route in expected_routes:
            # Check if route pattern exists (may have variables)
            found = any(route in r for r in routes)
            if not found:
                missing_routes.append(route)
        
        if missing_routes:
            print(f"❌ Missing routes: {missing_routes}")
            return False
        else:
            print("✅ Flask routes registered successfully")
            print(f"   Total AI routes: {len(routes)}")
            return True
            
    except Exception as e:
        print(f"❌ Flask routes error: {e}")
        return False

def test_prompt_templates():
    """Test prompt templates"""
    print("\nTesting prompt templates...")
    
    try:
        from ai_features.prompts import AnalysisPrompts, PlanningPrompts, CodingPrompts
        
        # Test that prompt methods exist and return strings
        analysis_prompt = AnalysisPrompts.website_structure_analysis(["index.html"], {})
        planning_prompt = PlanningPrompts.generate_todo_list("test request", {})
        coding_prompt = CodingPrompts.html_modification("test.html", "content", "goal", {})
        
        assert isinstance(analysis_prompt, str)
        assert isinstance(planning_prompt, str) 
        assert isinstance(coding_prompt, str)
        
        print("✅ Prompt templates working")
        return True
        
    except Exception as e:
        print(f"❌ Prompt templates error: {e}")
        return False

def test_smart_editor_basic():
    """Test smart editor basic functionality"""
    print("\nTesting smart editor (basic)...")
    
    try:
        from ai_features.smart_editor import FileBackupManager
        
        # Test backup manager
        backup_manager = FileBackupManager()
        
        print("✅ Smart editor components initialized")
        return True
        
    except Exception as e:
        print(f"❌ Smart editor error: {e}")
        return False

def main():
    """Run all tests"""
    print("🤖 AI Features Integration Test")
    print("=" * 40)
    
    tests = [
        test_ai_modules_import,
        test_ai_config,
        test_website_memory,
        test_data_directories,
        test_flask_routes,
        test_prompt_templates,
        test_smart_editor_basic
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 40)
    print(f"Test Results: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 All tests passed! AI features ready to use.")
        print("\nNext steps:")
        print("1. Configure LLM provider API keys in environment variables")
        print("2. Start the Flask app: python app.py")  
        print("3. Visit /ai/ to access the AI interface")
        return True
    else:
        print("❌ Some tests failed. Please check the errors above.")
        return False

if __name__ == "__main__":
    sys.exit(0 if main() else 1)