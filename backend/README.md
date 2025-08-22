# Backend: Painel do Clima

This folder contains all backend Python code for the Painel do Clima project, including the modern FastAPI data service and AI-powered climate narrative generation.

## 🚀 Core Services

### Data API Service (`data_api_service.py`)
**Modern FastAPI service with comprehensive climate data access**
- **Port**: 8001
- **Authentication**: API key-based security
- **Documentation**: http://localhost:8001/docs
- **Features**:
  - 🔐 Multi-key authentication system
  - 📊 City climate panoramas (all Level 2 indicators)
  - 🏛️ Hierarchical indicator navigation (complete trees + direct children)
  - 📈 Present data + future climate projections
  - 🌐 OpenAPI documentation with examples
  - 📝 Request logging and monitoring

**Key Endpoints**:
- `GET /api/v1/indicadores/dados/{estado}/{cidade}/panorama` - Complete city overview
- `GET /api/v1/indicadores/estrutura/{id}/arvore-completa` - Full hierarchy tree  
- `GET /api/v1/indicadores/estrutura/{id}/filhos` - Direct children only
- `GET /api/v1/indicadores/count` - Total indicators available
- `GET /auth/status` - Authentication testing

### Frontend Service (`serve.py`)
**Static file server for web interface**
- **Port**: 8000
- **Purpose**: Serves the interactive web visualization
- **CORS**: Enabled for local development

## 📡 Data Components

### Data Source Generation
- **`csv2json.py`** - Converts CSV indicator structure to JSON (handles UTF-8 BOM encoding)
- **`extract_indicator_years_pairs.py`** - Generates indicator/year pairs from AdaptaBrasil structure
  - Creates `mapa-dados.txt` (current data pairs)
  - Creates `trends-2030-2050.txt` (future projection pairs)
- **`filter_infra_out.py`** - Removes infrastructure indicators not linked to cities
  - Filters out sectors: 40000 (Portuária), 70000 (Rodoviária), 80000 (Ferroviária)
  - Recursively removes all child indicators under these sectors

### Data Ingestion & Processing
- **`adaptabrasil_batch_ingestor.py`** - Fetches data from AdaptaBrasil API with rate limiting and retry logic
  - **Multi-state support**: Process single state (`PR`) or multiple states (`RS, SP, RJ`)
  - Uses indicator/year pairs from generated text files
- **`process_city_files.py`** - Converts raw API responses to city-specific JSON files
- **`generate_llm_inputs.py`** - Creates structured templates for LLM processing
- **`populate_llm_inputs.py`** - Populates templates with city-specific data

## 🤖 AI/LLM Integration

### Narrative Generation
- **`filter_problematic_indicators.py`** - Filters indicators to focus on problematic areas
- **`generate_narratives.py`** - Orchestrates LLM narrative generation using multiple providers
- **`llm_prompts.py`** - Modular prompt templates for Brazilian Portuguese narratives
- **`narrative_models.py`** - Pydantic data models for structured validation
- **`render_html.py`** - Jinja2-based HTML report generation
- **`generate_PdC.py`** - Final HTML report generation with embedded narratives

## 🔧 Service Management

### Data API Service (Primary)
```bash
# From project root
./data_api.sh start     # Start API service (port 8001)
./data_api.sh status    # Check service status
./data_api.sh logs      # View service logs
./data_api.sh restart   # Restart service
```

### Frontend Service
```bash
# From project root  
./server.sh start       # Start frontend (port 8000)
./server.sh dev         # Development mode with auto-reload
./server.sh status      # Check status
```

## 🔐 Authentication

The Data API service requires API keys for protected endpoints:

```bash
# Test authentication
curl -H "X-API-Key: painel-clima-frontend-2025" \
     http://localhost:8001/auth/status

# Access protected data  
curl -H "X-API-Key: painel-clima-llm-2025" \
     http://localhost:8001/api/v1/indicadores/count
```

**API Keys** (configured in `../config.yaml`):
- `master` - Full administrative access
- `frontend` - Frontend client access
- `llm` - LLM agent access  
- `admin` - Administrative operations

## Key Features
- **Multi-Provider LLM Support**: OpenAI, Anthropic, Google, and 100+ others via LiteLLM
- **Comprehensive Observability**: Langfuse integration with OpenTelemetry for LLM monitoring
- **Robust Error Handling**: Retry logic, rate limiting, and graceful degradation
- **Configuration-Driven**: All settings managed via `../config.yaml`
- **Brazilian Portuguese**: Specialized prompts for Brazilian climate context

## Usage Patterns

### Complete Data Pipeline
```bash
# 0. Prepare indicator structure (one-time setup after CSV updates)
python csv2json.py  # Convert CSV to JSON with proper UTF-8 encoding
python filter_infra_out.py adaptaBrasilAPIEstrutura.json adaptaBrasilAPIEstrutura_filtered.json  # Remove infrastructure indicators
python extract_indicator_years_pairs.py adaptaBrasilAPIEstrutura.json .  # Generate data source files

cp adaptaBrasilAPIEstrutura_filtered.json ../frontend/ab_structure.json  # Update frontend

# 1. Fetch data (supports multi-state configuration)
python adaptabrasil_batch_ingestor.py

# 2. Process city files
python process_city_files.py

# 3. Start web server
python serve.py
# OR use management script from project root
cd .. && ./server.sh start
```

### Multi-State Configuration
Configure in `../config.yaml`:
```yaml
# Single state
state: PR

# Multiple states
state: "RS, SP, RJ"
```

All scripts should be run from the backend directory for proper relative path resolution:
```bash
cd backend
python script_name.py [arguments]
```
