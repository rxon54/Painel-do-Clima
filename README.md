# Painel do Clima

A comprehensive climate risk data visualization tool for Brazilian municipalities, powered by the AdaptaBrasil API and enhanced with AI-generated climate narratives.

## Overview

Painel do Clima transforms complex climate risk data into accessible, actionable insights for Brazilian municipalities. The tool consists of two main services: a modern FastAPI data service and a web visualization frontend, working together to provide comprehensive climate indicator analysis.

**Architecture**: `AdaptaBrasil API → Data Processing → FastAPI Service + Web Visualization → AI Narratives`

## 🏗️ System Architecture

### Dual Service Architecture
- **Frontend Service** (Port 8000): Web interface and static file serving
- **Data API Service** (Port 8001): FastAPI-based RESTful API with authentication
- **Data Processing**: Automated ingestion and city-specific data organization

## ✨ Features

- 🌡️ **Comprehensive Climate Data**: Access to 378+ climate indicators from AdaptaBrasil
- 🗺️ **Municipal Focus**: City-specific climate risk assessments for all Brazilian municipalities
- 🔐 **API Authentication**: Secure API access with key-based authentication
- 🤖 **AI-Powered Narratives**: LLM-generated climate summaries in Brazilian Portuguese
- 📊 **Interactive Visualization**: D3.js-powered hierarchical data exploration
- 🔄 **Batch Processing**: Automated data ingestion with rate limiting and retry logic
- 📈 **Future Projections**: Climate trends for 2030 and 2050 scenarios
- 🌐 **RESTful API**: Modern FastAPI service with OpenAPI documentation
- 🏛️ **Hierarchical Structure**: Complete indicator hierarchy navigation
- 📋 **City Panoramas**: Comprehensive city-wide climate overviews

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- OpenAI API key (for AI narratives)
- Internet connection for AdaptaBrasil API access

### Installation

1. **Clone and Setup**:
```bash
git clone https://github.com/rxon54/Painel-do-Clima.git
cd adaptabrasil
pip install -r requirements.txt
```

2. **Configure the Project**:
```bash
cp config.yaml.example config.yaml
# Edit config.yaml with your API keys and settings
```

3. **Start Services**:
```bash
# Start Data API service (port 8001)
./data_api.sh start

# Start Frontend service (port 8000) 
./server.sh start

# Verify both services
./data_api.sh status && ./server.sh status
```

4. **Access the Application**:
- **Web Interface**: http://localhost:8000
- **API Documentation**: http://localhost:8001/docs
- **API Health Check**: http://localhost:8001/health

## 🔐 API Authentication

The Data API service uses key-based authentication for secure access:

### API Keys
Configure in `config.yaml` under `api_security.keys`:
- **master**: Full administrative access
- **frontend**: Frontend client access  
- **llm**: LLM agent access
- **admin**: Administrative operations

### Usage Examples
```bash
# Test authentication status
curl -H "X-API-Key: your-api-key-here" \
     http://localhost:8001/auth/status

# Get city climate panorama
curl -H "X-API-Key: your-frontend-key" \
     http://localhost:8001/api/v1/indicadores/dados/PR/4119905/panorama

# Get indicator hierarchy
curl -H "X-API-Key: your-llm-key" \
     http://localhost:8001/api/v1/indicadores/estrutura/50001/arvore-completa
```

### Public Endpoints (No Authentication)
- `/health` - Service health check
- `/docs`, `/redoc` - API documentation
- `/openapi.json` - OpenAPI specification

## 📡 API Endpoints

### Core Data Endpoints
- `GET /api/v1/indicadores/estrutura` - List all indicators
- `GET /api/v1/indicadores/estrutura/{id}` - Get indicator by ID
- `GET /api/v1/indicadores/count` - Total indicators count
- `GET /api/v1/indicadores/setores` - Available sectors

### City Data Endpoints  
- `GET /api/v1/indicadores/dados/{estado}/{cidade}/panorama` - City climate overview
- `GET /api/v1/indicadores/dados/{estado}/{cidade}/{indicator_id}` - Specific indicator data

### Hierarchy Endpoints
- `GET /api/v1/indicadores/estrutura/{id}/arvore-completa` - Complete indicator tree
- `GET /api/v1/indicadores/estrutura/{id}/filhos` - Direct children only

### Authentication Endpoints
- `GET /auth/status` - Authentication configuration and status

## 🛠️ Data Processing Workflow

### 1. Initial Setup
```bash
# Generate indicator/year pairs from AdaptaBrasil structure
cd backend
python extract_indicator_years_pairs.py adaptaBrasilAPIEstrutura.json .
```

### 2. Data Ingestion
```bash
# Fetch climate data for all configured states
python backend/adaptabrasil_batch_ingestor.py
```

### 3. Data Processing
```bash
# Process and organize city files
python backend/process_city_files.py
```

### 4. AI Narratives (Optional)
```bash
# Filter problematic indicators
python backend/filter_problematic_indicators.py PR 5238 ../data/LLM

# Generate climate narratives with AI
python backend/generate_narratives.py 5238 PR ../data/LLM ../data/LLM_processed
```

5. **Access the Interface**:
- **Main Interface**: http://localhost:8000
- **Direct HTML**: http://localhost:8000/paineldoclima.html
- **Data API**: http://localhost:8000/data
- **Health Check**: http://localhost:8000/health

## Data Pipeline

### 1. Indicator Structure Preparation
Before API ingestion, prepare the indicator structure:

```bash
# Convert CSV to JSON (handles UTF-8 BOM encoding)
cd backend && python csv2json.py

# Generate indicator/year pairs for API ingestion
cd backend && python extract_indicator_years_pairs.py adaptaBrasilAPIEstrutura.json

# Filter out infrastructure indicators (not linked to cities)
cd backend && python filter_infra_out.py adaptaBrasilAPIEstrutura.json adaptaBrasilAPIEstrutura_filtered.json

# Update frontend structure file
cp adaptaBrasilAPIEstrutura_filtered.json ../frontend/ab_structure.json
```

### 2. API Ingestion
The batch ingestor fetches data from two AdaptaBrasil API endpoints:
- `/api/mapa-dados/` - Current indicator values by municipality
- `/api/total/` - Future climate trends (2030/2050) by scenario

**Multi-State Support**: Configure single state (`state: PR`) or multiple states (`state: "RS, SP, RJ"`) in `config.yaml`

**Data Source Files**:
- `mapa-dados.txt` - Indicator/year pairs for current data (generated by `extract_indicator_years_pairs.py`)
- `trends-2030-2050.txt` - Indicator/year pairs for future projections (generated by `extract_indicator_years_pairs.py`)

### 3. Data Processing
Raw API responses are processed into structured city-specific JSON files:
- **Input**: `data/mapa-dados_PR_6000_2022.json`
- **Output**: `data/PR/city_5310.json`

### 4. Web Visualization
The frontend provides an interactive interface with:
- Hierarchical indicator browsing (sector → level → sub-indicators)
- City selection and filtering
- Color-coded value badges based on indicator ranges

### 5. AI Narratives (Optional)
Generate human-readable climate summaries:

```bash
# Generate LLM input templates
python backend/generate_llm_inputs.py
python backend/populate_llm_inputs.py <city_id>

# Filter problematic indicators (run from backend directory)
cd backend && python filter_problematic_indicators.py <state_abbr> <city_id> ../data/LLM

# Generate AI narratives (run from backend directory)
cd backend && python generate_narratives.py <city_id> <state_abbr> ../data/LLM ../data/LLM_processed

# Generate final HTML report (optional)
cd backend && python generate_PdC.py ../data/LLM_processed/<state_abbr>/<city_id>/climate_narrative.json
```

## Configuration

The `config.yaml` file controls all aspects of the system:

```yaml
# Multi-state support - single: 'PR' or multiple: 'RS, SP, RJ'
state: "RS, SP, RJ"
delay_seconds: 2.0
output_dir: ../data/

# Generated by extract_indicator_years_pairs.py
mapa_dados_file: "mapa-dados.txt"
trends_file: "trends-2030-2050.txt"

# LLM configuration for narratives
llm:
  model: "openai/gpt-4o-mini"
  temperature: 0.3
  max_tokens: 10000

# Observability with Langfuse
observability:
  enabled: true
  host: "http://localhost:3080"
  project_name: "Painel do clima"
```

## Project Structure

```
├── backend/                 # Python scripts and API access
│   ├── adaptabrasil_batch_ingestor.py  # Main data ingestion
│   ├── data_api_service.py             # NEW: FastAPI data service
│   ├── process_city_files.py           # Data processing
│   ├── generate_narratives.py          # AI narrative generation
│   ├── serve.py                        # FastAPI web server
│   └── ...
├── frontend/                # Web interface
│   ├── paineldoclima.html              # Main interface
│   ├── paineldoclima.js                # D3.js visualization
│   ├── painel_data_api_integration.js  # NEW: API integration
│   └── ab_structure.json               # Indicator hierarchy
├── data/                    # Generated data (gitignored)
│   ├── PR/                             # State-specific city files
│   ├── LLM/                            # AI input templates
│   └── LLM_processed/                  # Generated narratives
├── config.yaml             # Configuration file
├── data_api.sh             # NEW: Data API service management
└── server.sh               # Main web server management
```

## Services

### Main Application (Port 8000)
```bash
./server.sh start    # Start main visualization app
```

### Data API Service (Port 8001) - NEW!
```bash
./data_api.sh start  # Start structured data API
./data_api.sh test   # Test API endpoints
```

**API Documentation**: http://localhost:8001/docs

**Key Endpoints**:
- `GET /api/v1/indicadores/estrutura/{id}` - Get indicator details
- `GET /api/v1/indicadores/count` - Total indicators count  
- `GET /api/v1/indicadores/setores` - Available sectors
- `GET /health` - Service health check
│   ├── process_city_files.py           # Data processing
│   ├── generate_narratives.py          # AI narrative generation
│   ├── serve.py                        # FastAPI web server
│   └── ...
├── frontend/                # Web interface
│   ├── paineldoclima.html              # Main interface
│   ├── paineldoclima.js                # D3.js visualization
│   └── ab_structure.json               # Indicator hierarchy
├── data/                    # Generated data (gitignored)
│   ├── PR/                             # State-specific city files
│   ├── LLM/                            # AI input templates
│   └── LLM_processed/                  # Generated narratives
└── config.yaml             # Configuration file
```

## API Integration

The system integrates with AdaptaBrasil's REST API with built-in resilience:

- **Multi-State Support**: Process single state or multiple states simultaneously
- **Rate Limiting**: Configurable delays between requests
- **Retry Logic**: Exponential backoff for failed requests
- **Error Handling**: Comprehensive logging and graceful degradation

## Server Management

### Quick Start
```bash
# Start the server
./server.sh start

# Access the application
open http://localhost:8000
```

### Management Commands
```bash
./server.sh start    # Start production server
./server.sh dev      # Start development server with auto-reload
./server.sh stop     # Stop the server
./server.sh status   # Check server status
```

### Manual Server Control
```bash
# Direct Python execution
python backend/serve.py

# Using uvicorn with auto-reload
uvicorn backend.serve:app --reload --host 0.0.0.0 --port 8000
```

## AI Features

### Narrative Generation
The system can generate contextual climate narratives using multiple LLM providers:

- **Multi-Provider Support**: OpenAI, Anthropic, Google, and 100+ others via LiteLLM
- **Structured Prompting**: Seven distinct narrative components
- **Brazilian Portuguese**: Localized content for Brazilian context
- **Observability**: Full tracing via Langfuse integration

### Narrative Components
1. **Introduction**: City overview and climate context
2. **Problem Statement**: Key climate challenges identified
3. **Risk Drivers**: Primary factors contributing to climate risk
4. **Impact Analysis**: Specific effects on different sectors
5. **Daily Implications**: How climate risks affect daily life
6. **Solutions**: Adaptation and mitigation strategies
7. **Conclusion**: Summary and call to action

## Development

### Adding New Indicators
1. Update indicator lists in `mapa-dados.txt` and `trends-2030-2050.txt`
2. Run the batch ingestor to fetch new data
3. Re-process city files
4. Frontend automatically detects new indicators

### Extending API Support
Follow the established patterns:
- Use `fetch_with_retries()` for all API calls
- Respect rate limiting with configurable delays
- Save both processed and raw responses when debugging

## Monitoring and Debugging

### Logs
- `batch_ingestor.log` - API ingestion logs
- Browser dev tools - Frontend data loading issues

### Common Issues
- **API Failures**: Check rate limiting and network connectivity
- **Missing Data**: Verify `config.yaml` state/indicator settings
- **LLM Issues**: Check API keys and Langfuse dashboard  
- **Frontend Problems**: Inspect `data/city_filelist.json` for processed cities

## ⚙️ Configuration Guide

### Environment Setup
```bash
# 1. Copy example configuration
cp config.yaml.example config.yaml

# 2. Edit with your API keys and settings
nano config.yaml  # or your preferred editor
```

### Key Configuration Sections

#### API Security Settings
```yaml
api_security:
  enabled: true  # Set to false to disable authentication
  keys:
    master: "your-secure-master-key-2025"
    frontend: "your-frontend-key-2025"  
    llm: "your-llm-agent-key-2025"
    admin: "your-admin-key-2025"
  public_endpoints:
    - "/health"
    - "/docs"
    - "/redoc"
    - "/openapi.json"
```

#### LLM Integration
```yaml
llm:
  model: "openai/gpt-4o-mini"  # Any LiteLLM-supported model
  temperature: 0.3
  max_tokens: 10000
  timeout: 30
  max_retries: 3

# Required API key
OPENAI_API_KEY: "your-openai-api-key-here"
```

#### Data Processing
```yaml
# States to process (comma-separated for multiple)
state: "PR, SC, RS, SP, RJ, MG, ES, BA"

# Processing settings
delay_seconds: 1  # Rate limiting between API calls
output_dir: "../data/"
save_full_response: true  # Keep raw responses for debugging
```

## 📁 Updated Project Structure

```
adaptabrasil/
├── 🔧 Service Management
│   ├── data_api.sh           # Data API service (port 8001)
│   └── server.sh             # Frontend service (port 8000)
├── ⚙️ Configuration  
│   ├── config.yaml           # Main configuration (create from example)
│   └── config.yaml.example   # Configuration template (NEW)
├── 📁 backend/               # Core processing and API
│   ├── 🚀 data_api_service.py     # FastAPI service with authentication
│   ├── 🌐 serve.py                # Frontend static file server
│   ├── 📡 adaptabrasil_batch_ingestor.py  # Data ingestion from API
│   ├── 🔄 process_city_files.py   # Data processing and organization
│   ├── 🤖 generate_narratives.py  # AI narrative generation
│   └── 🏗️ generate_PdC.py         # HTML report generation
├── 📁 frontend/              # Web visualization interface
│   ├── 🌐 paineldoclima.html      # Main interactive interface
│   ├── 🎨 paineldoclima.css       # Styling and layout
│   ├── ⚡ paineldoclima.js        # D3.js visualization logic
│   └── 📊 ab_structure.json      # Indicator hierarchy structure
├── 📁 data/                  # Processed climate data
│   ├── 📁 PR/, SC/, RS/...        # State-organized city data
│   ├── 📁 LLM/                    # AI processing workspace
│   └── 📁 LLM_processed/          # Generated narratives and reports
├── 📁 context/               # Project documentation and context
└── 📋 requirements.txt        # Python dependencies
```

## 🔄 Service Management Guide

### Dual Service Architecture
The system runs two complementary services:

#### Data API Service (Port 8001) - **Primary API**
```bash
./data_api.sh start    # Start FastAPI service
./data_api.sh stop     # Stop service
./data_api.sh restart  # Restart service  
./data_api.sh status   # Check service status
./data_api.sh logs     # View service logs
```

**Features:**
- 🔐 Key-based authentication
- 📡 RESTful API with OpenAPI documentation
- 🏛️ Hierarchical indicator navigation  
- 📊 City climate panoramas
- 📈 Present data + future projections

#### Frontend Service (Port 8000) - **Web Interface**
```bash
./server.sh start     # Start static file server
./server.sh dev       # Development mode with auto-reload
./server.sh stop      # Stop server
./server.sh status    # Check server status
```

**Features:**
- 🌐 Interactive climate data visualization
- 📱 Responsive web interface
- 🎨 D3.js-powered hierarchical browsing
- 🔍 City search and filtering

### Service Access Points
- **Web Interface**: http://localhost:8000
- **API Documentation**: http://localhost:8001/docs
- **API Health Check**: http://localhost:8001/health  
- **Authentication Test**: http://localhost:8001/auth/status

## 🧪 Development & Testing

### API Testing Examples
```bash
# Test public endpoints (no auth required)
curl http://localhost:8001/health

# Test authentication status
curl -H "X-API-Key: painel-clima-frontend-2025" \
     http://localhost:8001/auth/status

# Get total indicators count
curl -H "X-API-Key: painel-clima-llm-2025" \
     http://localhost:8001/api/v1/indicadores/count

# Get city climate panorama (comprehensive overview)
curl -H "X-API-Key: painel-clima-admin-2025" \
     "http://localhost:8001/api/v1/indicadores/dados/PR/4119905/panorama" | jq .summary

# Get complete indicator hierarchy
curl -H "X-API-Key: painel-clima-master-2025" \
     "http://localhost:8001/api/v1/indicadores/estrutura/50001/arvore-completa" | jq

# Get direct children only
curl -H "X-API-Key: painel-clima-frontend-2025" \
     "http://localhost:8001/api/v1/indicadores/estrutura/50001/filhos" | jq '.indicator.children[].nome'
```

### Data Processing Testing
```bash
# Test single city data fetch
cd backend
python adaptabrasil_simple_query.py PR 5238

# Validate indicator data loading
python -c "
from data_api_service import load_indicators_data
data = load_indicators_data()  
print(f'✅ Loaded {len(data)} climate indicators')
"

# Test AI narrative generation (requires OpenAI key)
python generate_narratives.py 5238 PR ../data/LLM ../data/LLM_processed
```

## Dependencies

### Backend
- **Core**: `fastapi`, `uvicorn`, `requests`, `PyYAML`
- **AI/LLM**: `litellm`, `langfuse`, `pydantic`
- **Templates**: `jinja2`

### Frontend
- **Visualization**: D3.js v7
- **UI**: Native JavaScript and CSS

## Contributing

> [!NOTE]
> This project focuses on Brazilian climate data and requires familiarity with AdaptaBrasil's data structure and Brazilian municipal systems.

1. Fork the repository
2. Create a feature branch
3. Make your changes following the established patterns
4. Test with a small dataset
5. Submit a pull request

## License

This project is designed for public benefit and climate adaptation research in Brazil.

---

**Built for climate resilience in Brazilian municipalities** 🇧🇷

## July 2025 Update: Narrative & Summary HTML Generation

- **No More Duplicates:** Fixed a bug in the AI narrative HTML generation (`generate_PdC.py`) that caused narrative sections to be duplicated before the summary sections. Narrative sections are now inserted only once after the header, and summary sections ("Implicações Cotidianas" and "Soluções e Recomendações") are always placed at the end, before the closing `.container` div.
- **Robust Section Placement:** The script now splits the template after the header and inserts narrative sections, ensuring no repeated content and that summary sections are never nested inside narrative blocks.
- **Output Structure:** The HTML output is now robust, visually clean, and structurally correct for all cities. This ensures a seamless end-to-end workflow for generating climate summaries and recommendations.
- **How to Use:**
  - Run: `python backend/generate_PdC.py <climate_narrative.json> [output.html]`
  - The output HTML will be in `data/LLM_processed/<STATE>/<CITY_ID>/climate_narrative_PdC.html`.

See also the in-code changelog in `backend/generate_PdC.py` for technical details.
