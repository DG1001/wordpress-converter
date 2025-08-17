# Claude Code Implementation Prompt

## Context
I have a WordPress-to-static-site converter (Flask app) at https://github.com/DG1001/wordpress-converter. I want to add agentic AI editing capabilities with multi-LLM support.

## Goal
Implement an agentic workflow system that:
1. Creates website-specific memory/context after conversion
2. Generates todo lists for user editing requests
3. Makes incremental file changes (not full rewrites)
4. Supports multiple LLM providers (OpenAI, Anthropic, Ollama, etc.)

## Implementation Requirements

### 1. Multi-LLM Abstraction Layer
Create `llm_providers.py` with:
- Abstract base class for LLM providers
- Concrete implementations for OpenAI, Anthropic, Ollama
- Unified interface for chat completions
- Configuration management for different models
- Error handling and fallbacks

### 2. Website Memory System
Create `website_memory.py` with:
- Site structure analysis (HTML files, assets, components)
- Content pattern detection (headers, navigation, layouts)
- Component relationship mapping
- Technology stack identification
- Persistent memory storage (JSON/SQLite)

### 3. Agentic Workflow Engine
Create `agentic_engine.py` with:
- Todo generation from user requests
- Task prioritization and dependencies
- Incremental change planning
- Progress tracking
- Change validation

### 4. File Editor with Context
Create `smart_editor.py` with:
- Context-aware file modifications
- Partial file editing (line ranges, sections)
- Backup and rollback capabilities
- Change impact analysis
- Multi-file coordination

### 5. Flask Integration
Extend the existing Flask app with:
- New routes for AI editing (/ai-edit, /generate-todo, /execute-changes)
- WebSocket support for real-time progress
- UI components for todo display and editing controls
- Memory browser/viewer

## Detailed Specifications

### LLM Provider Interface
```python
class LLMProvider(ABC):
    @abstractmethod
    def chat_completion(self, messages: List[dict], **kwargs) -> str:
        pass
    
    @abstractmethod
    def get_model_info(self) -> dict:
        pass
```

### Website Memory Structure
```python
{
    "structure": {
        "pages": [...],
        "assets": [...],
        "components": [...]
    },
    "patterns": {
        "navigation": {...},
        "layouts": {...},
        "styling": {...}
    },
    "metadata": {
        "technology": "WordPress",
        "theme": "detected_theme",
        "converted_at": "timestamp"
    }
}
```

### Todo Item Format
```python
{
    "id": "unique_id",
    "description": "Human readable task",
    "type": "modify_content|add_feature|style_change|structure_change",
    "files_affected": ["file1.html", "style.css"],
    "dependencies": ["other_todo_ids"],
    "estimated_complexity": "low|medium|high",
    "llm_prompt": "Specific instructions for LLM"
}
```

## Integration Points

### With Existing Converter
- Hook into the completion of website scraping
- Add "Enable AI Editing" button on results page
- Preserve existing file browser and download functionality

### New UI Components
- AI chat interface for editing requests
- Todo list viewer with status indicators
- Memory browser showing detected patterns
- LLM provider selection dropdown
- Progress tracker for batch changes

## Configuration
Create `ai_config.py` with:
```python
AI_PROVIDERS = {
    "openai": {
        "api_key_env": "OPENAI_API_KEY",
        "models": {
            "planning": "gpt-4o-mini",
            "coding": "gpt-4o",
            "analysis": "gpt-4o-mini"
        }
    },
    "anthropic": {
        "api_key_env": "ANTHROPIC_API_KEY", 
        "models": {
            "planning": "claude-3-haiku-20240307",
            "coding": "claude-3-sonnet-20240229",
            "analysis": "claude-3-haiku-20240307"
        }
    },
    "ollama": {
        "base_url": "http://localhost:11434",
        "models": {
            "planning": "llama3.1:8b",
            "coding": "codellama:13b",
            "analysis": "llama3.1:8b"
        }
    }
}
```

## Workflow Example
1. User completes WordPress conversion
2. System analyzes site and creates memory
3. User requests: "Make the header sticky and add a dark mode toggle"
4. System generates todo:
   - Analyze current header structure
   - Modify CSS for sticky positioning
   - Add dark mode CSS variables
   - Create toggle button HTML
   - Add JavaScript for toggle functionality
5. User reviews and approves todo
6. System executes changes incrementally with progress updates

## File Structure
```
/ai_features/
├── __init__.py
├── llm_providers.py
├── website_memory.py
├── agentic_engine.py
├── smart_editor.py
├── ai_config.py
└── prompts/
    ├── analysis_prompts.py
    ├── planning_prompts.py
    └── coding_prompts.py

/templates/
├── ai_interface.html
├── todo_viewer.html
└── memory_browser.html

/static/js/
├── ai_chat.js
├── todo_manager.js
└── memory_viewer.js
```

## Requirements to Add
```
openai>=1.0.0
anthropic>=0.8.0
ollama>=0.1.0
tiktoken>=0.5.0
```

## Success Criteria
- Successfully analyze and create memory for converted WordPress sites
- Generate actionable todo lists from natural language requests
- Make precise, incremental file changes without breaking functionality
- Support seamless switching between different LLM providers
- Maintain compatibility with existing converter functionality

Please implement this step-by-step, starting with the LLM abstraction layer and website memory system, then building up to the full agentic workflow.