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
  A modern web frontend (`visu_2.html`) lets you explore indicator hierarchies and see city-level values, with color-coded badges and collapsible lists.

- **Easy Integration:**  
  Outputs structured JSON files for dashboards, newsrooms, or further data science.

---

## 🏗️ Project Structure

```
adaptabrasil/
├── data/                  # Processed data files (gitignored)
│   ├── PR/city_5310.json  # Example: all indicators for city 5310 (Abatiá/PR)
│   └── city_filelist.json # Mapping of city codes to files/names/states
├── adaptabrasil_batch_ingestor.py   # Batch API ingestor
├── process_city_files.py            # Groups data into per-city files
├── visu_2.html                      # Interactive frontend
├── config.yaml                      # Your local config (not tracked)
├── config.example.yaml              # Example config for new users
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
python adaptabrasil_batch_ingestor.py
```

### 5. Process city files

```bash
python process_city_files.py
```

### 6. Serve the frontend

```bash
python serve.py
# or
uvicorn serve:app --reload
```
Then open [http://localhost:8000/visu_2.html](http://localhost:8000/visu_2.html) in your browser.

---

## 🖥️ Frontend Usage

- **Step 1:** Upload the indicator structure JSON (scaffolding).
- **Step 2:** Select a state and city.  
  All available indicators for that city will be loaded and visualized.
- **Step 3:** Explore the collapsible indicator tree, with color-coded value badges.

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

*Painel do Clima: Bringing climate risk data