# AI Features for WordPress Converter

This document describes the new AI-powered website editing capabilities added to the WordPress converter.

## Overview

The AI features provide an intelligent, agentic workflow system that allows users to edit converted WordPress sites using natural language instructions. The system analyzes website structure, generates action plans, and executes changes while maintaining site integrity.

## Key Features

### 🧠 Website Memory System
- Analyzes converted site structure, components, and patterns
- Stores persistent memory of website characteristics
- Understands navigation, content patterns, and technology stack

### 🤖 Multi-LLM Support
- Support for multiple AI providers (OpenAI, Anthropic, Ollama)
- Configurable model selection for different tasks
- Automatic fallback between providers

### 📋 Agentic Workflows
- Converts natural language requests into actionable task lists
- Generates detailed implementation plans with dependencies
- Tracks progress and handles error recovery

### ✏️ Smart Editing
- Context-aware file modifications
- Backup and rollback capabilities
- Impact analysis before changes
- Multi-file coordination

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure API Keys

Set environment variables for your preferred LLM providers:

```bash
# For OpenAI
export OPENAI_API_KEY="your_openai_api_key"

# For Anthropic
export ANTHROPIC_API_KEY="your_anthropic_api_key"

# Ollama runs locally - no API key needed
```

### 3. Start the Application

```bash
python app.py
```

### 4. Access AI Interface

Navigate to `/ai/` in your browser to access the AI manager interface.

## Usage Workflow

### Step 1: Convert a WordPress Site
Use the existing converter to scrape and convert a WordPress site to static HTML.

### Step 2: Analyze the Site
1. Go to the AI interface (`/ai/`)
2. Select your converted site
3. Click "Analyze Site" to create website memory

### Step 3: Make AI-Powered Edits
1. Describe your desired changes in natural language
2. Review the generated task list
3. Execute the workflow to apply changes

### Example Requests
- "Make the header sticky and add a dark mode toggle"
- "Improve the mobile responsiveness of the navigation"
- "Add a contact form to the contact page"
- "Change the color scheme to use blue instead of green"

## Architecture

### Core Components

1. **LLM Providers** (`ai_features/llm_providers.py`)
   - Unified interface for multiple AI providers
   - Automatic fallback and error handling

2. **Website Memory** (`ai_features/website_memory.py`)
   - Analyzes and stores website structure
   - Pattern detection and component identification

3. **Agentic Engine** (`ai_features/agentic_engine.py`)
   - Converts requests to actionable workflows
   - Task generation and dependency management

4. **Smart Editor** (`ai_features/smart_editor.py`)
   - Context-aware file editing
   - Backup management and validation

5. **Prompt Templates** (`ai_features/prompts/`)
   - Specialized prompts for different AI tasks
   - Analysis, planning, and coding templates

### Data Storage

- **Memory**: `ai_features/data/memory/` - Website analysis data
- **Sessions**: `ai_features/data/sessions/` - Workflow sessions
- **Backups**: `ai_features/data/backups/` - File backups

## Configuration

### AI Configuration (`ai_config.py`)

The system supports flexible configuration:

```python
{
    "providers": {
        "openai": {
            "models": {
                "planning": "gpt-4o-mini",
                "coding": "gpt-4o", 
                "analysis": "gpt-4o-mini"
            }
        }
    },
    "active_provider": "openai",
    "memory": {
        "auto_analyze_on_conversion": True,
        "cleanup_older_than_days": 30
    },
    "workflow": {
        "require_user_approval": True,
        "backup_before_changes": True
    }
}
```

### Model Selection

Different AI models are used for different tasks:
- **Planning**: Lightweight models for task generation
- **Coding**: Powerful models for code modifications  
- **Analysis**: Efficient models for structure analysis

## API Endpoints

### Core AI Routes

- `GET /ai/` - Main AI interface
- `GET /ai/status` - System status and provider health
- `POST /ai/analyze/{site_path}` - Analyze and create memory
- `POST /ai/workflow/create` - Create new workflow session
- `POST /ai/workflow/{session_id}/execute` - Execute workflow

### Memory Management

- `GET /ai/memory` - List all memories
- `GET /ai/memory/{site_id}` - Get specific memory
- `DELETE /ai/memory/{site_id}` - Delete memory

### Configuration

- `GET /ai/config` - Get AI configuration
- `POST /ai/config` - Update configuration

## User Interface

### Main AI Interface (`/ai/`)
- Site selection and analysis
- Chat-based interaction
- Real-time task management
- Configuration settings

### Todo Viewer (`/ai/todo/{session_id}`)
- Detailed task management
- Progress tracking
- Task editing and execution

### Memory Browser (`/ai/memory`)
- Explore website memories
- View analysis results
- Memory management

## Security Considerations

- API keys are stored as environment variables
- File modifications are sandboxed to scraped sites
- Backup system prevents data loss
- Input validation on all user requests

## Development

### Adding New LLM Providers

1. Extend the `LLMProvider` base class
2. Implement required methods
3. Add to `LLMProviderFactory`
4. Update configuration schema

### Extending Prompt Templates

1. Add methods to appropriate prompt class
2. Follow existing naming conventions
3. Include context parameters
4. Test with different scenarios

### Custom Workflow Steps

1. Extend the `TaskAnalyzer` class
2. Add new task types to enum
3. Implement execution logic
4. Update UI components

## Troubleshooting

### Common Issues

1. **No AI providers configured**
   - Check environment variables
   - Verify API key validity
   - Test provider connections

2. **Memory creation fails**
   - Ensure site path exists
   - Check file permissions
   - Verify HTML structure

3. **Workflow execution errors**
   - Review task dependencies
   - Check file modification permissions
   - Examine backup logs

### Debugging

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

Check data directories:
```bash
ls -la ai_features/data/
```

Test provider connections:
```bash
python -c "from ai_features.ai_config import get_ai_config; print(get_ai_config().get_all_provider_status())"
```

## Performance Optimization

- Use lightweight models for analysis tasks
- Cache website memories between sessions
- Implement request throttling for API calls
- Optimize file reading for large sites

## Future Enhancements

Potential improvements:
- Visual diff preview before applying changes
- Collaborative editing workflows
- Template library for common modifications
- Integration with version control systems
- Advanced SEO optimization suggestions

## Contributing

When adding new features:
1. Follow existing code patterns
2. Add comprehensive tests
3. Update documentation
4. Consider security implications
5. Test with multiple LLM providers

## License

Same as the main WordPress converter project.