# Painel do Clima

**Painel do Clima** is an open-source Python and JavaScript toolkit for retrieving, processing, and visualizing climate risk indicators for Brazilian municipalities, powered by the [AdaptaBrasil API](https://sistema.adaptabrasil.mcti.gov.br/).  
It aims to make complex climate risk data accessible and actionable for local decision-makers, journalists, and citizens.

---

## 🚀 Features

- **Batch Data Ingestion:**  
  Fetches and processes climate risk indicators for all cities and indicators in a state, with robust error handling and logging.

- **Flexible Configuration:**  
  All parameters (state, year, indicators, delay, etc.) are set in a simple `config.yaml`.

- **Clean Data Processing:**  
  Groups and cleans raw API data into per-city files, ready for visualization or further analysis.

- **Interactive Visualization:**  
  A modern web frontend (`frontend/visu_2.html`) lets you explore indicator hierarchies and see city-level values, with color-coded badges and collapsible lists.

- **Indicator Documentation Overlay:**  
  Click any indicator ID in the tree to open a scrollable overlay with detailed documentation, loaded from `frontend/indicators_doc.html`.

- **Easy Integration:**  
  Outputs structured JSON files for dashboards, newsrooms, or further data science.

- **LLM Data Preparation:**  
  Scripts to generate and populate structured JSON files for large language model (LLM) processing, enabling advanced summarization and analysis workflows.

---

## 🏗️ Project Structure

```
adaptabrasil/
├── data/                  # Processed data files (gitignored)
│   ├── PR/city_5310.json  # Example: all indicators for city 5310 (Abatiá/PR)
│   ├── city_filelist.json # Mapping of city codes to files/names/states
│   └── LLM/               # LLM input/output files (per city/sector)
├── backend/               # Python backend scripts and API access
│   ├── adaptabrasil_batch_ingestor.py
│   ├── process_city_files.py
│   ├── generate_llm_inputs.py    # Generate sector-based LLM templates
│   ├── populate_llm_inputs.py    # Populate LLM templates with city data
│   └── ...
├── frontend/              # Frontend HTML, JS, CSS, and docs
│   ├── visu_2.html        # Interactive frontend
│   ├── visu_2.js          # Main JS logic
│   ├── visu_2.css         # Styles
│   └── indicators_doc.html # Indicator documentation (for overlay)
├── config.yaml            # Your local config (not tracked)
├── config.example.yaml    # Example config for new users
├── serve.py               # Simple server (optional)
├── .gitignore
└── README.md
```

---

## ⚡ Quickstart

### 1. Clone the repo

```bash
git clone https://github.com/yourusername/Painel-do-Clima.git
cd Painel-do-Clima
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```
*(You may need to create this file with `requests`, `PyYAML`, `fastapi`, `uvicorn`, etc.)*

### 3. Configure

Copy and edit the example config:

```bash
cp config.example.yaml config.yaml
# Edit config.yaml as needed (state, delay, etc.)
```

### 4. Run the batch ingestor

```bash
python backend/adaptabrasil_batch_ingestor.py
```

### 5. Process city files

```bash
python backend/process_city_files.py
```

### 6. Serve the frontend

```bash
python serve.py
# or
uvicorn serve:app --reload
```
Then open [http://localhost:8000/frontend/visu_2.html](http://localhost:8000/frontend/visu_2.html) in your browser.

### 7. Generate LLM-Powered Climate Narratives

To create structured, human-readable climate narratives using AI:

```bash
# 1. Generate sector-based LLM templates from the main output
python backend/generate_llm_inputs.py

# 2. Populate LLM templates with city-specific data (repeat for each city_id)
python backend/populate_llm_inputs.py <city_id>
# Example:
python backend/populate_llm_inputs.py 5329

# 3. Set up API keys for LLM and observability (choose your provider)
export OPENAI_API_KEY="your_openai_key_here"  # For OpenAI models
# OR
export ANTHROPIC_API_KEY="your_anthropic_key_here"  # For Claude models
# OR 
export GOOGLE_API_KEY="your_google_key_here"  # For Gemini models

# Optional: Set up Langfuse for observability
export LANGFUSE_PUBLIC_KEY="your_langfuse_public_key"
export LANGFUSE_SECRET_KEY="your_langfuse_secret_key"
export LANGFUSE_HOST="https://cloud.langfuse.com"  # or your self-hosted instance

# 4. Configure your preferred model in config.yaml (see LLM section)
# Example models: "openai/gpt-4o-mini", "anthropic/claude-3-sonnet", "gemini/gemini-1.5-pro"

# 5. Generate AI-powered narratives
python backend/generate_narratives.py <city_id> <state_abbr> data/LLM data/LLM_processed
# Example:
python backend/generate_narratives.py 5329 PR data/LLM data/LLM_processed
```

This will create:
- `data/LLM_processed/<STATE>/<CITY_ID>/climate_narrative.json` (structured narrative)
- `data/LLM_processed/<STATE>/<CITY_ID>/climate_narrative.html` (rendered HTML report)

---

## 🤖 LLM Narrative Generation

The project includes an advanced AI-powered narrative generation system that transforms raw climate data into compelling, localized stories:

### Architecture
- **Smart Filtering**: Only processes "problematic" indicators (poor current state or worsening trends)
- **Structured Prompting**: Seven narrative components from introduction to solutions
- **Multi-Provider Support**: Uses LiteLLM for compatibility with OpenAI, Anthropic, Google, and other providers
- **Observability**: Integrated with Langfuse for comprehensive LLM monitoring and debugging
- **Flexible Rendering**: Jinja2 templates for HTML, extensible to other formats
- **Portuguese Focus**: All outputs in Brazilian Portuguese with accessible tone

### Key Files
- `backend/narrative_models.py` - Pydantic data models for validation
- `backend/llm_prompts.py` - Modular prompt templates for each narrative section
- `backend/generate_narratives.py` - Main orchestration with LiteLLM integration
- `backend/render_html.py` - Template-based HTML rendering system

### Supported LLM Providers
Configure via `config.yaml` under the `llm.model` setting:
- **OpenAI**: `openai/gpt-4o-mini`, `openai/gpt-4`, `openai/gpt-3.5-turbo`
- **Anthropic**: `anthropic/claude-3-sonnet`, `anthropic/claude-3-haiku`
- **Google**: `gemini/gemini-1.5-pro`, `gemini/gemini-1.5-flash`
- **And 100+ other providers supported by LiteLLM**

### Observability & Monitoring
- **Langfuse Integration**: Automatic tracing of all LLM calls
- **Component-Level Tracking**: Each narrative component tracked separately
- **Error Handling**: Robust JSON parsing with fallback strategies
- **Performance Metrics**: Token usage, latency, and success rates

### Narrative Components Generated
1. **Introduction** - City context and Climate Impact Index overview
2. **Problem Statement** - Current vs. projected risk quantification
3. **Risk Drivers** - Explanation of vulnerability and adaptation capacity
4. **Specific Impacts** - Concrete climate phenomena and their changes
5. **Daily Life Implications** - Tangible effects on citizens' everyday lives
6. **Solutions** - Actionable preparation strategies and themes
7. **Conclusion** - Empowering message encouraging action

---

## 📝 Documentation

- See [`project requirements document.md`](project%20requirements%20document.md) for detailed requirements and design.
- See [`project_tasks.txt`](project_tasks.txt) for current and planned features.

---

## 🤝 Contributing

Pull requests and suggestions are welcome!  
Please open an issue to discuss major changes.

---

## 📄 License

MIT License (see `LICENSE` file).

---

## 📚 References

- [AdaptaBrasil API](https://sistema.adaptabrasil.mcti.gov.br/)
- Painel do Clima concept briefings

---

*Painel do Clima: Bringing climate risk data to everyone.*