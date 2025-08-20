# Frontend: Painel do Clima

This folder contains the web interface for the Painel do Clima project.

## Core Components

### Main Interface
- **`paineldoclima.html`** - Primary web interface with interactive climate data visualization
- **`paineldoclima.js`** - D3.js-powered interactive visualization logic
- **`paineldoclima.css`** - Styling for responsive and accessible design

### Data Structure
- **`ab_structure.json`** - Complete AdaptaBrasil indicator hierarchy (~9,000 indicators)
- **`indicators_doc.html`** - Documentation for available indicators

## Features
- **Interactive Hierarchical Browsing**: Sector → Level → Sub-indicator navigation
- **City Selection Interface**: Dynamic loading of city-specific climate data  
- **Color-Coded Value Badges**: Risk-based indicator visualization
- **Responsive Design**: Optimized for desktop and mobile devices
- **Real-Time Data Loading**: Connects to FastAPI backend for live data

## Architecture
- **D3.js v7**: Powers the hierarchical tree visualization
- **Native JavaScript**: Modern ES6+ for data handling and UI interactions
- **CSS Grid/Flexbox**: Responsive layout system
- **JSON-Based Communication**: RESTful API integration with backend

## Data Flow
1. Load indicator structure from `ab_structure.json`
2. Fetch city-specific data via backend API calls
3. Merge structure with values and render interactive tree
4. Update visualization based on user selections

## Development
The frontend is served by the FastAPI backend (`backend/serve.py`) and integrates seamlessly with the processed climate data pipeline.
