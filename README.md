# Painel do Clima

A comprehensive climate risk data visualization tool for Brazilian municipalities, powered by the AdaptaBrasil API and enhanced with AI-generated climate narratives.

## Overview

Painel do Clima transforms complex climate risk data into accessible, actionable insights for Brazilian municipalities. The tool fetches data from the AdaptaBrasil API, processes it into city-specific files, and provides an interactive web interface for exploring over 9,000 climate indicators across multiple sectors.

**Core Architecture**: `API Ingestion → Data Processing → Web Visualization → AI Narratives`

## Features

- 🌡️ **Comprehensive Climate Data**: Access to thousands of climate indicators from AdaptaBrasil
- 🗺️ **Municipal Focus**: City-specific climate risk assessments for Brazilian municipalities
- 🤖 **AI-Powered Narratives**: LLM-generated climate summaries in Brazilian Portuguese
- 📊 **Interactive Visualization**: D3.js-powered hierarchical data exploration
- 🔄 **Batch Processing**: Automated data ingestion with rate limiting and retry logic
- 📈 **Future Projections**: Climate trends for 2030 and 2050 scenarios
- 🌐 **Web Interface**: Clean, accessible frontend for data exploration

## Quick Start

### Prerequisites

- Python 3.8+
- OpenAI API key (for AI narratives)
- Internet connection for AdaptaBrasil API access

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd adaptabrasil
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure the project:
```bash
cp config.yaml.example config.yaml
# Edit config.yaml with your settings
```

4. Set up environment variables for AI features:
```bash
export OPENAI_API_KEY="your-api-key-here"
```

### Running the Application

1. **Fetch Climate Data**:
```bash
python backend/adaptabrasil_batch_ingestor.py
```

2. **Process City Files**:
```bash
python backend/process_city_files.py
```

3. **Start the Web Server**:
```bash
python backend/serve.py
```

4. **Access the Interface**:
Open `http://localhost:8000` in your browser

## Data Pipeline

### 1. API Ingestion
The batch ingestor fetches data from two AdaptaBrasil API endpoints:
- `/api/mapa-dados/` - Current indicator values by municipality
- `/api/total/` - Future climate trends (2030/2050) by scenario

### 2. Data Processing
Raw API responses are processed into structured city-specific JSON files:
- **Input**: `data/mapa-dados_PR_6000_2022.json`
- **Output**: `data/PR/city_5310.json`

### 3. Web Visualization
The frontend provides an interactive interface with:
- Hierarchical indicator browsing (sector → level → sub-indicators)
- City selection and filtering
- Color-coded value badges based on indicator ranges

### 4. AI Narratives (Optional)
Generate human-readable climate summaries:

```bash
# Generate LLM input templates
python backend/generate_llm_inputs.py
python backend/populate_llm_inputs.py <city_id>

# Generate AI narratives
python backend/generate_narratives.py <city_id> <state_abbr> data/LLM data/LLM_processed
```

## Configuration

The `config.yaml` file controls all aspects of the system:

```yaml
# Target state and API settings
state: PR
delay_seconds: 5.0
output_dir: ../data/

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

- **Rate Limiting**: Configurable delays between requests
- **Retry Logic**: Exponential backoff for failed requests
- **Error Handling**: Comprehensive logging and graceful degradation

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
