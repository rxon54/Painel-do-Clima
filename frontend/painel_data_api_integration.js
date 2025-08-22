// Integration example for using the new Data API with the existing frontend

/**
 * Enhanced indicator data fetcher using the new Data API
 * This replaces direct JSON file access with API calls for better performance and error handling
 */

class PainelDataAPI {
    constructor(baseUrl = 'http://localhost:8001') {
        this.baseUrl = baseUrl;
        this.cache = new Map(); // Client-side caching
    }

    /**
     * Get all indicators with optional filtering
     * @param {Object} options - Filtering options
     * @param {string} options.setor - Filter by sector
     * @param {string} options.nivel - Filter by level
     * @param {string} options.search - Search term
     * @param {number} options.limit - Maximum results (default: 100)
     * @param {number} options.offset - Pagination offset (default: 0)
     * @returns {Promise<Object>} List of indicators with metadata
     */
    async getAllIndicators(options = {}) {
        const {
            setor,
            nivel,
            search,
            limit = 100,
            offset = 0
        } = options;

        // Build query parameters
        const params = new URLSearchParams();
        if (setor) params.append('setor', setor);
        if (nivel) params.append('nivel', nivel);
        if (search) params.append('search', search);
        if (limit) params.append('limit', limit.toString());
        if (offset) params.append('offset', offset.toString());

        const cacheKey = `indicators_all_${params.toString()}`;
        
        // Check cache first
        if (this.cache.has(cacheKey)) {
            console.log(`Cache hit for indicators list: ${params.toString()}`);
            return this.cache.get(cacheKey);
        }

        try {
            const url = `${this.baseUrl}/api/v1/indicadores/estrutura?${params}`;
            const response = await fetch(url);

            if (!response.ok) {
                throw new Error(`API error: ${response.status} ${response.statusText}`);
            }

            const data = await response.json();
            
            // Cache successful responses
            this.cache.set(cacheKey, data);
            console.log(`Fetched ${data.indicators.length} indicators (total: ${data.total_count})`);
            
            return data;
            
        } catch (error) {
            console.error('Error fetching all indicators:', error);
            throw error;
        }
    }

    /**
     * Get indicator structure by ID with caching
     * @param {string} indicatorId - Numeric indicator ID
     * @returns {Promise<Object>} Indicator data structure
     */
    async getIndicatorStructure(indicatorId) {
        const cacheKey = `indicator_${indicatorId}`;
        
        // Check cache first
        if (this.cache.has(cacheKey)) {
            console.log(`Cache hit for indicator ${indicatorId}`);
            return this.cache.get(cacheKey);
        }

        try {
            const response = await fetch(
                `${this.baseUrl}/api/v1/indicadores/estrutura/${indicatorId}`
            );

            if (!response.ok) {
                if (response.status === 404) {
                    throw new Error(`Indicator ${indicatorId} not found`);
                }
                throw new Error(`API error: ${response.status} ${response.statusText}`);
            }

            const data = await response.json();
            
            // Cache successful responses
            this.cache.set(cacheKey, data);
            console.log(`Fetched indicator ${indicatorId}: ${data.nome}`);
            
            return data;
            
        } catch (error) {
            console.error(`Error fetching indicator ${indicatorId}:`, error);
            throw error;
        }
    }

    /**
     * Get total indicators count
     * @returns {Promise<Object>} Count information
     */
    async getIndicatorsCount() {
        try {
            const response = await fetch(`${this.baseUrl}/api/v1/indicadores/count`);
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            return await response.json();
        } catch (error) {
            console.error('Error fetching indicators count:', error);
            throw error;
        }
    }

    /**
     * Get available sectors
     * @returns {Promise<Object>} Sectors list
     */
    async getAvailableSectors() {
        const cacheKey = 'sectors';
        
        if (this.cache.has(cacheKey)) {
            return this.cache.get(cacheKey);
        }

        try {
            const response = await fetch(`${this.baseUrl}/api/v1/indicadores/setores`);
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            
            const data = await response.json();
            this.cache.set(cacheKey, data);
            
            return data;
        } catch (error) {
            console.error('Error fetching sectors:', error);
            throw error;
        }
    }

    /**
     * Check API health
     * @returns {Promise<Object>} Health status
     */
    async checkHealth() {
        try {
            const response = await fetch(`${this.baseUrl}/health`);
            return await response.json();
        } catch (error) {
            console.error('API health check failed:', error);
            return { status: 'unhealthy', error: error.message };
        }
    }

    /**
     * Batch fetch multiple indicators
     * @param {string[]} indicatorIds - Array of indicator IDs
     * @returns {Promise<Object[]>} Array of indicator data
     */
    async getMultipleIndicators(indicatorIds) {
        const promises = indicatorIds.map(id => 
            this.getIndicatorStructure(id).catch(error => ({
                id,
                error: error.message
            }))
        );

        return Promise.all(promises);
    }

    /**
     * Clear cache
     */
    clearCache() {
        this.cache.clear();
        console.log('API cache cleared');
    }
}

// Usage examples:

// Initialize API client
const painelAPI = new PainelDataAPI();

// Example 1: Enhanced indicator info display
async function showIndicatorDetails(indicatorId) {
    try {
        const indicator = await painelAPI.getIndicatorStructure(indicatorId);
        
        console.log(`=== ${indicator.nome} ===`);
        console.log(`Setor: ${indicator.setor_estrategico}`);
        console.log(`Nível: ${indicator.nivel}`);
        console.log(`Anos disponíveis: ${indicator.anos}`);
        console.log(`Descrição: ${indicator.descricao_simples}`);
        console.log(`URL dos dados: ${indicator.url_obtem_dados_indicador}`);
        
        return indicator;
    } catch (error) {
        console.error(`Failed to show indicator ${indicatorId}:`, error);
    }
}

// Example 2: Enhanced sector browser with filtering
async function initializeSectorBrowser() {
    try {
        // Get all indicators grouped by sector
        const allData = await painelAPI.getAllIndicators({ limit: 1000 });
        
        console.log(`Dashboard data loaded:`);
        console.log(`- ${allData.total_count} total indicators`);
        console.log(`- ${allData.sectors.length} sectors available`);
        
        // Group indicators by sector for navigation
        const sectorGroups = {};
        allData.indicators.forEach(indicator => {
            const sector = indicator.setor_estrategico;
            if (!sectorGroups[sector]) {
                sectorGroups[sector] = [];
            }
            sectorGroups[sector].push(indicator);
        });
        
        // Create sector navigation
        const nav = document.getElementById('sector-navigation');
        if (nav) {
            nav.innerHTML = '';
            Object.entries(sectorGroups).forEach(([sector, indicators]) => {
                const sectorBtn = document.createElement('button');
                sectorBtn.textContent = `${sector} (${indicators.length})`;
                sectorBtn.onclick = () => loadSectorIndicators(sector);
                nav.appendChild(sectorBtn);
            });
        }
        
        return sectorGroups;
    } catch (error) {
        console.error('Failed to initialize sector browser:', error);
    }
}

// Example 3: Search functionality
async function searchIndicators(searchTerm) {
    try {
        const results = await painelAPI.getAllIndicators({
            search: searchTerm,
            limit: 50
        });
        
        console.log(`Search "${searchTerm}": ${results.indicators.length} results`);
        
        // Update search results UI
        const resultsContainer = document.getElementById('search-results');
        if (resultsContainer) {
            resultsContainer.innerHTML = '';
            
            if (results.indicators.length === 0) {
                resultsContainer.innerHTML = `<p>Nenhum indicador encontrado para "${searchTerm}"</p>`;
                return;
            }
            
            results.indicators.forEach(indicator => {
                const item = document.createElement('div');
                item.className = 'search-result-item';
                item.innerHTML = `
                    <h4>${indicator.nome}</h4>
                    <p><strong>Setor:</strong> ${indicator.setor_estrategico}</p>
                    <p><strong>Nível:</strong> ${indicator.nivel}</p>
                    <p>${indicator.descricao_simples}</p>
                `;
                item.onclick = () => handleIndicatorClick(indicator.id, item);
                resultsContainer.appendChild(item);
            });
        }
        
        return results;
    } catch (error) {
        console.error('Search failed:', error);
    }
}

// Example 4: Paginated indicator browser
async function loadSectorIndicators(sector, page = 0, pageSize = 20) {
    try {
        const offset = page * pageSize;
        const results = await painelAPI.getAllIndicators({
            setor: sector,
            limit: pageSize,
            offset: offset
        });
        
        console.log(`Loaded ${sector} indicators (page ${page + 1})`);
        
        // Update indicator list
        const listContainer = document.getElementById('indicator-list');
        if (listContainer) {
            if (page === 0) listContainer.innerHTML = ''; // Clear on first page
            
            results.indicators.forEach(indicator => {
                const item = document.createElement('div');
                item.className = 'indicator-item';
                item.innerHTML = `
                    <div class="indicator-header">
                        <span class="indicator-name">${indicator.nome}</span>
                        <span class="indicator-level">Nível ${indicator.nivel}</span>
                    </div>
                    <p class="indicator-description">${indicator.descricao_simples}</p>
                `;
                item.onclick = () => handleIndicatorClick(indicator.id, item);
                listContainer.appendChild(item);
            });
            
            // Add pagination if needed
            const hasMore = offset + pageSize < results.total_count;
            if (hasMore) {
                const loadMoreBtn = document.createElement('button');
                loadMoreBtn.textContent = `Carregar mais (${results.total_count - offset - pageSize} restantes)`;
                loadMoreBtn.onclick = () => {
                    loadMoreBtn.remove();
                    loadSectorIndicators(sector, page + 1, pageSize);
                };
                listContainer.appendChild(loadMoreBtn);
            }
        }
        
        return results;
    } catch (error) {
        console.error(`Failed to load ${sector} indicators:`, error);
    }
}

// Example 2: Initialize dashboard with API stats
async function initializeDashboard() {
    try {
        // Check API health
        const health = await painelAPI.checkHealth();
        console.log('API Status:', health.status);
        
        if (health.status === 'healthy') {
            // Get basic stats
            const count = await painelAPI.getIndicatorsCount();
            const sectors = await painelAPI.getAvailableSectors();
            
            console.log(`Dashboard initialized:`);
            console.log(`- ${count.total_indicators} indicators available`);
            console.log(`- ${sectors.total_sectors} sectors: ${sectors.sectors.join(', ')}`);
            
            // Update UI elements
            document.getElementById('indicator-count').textContent = count.total_indicators;
            
            // Populate sector filter
            const sectorSelect = document.getElementById('sector-filter');
            if (sectorSelect) {
                sectors.sectors.forEach(sector => {
                    const option = document.createElement('option');
                    option.value = sector;
                    option.textContent = sector;
                    sectorSelect.appendChild(option);
                });
            }
        }
    } catch (error) {
        console.error('Dashboard initialization failed:', error);
    }
}

// Example 3: Enhanced tree node click handler
async function handleIndicatorClick(indicatorId, nodeElement) {
    try {
        // Show loading state
        nodeElement.classList.add('loading');
        
        // Fetch detailed data
        const indicator = await painelAPI.getIndicatorStructure(indicatorId);
        
        // Update node with additional info
        const infoPanel = document.getElementById('indicator-info');
        if (infoPanel) {
            infoPanel.innerHTML = `
                <h3>${indicator.nome}</h3>
                <p><strong>Setor:</strong> ${indicator.setor_estrategico}</p>
                <p><strong>Nível:</strong> ${indicator.nivel}</p>
                <p><strong>Anos:</strong> ${indicator.anos}</p>
                <p>${indicator.descricao_simples}</p>
                <div class="indicator-links">
                    <a href="${indicator.url_mostra_mapas_na_tela}" target="_blank">Ver Mapas</a>
                    <a href="${indicator.url_obtem_dados_indicador}" target="_blank">Obter Dados</a>
                </div>
            `;
        }
        
    } catch (error) {
        console.error('Error handling indicator click:', error);
        
        // Show error in info panel
        const infoPanel = document.getElementById('indicator-info');
        if (infoPanel) {
            infoPanel.innerHTML = `<p class="error">Erro ao carregar indicador: ${error.message}</p>`;
        }
    } finally {
        nodeElement.classList.remove('loading');
    }
}

// Example 4: Batch processing for performance
async function preloadCriticalIndicators() {
    const criticalIds = ['2', '8', '50001', '60000']; // Most commonly accessed
    
    console.log('Preloading critical indicators...');
    const results = await painelAPI.getMultipleIndicators(criticalIds);
    
    const successful = results.filter(r => !r.error);
    console.log(`Preloaded ${successful.length}/${criticalIds.length} indicators`);
}

// Example 5: Integration with existing paineldoclima.js
function enhancePainelDoClima() {
    // Override the existing showIndicatorDoc function to use the API
    if (window._testShowIndicatorDoc) {
        const originalShowIndicatorDoc = window._testShowIndicatorDoc;
        
        window._testShowIndicatorDoc = async function(indicatorId) {
            try {
                const indicator = await painelAPI.getIndicatorStructure(indicatorId);
                
                // Use the enhanced data for better documentation display
                return {
                    ...indicator,
                    // Parse JSON strings for better handling
                    years: JSON.parse(indicator.anos || '[]'),
                    scenarios: JSON.parse(indicator.cenarios || '[]')
                };
            } catch (error) {
                // Fallback to original function
                console.warn('API fallback for indicator', indicatorId);
                return originalShowIndicatorDoc(indicatorId);
            }
        };
    }
}

// Auto-initialization
document.addEventListener('DOMContentLoaded', () => {
    console.log('Painel Data API integration loaded');
    
    // Initialize dashboard
    initializeDashboard();
    
    // Enhance existing functionality
    enhancePainelDoClima();
    
    // Preload critical data
    preloadCriticalIndicators();
});

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { PainelDataAPI };
} else {
    window.PainelDataAPI = PainelDataAPI;
}
