# Copilot Instructions: Painel do Clima

## Project Overview
**Painel do Clima** is a climate risk data visualization tool for Brazilian municipalities. It fetches data from the AdaptaBrasil API, processes it into city-specific files, and provides an interactive frontend for exploring climate indicators.

**Core Architecture**: `API Ingestion → Data Processing → Data API Service → Web Visualization`

## Key Workflows

### 1. Data Pipeline (Backend)
```bash
# 1. Configure target state(s) and indicators in config.yaml
# Single state: state: PR
# Multiple states: state: "RS, SP, RJ"

# 2. Generate indicator/year pairs from AdaptaBrasil structure
cd backend
python extract_indicator_years_pairs.py adaptaBrasilAPIEstrutura.json .

# 3. Fetch raw data from AdaptaBrasil API (supports multi-state)
python adaptabrasil_batch_ingestor.py

# 4. Process into per-city JSON files
python process_city_files.py

# 5. Generate LLM input templates and populate with city data
python generate_llm_inputs.py
python populate_llm_inputs.py <city_id>

# 6. Filter problematic indicators (NEW STEP - run from backend dir)
cd backend && python filter_problematic_indicators.py <state_abbr> <city_id> ../data/LLM

# 7. Generate AI-powered climate narratives (requires OpenAI API key - run from backend dir)
cd backend && python generate_narratives.py <city_id> <state_abbr> ../data/LLM ../data/LLM_processed

# 8. Generate final HTML report (optional - run from backend dir)
cd backend && python generate_PdC.py ../data/LLM_processed/<state_abbr>/<city_id>/climate_narrative.json

# 9. Start services (UPDATED STANDARD)
# Main visualization app (port 8000)
./server.sh start

# Data API service (port 8001) - NEW STANDARD
./data_api.sh start

# Verify both services are running
./server.sh status && ./data_api.sh status
```

### 2. API Integration Patterns
- **AdaptaBrasil API Access**: External climate data fetching with retry logic and rate limiting
- **Data API Service**: Internal structured data access (NEW STANDARD for all indicator queries)
- **Multi-State Support**: Configure single state (`state: PR`) or multiple states (`state: "RS, SP, RJ"`) in config.yaml
- **Rate Limiting**: Always use configurable delays (`config.yaml: delay_seconds`) for external APIs
- **Retry Logic**: All external API calls use `fetch_with_retries()` with exponential backoff
- **Two External API Types**:
  - `/api/mapa-dados/` - Current indicator values by municipality
  - `/api/total/` - Future trends (2030/2050) by scenario

### 3. Data API Service (NEW STANDARD)
**Structured Data Access**: Use the dedicated FastAPI service for all indicator data access
```bash
# Start Data API service (port 8001)
./data_api.sh start

# Test endpoints
./data_api.sh test

# Check service status
./data_api.sh status
```

**Key Endpoints** (Standard for all API work):
- `GET /api/v1/indicadores/estrutura/{id}` - Get indicator structure by ID
- `GET /api/v1/indicadores/count` - Total indicators count
- `GET /api/v1/indicadores/setores` - Available sectors list
- `GET /health` - Service health monitoring

**API Documentation**: Always available at http://localhost:8001/docs

### 4. Frontend Integration
- **Input Generation**: Use `extract_indicator_years_pairs.py` to create input files from AdaptaBrasil structure
- **Input Sources**: Text files like `mapa-dados.txt` (format: `indicator_id/year` per line)
- **Raw Output**: `data/mapa-dados_PR_6000_2022.json` (state-specific naming for multi-state support)
- **Processed Output**: `data/PR/city_5310.json` (all indicators for one city)
- **City Catalog**: `data/city_filelist.json` (maps city codes to names/files)

## Frontend Architecture

### Component Structure
- `paineldoclima.html` - Main interface with controls and D3.js visualization
- `ab_structure.json` - Complete indicator hierarchy and metadata (~9k indicators)
- **Hierarchical Display**: Indicators organized by sector → level → sub-indicators

### Data Flow Pattern (UPDATED STANDARD)
```javascript
// 1. Use Data API service for indicator structure (NEW STANDARD)
const painelAPI = new PainelDataAPI('http://localhost:8001');
const indicator = await painelAPI.getIndicatorStructure(indicatorId);

// 2. Load indicator structure
loadStructureData() → buildHierarchy()

// 3. Load city-specific data
loadCityData() → mergeWithStructure()

// 4. Render interactive tree with value badges
renderVisualization()
```

**API Client Usage** (Standard Pattern):
```javascript
// Always use the PainelDataAPI class for structured data access
const painelAPI = new PainelDataAPI();
const indicator = await painelAPI.getIndicatorStructure('2');
const sectors = await painelAPI.getAvailableSectors();
const health = await painelAPI.checkHealth();
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
  ├── adaptabrasil_batch_ingestor.py  # External API data ingestion
  ├── data_api_service.py            # NEW STANDARD: FastAPI data service
  ├── generate_narratives.py          # LLM orchestration and narrative generation
  ├── narrative_models.py             # Pydantic models for structured validation
  ├── llm_prompts.py                 # Modular prompt templates  
  ├── render_html.py                 # Jinja2-based HTML rendering
  └── serve.py                       # Main web server (frontend serving)
frontend/    # HTML/JS/CSS, indicator documentation  
  ├── paineldoclima.html             # Main visualization interface
  ├── paineldoclima.js              # D3.js visualization logic
  ├── painel_data_api_integration.js # NEW STANDARD: Data API client
  └── ab_structure.json             # Indicator hierarchy
data/        # Generated JSON files (gitignored)
  ├── PR/    # State-specific city files
  ├── LLM/   # Populated LLM input files (per city/sector)
  ├── LLM_processed/ # Generated narratives and HTML reports
  └── downloads/ # Archived raw API responses
templates/   # Jinja2 templates (auto-created)
server.sh    # Main web server management script
data_api.sh  # NEW STANDARD: Data API service management
```

## Development Guidelines

### API Development Standards (NEW)
**All new API development must follow these patterns:**

1. **FastAPI Architecture**: Use FastAPI with Pydantic models for all new API endpoints
2. **Error Handling**: Proper HTTP status codes (200, 404, 500) with detailed error responses
3. **Input Validation**: Use Pydantic models and regex validation for path/query parameters
4. **OpenAPI Documentation**: Auto-generated docs with proper response models and examples
5. **Request Logging**: Comprehensive request/response logging with timing metrics
6. **Health Monitoring**: Always include `/health` endpoint with service status
7. **CORS Configuration**: Proper CORS headers for frontend integration
8. **Performance**: Use caching strategies (LRU cache, in-memory data structures)

**Reference Implementation**: See `backend/data_api_service.py` for the complete pattern

### Service Management Standards (NEW)
- Use management scripts (`.sh`) for service control: start/stop/status/logs/test
- Background services with PID file tracking
- Comprehensive logging to dedicated log files
- Health check endpoints for monitoring
- Port standardization: 8000 (main app), 8001 (data API), 8002+ (future services)

### Adding New Indicators
1. Update AdaptaBrasil structure file (`adaptaBrasilAPIEstrutura.json`)
2. Regenerate indicator/year pairs: `python extract_indicator_years_pairs.py adaptaBrasilAPIEstrutura.json .`
3. Run batch ingestor to fetch new data
4. Re-run processor to update city files
5. Frontend automatically picks up new indicators

### Multi-State Processing
- Configure states in `config.yaml`: `state: "RS, SP, RJ"`
- Batch ingestor processes all states automatically
- Files are organized by state: `data/mapa-dados_RS_2_2020.json`
- Use management script for easy server control: `./server.sh {start|dev|stop|status}`

### API Extensions
- Follow the `fetch_with_retries()` pattern for all new API calls
- Always respect rate limiting (`time.sleep(delay)`)
- Save both processed and raw responses when `debug: true`

### Frontend Data Integration (UPDATED)
- **NEW STANDARD**: Use `PainelDataAPI` class for all indicator data access
- **API-First Approach**: Prefer API calls over direct JSON file access
- **Error Handling**: Proper try/catch with fallback mechanisms
- **Caching**: Client-side caching for frequently accessed data
- **City data structure**: `{id, name, indicators: [{indicator_id, year, value, future_trends: {2030: {...}, 2050: {...}}}]}`
- **Indicator structure**: Hierarchical tree with `children` arrays
- **Value display**: Color-coded badges based on indicator ranges

**Integration Example**:
```javascript
// NEW STANDARD: Use Data API for indicator access
const painelAPI = new PainelDataAPI();
const indicator = await painelAPI.getIndicatorStructure(indicatorId);
updateVisualization(indicator);
```

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
- **API Services**: FastAPI for structured data access with OpenAPI documentation
- **Service Management**: Bash scripts for service lifecycle management

## Common Debugging
- Check `batch_ingestor.log` for external API failures
- Verify `config.yaml` state/indicator settings
- **NEW**: Check Data API service status: `./data_api.sh status` and logs: `./data_api.sh logs`
- **NEW**: Test Data API endpoints: `./data_api.sh test`
- **NEW**: Verify Data API health: `curl http://localhost:8001/health`
- Use browser dev tools to inspect data loading in frontend
- Compare `data/city_filelist.json` to ensure cities are processed
- **LLM Issues**: Check Langfuse dashboard for failed generations, verify API keys are set
- **Model Configuration**: Ensure `config.yaml` has valid model format (e.g., "openai/gpt-4o-mini")
- **OpenTelemetry Observability**: LLM calls automatically traced via Langfuse OpenTelemetry integration
- **JSON Parsing**: Enable debug prints in `generate_llm_response()` to see raw LLM outputs
- **Service Integration**: Verify both main app (8000) and data API (8001) are running for full functionality

---

## Data API Service Standards (REFERENCE IMPLEMENTATION)

The **Data API Service** (`backend/data_api_service.py`) serves as the **standard template** for all API development in this project. Any new API functionality should follow these established patterns:

### Architecture Standards
```python
# 1. FastAPI with Pydantic models
from fastapi import FastAPI, HTTPException, Path as PathParam
from pydantic import BaseModel, Field

# 2. Proper error handling with HTTP status codes
@app.get("/api/v1/endpoint/{param}")
async def endpoint(param: str = PathParam(..., pattern=r"^[0-9]+$")):
    try:
        # Business logic
        return response_model
    except Exception as e:
        logger.error(f"Error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# 3. Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"Request: {request.method} {request.url.path}")
    response = await call_next(request)
    logger.info(f"Response: {response.status_code}")
    return response
```

### Required Endpoints
Every API service must implement:
- `GET /health` - Service health check with metrics
- `GET /docs` - Auto-generated OpenAPI documentation
- Proper CORS middleware configuration
- Comprehensive error responses with details

### Performance Standards
- **Caching**: Use `@lru_cache` for expensive operations
- **Efficient Data Structures**: Dictionary lookups for O(1) access
- **Resource Management**: One-time data loading with error handling
- **Memory Optimization**: In-memory caching for frequently accessed data

### Service Management
- Management script (`.sh`) with: start/stop/restart/status/dev/logs/test commands
- Background service with PID file tracking
- Dedicated log file with request/response tracking
- Health monitoring with service statistics

### Documentation Requirements
- Complete OpenAPI/Swagger documentation at `/docs`
- Response models with examples using Pydantic
- Error response models with proper HTTP status codes
- Integration examples and client usage patterns

**Reference Files**:
- `backend/data_api_service.py` - Complete API implementation
- `data_api.sh` - Service management script
- `frontend/painel_data_api_integration.js` - Client integration
- `DATA_API_README.md` - Comprehensive documentation

**This is the established standard - all new API development must follow these patterns for consistency and maintainability.**