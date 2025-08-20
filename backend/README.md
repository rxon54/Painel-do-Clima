# Backend: Painel do Clima

This folder contains all backend Python code for the Painel do Clima project.

## Core Components

### Data Ingestion & Processing
- **`adaptabrasil_batch_ingestor.py`** - Fetches data from AdaptaBrasil API with rate limiting and retry logic
- **`process_city_files.py`** - Converts raw API responses to city-specific JSON files
- **`generate_llm_inputs.py`** - Creates structured templates for LLM processing
- **`populate_llm_inputs.py`** - Populates templates with city-specific data

### AI/LLM Integration
- **`filter_problematic_indicators.py`** - Filters indicators to focus on problematic areas
- **`generate_narratives.py`** - Orchestrates LLM narrative generation using multiple providers
- **`llm_prompts.py`** - Modular prompt templates for Brazilian Portuguese narratives
- **`narrative_models.py`** - Pydantic data models for structured validation
- **`render_html.py`** - Jinja2-based HTML report generation
- **`generate_PdC.py`** - Final HTML report generation with embedded narratives

### Web Server
- **`serve.py`** - FastAPI server providing both data APIs and static file serving

## Key Features
- **Multi-Provider LLM Support**: OpenAI, Anthropic, Google, and 100+ others via LiteLLM
- **Comprehensive Observability**: Langfuse integration with OpenTelemetry for LLM monitoring
- **Robust Error Handling**: Retry logic, rate limiting, and graceful degradation
- **Configuration-Driven**: All settings managed via `../config.yaml`
- **Brazilian Portuguese**: Specialized prompts for Brazilian climate context

## Usage Patterns
All scripts should be run from the backend directory for proper relative path resolution:
```bash
cd backend
python script_name.py [arguments]
```
