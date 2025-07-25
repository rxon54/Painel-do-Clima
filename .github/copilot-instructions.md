# Copilot Instructions: Painel do Clima

## Project Overview
**Painel do Clima** is a climate risk data vi### 2. LLM Narrative Generation Patterns
- **Data Filtering**: `is_indicator_problematic()` filters out "good" indicators based on `proporcao_direta` and `rangelabel`
- **Structured Prompting**: Seven distinct narrative components with Brazilian Portuguese focus
- **Multi-Provider Support**: LiteLLM enables OpenAI, Anthropic, Google, and 100+ other providers
- **Observability**: Langfuse integration for comprehensive LLM monitoring and debugging
- **Robust Parsing**: JSON extraction with markdown fallback for LLM responses
- **Template Rendering**: Jinja2-based system auto-creates HTML templates if missingzation tool for Brazilian municipalities. It fetches data from the AdaptaBrasil API, processes it into city-specific files, and provides an interactive frontend for exploring climate indicators.

**Core Architecture**: `API Ingestion → Data Processing → Web Visualization`

## Key Workflows

### 1. Data Pipeline (Backend)
```bash
# 1. Configure target state and indicators in config.yaml
# 2. Fetch raw data from AdaptaBrasil API
python backend/adaptabrasil_batch_ingestor.py

# 3. Process into per-city JSON files
python backend/process_city_files.py

# 4. Generate LLM input templates and populate with city data
python backend/generate_llm_inputs.py
python backend/populate_llm_inputs.py <city_id>

# 5. Filter problematic indicators (NEW STEP - run from backend dir)
cd backend && python filter_problematic_indicators.py <state_abbr> <city_id> ../data/LLM

# 6. Generate AI-powered climate narratives (requires OpenAI API key - run from backend dir)
cd backend && python generate_narratives.py <city_id> <state_abbr> ../data/LLM ../data/LLM_processed

# 7. Serve frontend and data
python backend/serve.py
```

### 2. API Integration Patterns
- **Rate Limiting**: Always use configurable delays (`config.yaml: delay_seconds`)
- **Retry Logic**: All API calls use `fetch_with_retries()` with exponential backoff
- **Two API Types**:
  - `/api/mapa-dados/` - Current indicator values by municipality
  - `/api/total/` - Future trends (2030/2050) by scenario

### 3. Data Structure Conventions
- **Input Sources**: Text files like `mapa-dados.txt` (format: `indicator_id/year` per line)
- **Raw Output**: `data/mapa-dados_PR_6000_2022.json`
- **Processed Output**: `data/PR/city_5310.json` (all indicators for one city)
- **City Catalog**: `data/city_filelist.json` (maps city codes to names/files)

## Frontend Architecture

### Component Structure
- `paineldoclima.html` - Main interface with controls and D3.js visualization
- `ab_structure.json` - Complete indicator hierarchy and metadata (~9k indicators)
- **Hierarchical Display**: Indicators organized by sector → level → sub-indicators

### Data Flow Pattern
```javascript
// 1. Load indicator structure
loadStructureData() → buildHierarchy()

// 2. Load city-specific data
loadCityData() → mergeWithStructure()

// 3. Render interactive tree with value badges
renderVisualization()
```

## Critical File Patterns

### Configuration Management
- `config.yaml` - Single source of truth for API parameters, file paths, delays
- Never hardcode API endpoints or delays in scripts

### Error Handling & Logging
- All batch operations log to `batch_ingestor.log`
- API failures are logged but don't stop batch processing
- Use `logging.info()` for progress, `logging.error()` for failures

### File Organization
```
backend/     # Python scripts, API access, data processing
  ├── generate_narratives.py    # LLM orchestration and narrative generation
  ├── narrative_models.py       # Pydantic models for structured validation
  ├── llm_prompts.py           # Modular prompt templates  
  └── render_html.py           # Jinja2-based HTML rendering
frontend/    # HTML/JS/CSS, indicator documentation  
data/        # Generated JSON files (gitignored)
  ├── PR/    # State-specific city files
  ├── LLM/   # Populated LLM input files (per city/sector)
  ├── LLM_processed/ # Generated narratives and HTML reports
  └── downloads/ # Archived raw API responses
templates/   # Jinja2 templates (auto-created)
```

## Development Guidelines

### Adding New Indicators
1. Update text files (`mapa-dados.txt`, `trends-2030-2050.txt`)
2. Run batch ingestor to fetch new data
3. Re-run processor to update city files
4. Frontend automatically picks up new indicators

### API Extensions
- Follow the `fetch_with_retries()` pattern for all new API calls
- Always respect rate limiting (`time.sleep(delay)`)
- Save both processed and raw responses when `debug: true`

### Frontend Data Integration
- City data structure: `{id, name, indicators: [{indicator_id, year, value, future_trends: {2030: {...}, 2050: {...}}}]}`
- Indicator structure: Hierarchical tree with `children` arrays
- Value display: Color-coded badges based on indicator ranges

## LLM Narrative Generation Patterns
- **Data Filtering**: `is_indicator_problematic()` filters out "good" indicators based on `proporcao_direta` and `rangelabel`
- **Structured Prompting**: Seven distinct narrative components with Brazilian Portuguese focus
- **Multi-Provider Support**: LiteLLM enables OpenAI, Anthropic, Google, and 100+ other providers
- **Observability**: Langfuse integration via OpenTelemetry for comprehensive LLM monitoring and debugging
- **Robust Parsing**: JSON extraction with markdown fallback for LLM responses
- **Template Rendering**: Jinja2-based system auto-creates HTML templates if missing

## Key Dependencies
- **Backend**: `requests`, `PyYAML`, `fastapi`, `uvicorn`, `pydantic`, `jinja2`
- **LLM Integration**: `litellm`, `langfuse` (multi-provider LLM support with observability)
- **Frontend**: D3.js for visualization, native JS for data handling
- **Serving**: FastAPI serves both data APIs and static frontend files

## Common Debugging
- Check `batch_ingestor.log` for API failures
- Verify `config.yaml` state/indicator settings
- Use browser dev tools to inspect data loading in frontend
- Compare `data/city_filelist.json` to ensure cities are processed
- **LLM Issues**: Check Langfuse dashboard for failed generations, verify API keys are set
- **Model Configuration**: Ensure `config.yaml` has valid model format (e.g., "openai/gpt-4o-mini")
- **OpenTelemetry Observability**: LLM calls automatically traced via Langfuse OpenTelemetry integration
- **JSON Parsing**: Enable debug prints in `generate_llm_response()` to see raw LLM outputs
