// visu_2.js - Main logic for Painel do Clima visualization

// Global variables for the visualization
let allData, hierarchyData;
// Function to build hierarchy from flat data
function buildHierarchy(data) {
    const sectors = {};
    const indicatorMap = {};

    // First, create a map of all indicators by ID
    data.forEach(indicator => {
        // Convert nivel to number for proper sorting
        const nivel = indicator.nivel ? parseInt(indicator.nivel) : 0;
        indicator.nivel_num = nivel;

        indicatorMap[indicator.id] = indicator;
        if (!sectors[indicator.setor_estrategico]) {
            sectors[indicator.setor_estrategico] = [];
        }
    });

    // Then build the hierarchy for each sector
    const sectorHierarchies = {};
    Object.keys(sectors).forEach(sector => {
        // Find root indicators (those with no parent or parent not in the same sector)
        const roots = data.filter(indicator =>
            indicator.setor_estrategico === sector &&
            (!indicator.indicador_pai ||
                !data.some(i => i.id === indicator.indicador_pai && i.setor_estrategico === sector))
        ).map(indicator => buildTree(indicator, data, sector));

        sectorHierarchies[sector] = roots.length > 0 ? roots : null;
    });

    // Get all unique levels
    const levels = new Set();
    data.forEach(indicator => {
        if (indicator.nivel) levels.add(indicator.nivel);
    });
    // Sort levels numerically
    const sortedLevels = Array.from(levels)
        .map(l => parseInt(l))
        .sort((a, b) => a - b)
        .map(l => l.toString());

    // Get all unique sectors for the filter
    const sectorList = Object.keys(sectors).sort();

    return {
        sectors: sectorList,
        hierarchy: sectorHierarchies,
        levels: sortedLevels
    };
}

// Recursive function to build the tree structure
function buildTree(rootIndicator, allIndicators, sector) {
    // Ensure parent_indicator is treated as empty string if missing/null
    const parentIndicator = rootIndicator.indicador_pai || "";

    const children = allIndicators.filter(child =>
        (child.indicador_pai || "") === rootIndicator.id &&
        child.setor_estrategico === sector
    ).map(child => buildTree(child, allIndicators, sector));

    // Sort children by nivel_num to maintain hierarchy order
    if (children.length > 0) {
        children.sort((a, b) => (a.nivel_num || 0) - (b.nivel_num || 0));
    }

    return {
        id: rootIndicator.id || "",
        nome: rootIndicator.nome || "",
        nivel: rootIndicator.nivel || "Unknown",
        nivel_num: rootIndicator.nivel_num || 0,
        sector: rootIndicator.setor_estrategico || "",
        descricao: rootIndicator.descricao_simples || rootIndicator.descricao || "",
        children: children.length > 0 ? children : null
    };
}

// Function to calculate the height needed for a subtree
function calculateTreeHeight(root, margin, minVerticalSpacing = 40) {
    // Calculate the maximum depth of the tree
    function getMaxDepth(node, depth = 0) {
        if (!node.children || node.children.length === 0) {
            return depth;
        }
        let maxChildDepth = 0;
        for (const child of node.children) {
            const childDepth = getMaxDepth(child, depth + 1);
            if (childDepth > maxChildDepth) {
                maxChildDepth = childDepth;
            }
        }
        return maxChildDepth;
    }

    const maxDepth = getMaxDepth(root);
    // Use minVerticalSpacing per level
    return (maxDepth + 1) * minVerticalSpacing + margin.top + margin.bottom;
}

// Function to render a single subtree
function renderSubtree(container, root, sector, rootIndex) {
    // Vertical tree: root at top, children below
    const margin = {top: 40, right: 40, bottom: 40, left: 200};
    const verticalSpacing = 60; // More space between levels vertically
    const horizontalSpacing = 180; // Space between siblings
    // Create a group for this tree with proper margins
    const svgGroup = container.append("g")
        .attr("transform", `translate(${margin.left},${margin.top})`);

    // Create the tree layout (vertical)
    const treeLayout = d3.tree()
        .nodeSize([horizontalSpacing, verticalSpacing]); // [x, y]: x is horizontal, y is vertical

    // Create a hierarchy from our root
    const hierarchyData = d3.hierarchy(root);
    const treeData = treeLayout(hierarchyData);

    // Draw links (lines connecting nodes)
    svgGroup.selectAll(".link")
        .data(treeData.links())
        .enter().append("path")
        .attr("class", "link")
        .attr("d", d3.linkVertical()
            .x(d => d.x)
            .y(d => d.y));

    // Create a group for each node
    const nodes = svgGroup.selectAll(".node")
        .data(treeData.descendants())
        .enter().append("g")
        .attr("class", "node")
        .attr("transform", d => `translate(${d.x},${d.y})`)
        .attr("data-id", d => d.data.id);

    // Add circles for the nodes
    nodes.append("circle")
        .attr("r", 10)
        .attr("class", d => `level-${d.data.nivel || 'unknown'}`);

    // Add labels to the nodes (right of node)
    nodes.append("text")
        .attr("dy", ".35em")
        .attr("x", 16)
        .style("text-anchor", "start")
        .text(d => `${d.data.id}: ${d.data.nome}`)
        .on("click", function(event, d) {
            // Toggle children visibility
            const node = d3.select(this.parentNode);
            if (d.children) {
                node.classed("collapsed", !node.classed("collapsed"));
                // Find all descendants and toggle their display
                const descendants = treeData.descendants().filter(n =>
                    d.data.id && n.data.id && isDescendant(d, n));
                descendants.forEach(desc => {
                    d3.selectAll(`.node[data-id="${desc.data.id}"]`)
                        .style("display", node.classed("collapsed") ? "none" : null);
                });
            }
        });

    // Helper function to check if one node is a descendant of another
    function isDescendant(ancestor, node) {
        if (!node.parent || !node.parent.data) return false;
        if (node.parent.data.id === ancestor.data.id) return true;
        return isDescendant(ancestor, node.parent);
    }

    // Add tooltip or more details on hover
    nodes.on("mouseover", function(event, d) {
        d3.select(".tooltip").remove(); // Remove any existing tooltip

        const tooltip = d3.select("body").append("div")
            .attr("class", "tooltip")
            .style("left", (event.pageX + 10) + "px")
            .style("top", (event.pageY - 28) + "px");

        let content = `
            <strong>ID:</strong> ${d.data.id}<br/>
            <strong>Nome:</strong> ${d.data.nome}<br/>
            <strong>Nível:</strong> ${d.data.nivel}<br/>
            <strong>Setor:</strong> ${d.data.sector}<br/>
        `;

        if (d.parent && d.parent.data && d.parent.data.id) {
            content += `<strong>Indicador Pai:</strong> ${d.parent.data.id}: ${d.parent.data.nome}<br/>`;
        }

        if (d.data.descricao) {
            content += `<strong>Descrição:</strong> ${d.data.descricao}`;
        }

        tooltip.html(content);
    })
    .on("mouseout", function() {
        d3.select(".tooltip").remove();
    });

    // --- Responsive SVG: set viewBox and dynamic height/width ---
    setTimeout(() => {
        try {
            const nodeElements = container.node().querySelectorAll('.node');
            let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
            nodeElements.forEach(el => {
                const transform = el.getAttribute('transform');
                if (transform) {
                    // Now using translate(x, y): x is horizontal, y is vertical
                    const match = /translate\\(([-\\d.]+),([-.\\d]+)\\)/.exec(transform);
                    if (match) {
                        const x = parseFloat(match[1]); // horizontal
                        const y = parseFloat(match[2]); // vertical
                        if (x < minX) minX = x;
                        if (x > maxX) maxX = x;
                        if (y < minY) minY = y;
                        if (y > maxY) maxY = y;
                    }
                }
            });
            // Calculate width/height including margins
            const width = (maxX - minX) + margin.left + margin.right;
            const height = (maxY - minY) + margin.top + margin.bottom;
            // Move the group so the tree is always visible
            container.select('g')
                .attr('transform', `translate(${-minX + margin.left},${-minY + margin.top})`);
            container
                .attr("viewBox", `0 0 ${width} ${height}`)
                .attr("width", "100%")
                .attr("height", height > 0 ? height : 400);
        } catch (e) {
            // fallback: do nothing
        }
    }, 0);
}

// Function to check if one node is a descendant of another
function isDescendant(ancestor, node) {
    if (!node.parent || !node.parent.data) return false;
    if (node.parent.data.id === ancestor.data.id) return true;
    return isDescendant(ancestor, node.parent);
}

// --- Collapsible Indented List ---
// --- Indicator Documentation Overlay Logic ---
let docHtmlLoaded = false;
let docHtmlContent = '';

// Load indicators_doc.html only once
async function showIndicatorDoc(indicatorId) {
    ensureDocOverlay();
    const overlay = document.getElementById('doc-overlay');
    const content = document.getElementById('doc-overlay-content');
    async function tryFetchDoc(paths) {
        for (const path of paths) {
            try {
                const resp = await fetch(path, {cache: 'reload'});
                if (resp.ok) return await resp.text();
            } catch (e) {}
        }
        throw new Error('Não foi possível carregar a documentação.');
    }
    if (!window.docHtmlLoaded) {
        try {
            window.docHtmlContent = await tryFetchDoc([
                'indicators_doc.html',
                'frontend/indicators_doc.html',
                'backend/indicators_doc.html'
            ]);
            window.docHtmlLoaded = true;
        } catch (e) {
            content.innerHTML = '<div style="color:red">Erro ao carregar documentação.</div>';
            overlay.style.visibility = 'visible';
            overlay.style.opacity = '1';
            return;
        }
    }
    content.innerHTML = window.docHtmlContent;
    setTimeout(() => {
        const section = content.querySelector(`#indicator${indicatorId}`);
        if (section) {
            section.scrollIntoView({behavior: 'auto', block: 'center'});
            section.style.background = '#ffe';
            setTimeout(() => { section.style.background = ''; }, 1200);
        }
    }, 50);
    overlay.style.visibility = 'visible';
    overlay.style.opacity = '1';
    function escListener(ev) {
        if (ev.key === 'Escape') {
            overlay.style.opacity = '0';
            setTimeout(() => { overlay.style.visibility = 'hidden'; }, 200);
            document.removeEventListener('keydown', escListener);
        }
    }
    document.addEventListener('keydown', escListener);
}

// --- DEBUG: Add global click test ---
window._testShowIndicatorDoc = showIndicatorDoc;

// --- Collapsible Indented List ---
function renderIndentedList(container, root) {
    // Recursive function to build the list
    function buildList(node) {
        const li = document.createElement('li');
        li.className = 'indented-node';
        // --- GRID ROW ---
        const row = document.createElement('span');
        row.className = 'indicator-row-grid';
        // Tree label (with toggle if needed)
        const labelCell = document.createElement('span');
        labelCell.className = 'tree-label-cell';
        // Node label
        const label = document.createElement('span');
        label.className = 'indented-label';
        // --- Make ID clickable ---
        const idSpan = document.createElement('span');
        idSpan.className = 'indicator-id-link';
        idSpan.textContent = node.id;
        idSpan.title = 'Ver documentação do indicador';
        idSpan.style.cursor = 'pointer';
        // FIX: Call showIndicatorDoc directly, not via global
        idSpan.addEventListener('click', function(e) {
            e.stopPropagation();
            showIndicatorDoc(node.id);
        });
        label.innerHTML = '';
        label.appendChild(idSpan);
        label.appendChild(document.createTextNode(`: ${node.nome}`));
        label.title = (node.descricao ? node.descricao + '\n' : '') + `Nível: ${node.nivel}\nSetor: ${node.sector}`;
        labelCell.appendChild(label);
        // Value cells
        const valueSpanPresent = document.createElement('span');
        valueSpanPresent.className = 'indicator-value indicator-value-present';
        valueSpanPresent.setAttribute('data-indicator-id', node.id);
        valueSpanPresent.setAttribute('data-indicator-year', 'present');
        // 2030
        const valueSpan2030 = document.createElement('span');
        valueSpan2030.className = 'indicator-value indicator-value-2030';
        valueSpan2030.setAttribute('data-indicator-id', node.id);
        valueSpan2030.setAttribute('data-indicator-year', '2030');
        // 2050
        const valueSpan2050 = document.createElement('span');
        valueSpan2050.className = 'indicator-value indicator-value-2050';
        valueSpan2050.setAttribute('data-indicator-id', node.id);
        valueSpan2050.setAttribute('data-indicator-year', '2050');
        // Add toggle if needed
        let ul = null;
        if (node.children && node.children.length > 0) {
            const toggle = document.createElement('span');
            toggle.className = 'toggle';
            toggle.textContent = '▼';
            toggle.style.cursor = 'pointer';
            toggle.style.marginRight = '6px';
            let expanded = true;
            ul = document.createElement('ul');
            ul.className = 'indented-list';
            node.children.forEach(child => {
                ul.appendChild(buildList(child));
            });
            toggle.onclick = function() {
                expanded = !expanded;
                ul.style.display = expanded ? '' : 'none';
                toggle.textContent = expanded ? '▼' : '►';
            };
            labelCell.insertBefore(toggle, labelCell.firstChild);
        }
        // Assemble row
        row.appendChild(labelCell);
        row.appendChild(valueSpanPresent);
        row.appendChild(valueSpan2030);
        row.appendChild(valueSpan2050);
        li.appendChild(row);
        if (ul) li.appendChild(ul);
        return li;
    }
    // Start with a <ul>
    const ul = document.createElement('ul');
    ul.className = 'indented-list';
    ul.appendChild(buildList(root));
    container.node().appendChild(ul);
}

// --- Update indicator values in the indented list ---
function updateIndicatorValues(data) {
    data.forEach(record => {
        // Present value
        const elPresent = document.querySelector(`.indicator-value-present[data-indicator-id='${record.indicator_id}']`);
        if (elPresent) {
            elPresent.textContent = `${record.value} ${record.rangelabel || record.valuelabel || ''}`;
            elPresent.style.background = record.valuecolor || '#eee';
            elPresent.style.color = '#222';
        }
        // 2030 value (future trends)
        const el2030 = document.querySelector(`.indicator-value-2030[data-indicator-id='${record.indicator_id}']`);
        if (el2030) {
            if (record.future_trends && record.future_trends["2030"]) {
                const ft = record.future_trends["2030"];
                el2030.textContent = `${ft.value}` + (ft.valuelabel ? ` ${ft.valuelabel}` : '');
                el2030.style.background = ft.valuecolor || '#eee';
                el2030.style.color = '#222';
            } else {
                el2030.textContent = '';
                el2030.style.background = '#eee';
                el2030.style.color = '#aaa';
            }
        }
        // 2050 value (future trends)
        const el2050 = document.querySelector(`.indicator-value-2050[data-indicator-id='${record.indicator_id}']`);
        if (el2050) {
            if (record.future_trends && record.future_trends["2050"]) {
                const ft = record.future_trends["2050"];
                el2050.textContent = `${ft.value}` + (ft.valuelabel ? ` ${ft.valuelabel}` : '');
                el2050.style.background = ft.valuecolor || '#eee';
                el2050.style.color = '#222';
            } else {
                el2050.textContent = '';
                el2050.style.background = '#eee';
                el2050.style.color = '#aaa';
            }
        }
    });
}

// Function to render the hierarchy
function renderHierarchy(hierarchyData) {
    const visualization = d3.select("#visualization");
    visualization.html(""); // Clear previous content

    // Populate sector filter (now multi-select)
    const sectorFilter = d3.select("#sector-filter")
        .attr("multiple", true)
        .attr("size", Math.min(8, hierarchyData.sectors.length + 1));
    sectorFilter.selectAll("option").remove();
    sectorFilter.append("option")
        .attr("value", "all")
        .text("Todos os Setores");
    hierarchyData.sectors.forEach(sector => {
        sectorFilter.append("option")
            .attr("value", sector)
            .text(sector);
    });

    // Populate level filter
    const levelFilter = d3.select("#level-filter");
    levelFilter.selectAll("option:not(:first-child)").remove();
    hierarchyData.levels.forEach(level => {
        levelFilter.append("option")
            .attr("value", level)
            .text(`Nível ${level}`);
    });

    // Add event listeners for buttons
    d3.select("#collapse-all").on("click", () => {
        // Collapse all: set all toggles to collapsed
        document.querySelectorAll('.toggle').forEach(toggle => {
            if (toggle.textContent === '▼') toggle.click();
        });
    });

    d3.select("#expand-all").on("click", () => {
        // Expand all: set all toggles to expanded
        document.querySelectorAll('.toggle').forEach(toggle => {
            if (toggle.textContent === '►') toggle.click();
        });
    });

    // Render each sector's hierarchy
    hierarchyData.sectors.forEach(sector => {
        const sectorDiv = visualization.append("div")
            .attr("class", "sector")
            .attr("id", `sector-${sector.replace(/\s+/g, '-')}`);

        sectorDiv.append("div")
            .attr("class", "sector-title")
            .text(sector);

        const roots = hierarchyData.hierarchy[sector];
        if (roots && roots.length > 0) {
            // If there are Level 2 roots, show them side by side
            const level2Roots = roots.filter(r => r.nivel === '2' || r.nivel === 2);
            const otherRoots = roots.filter(r => !(r.nivel === '2' || r.nivel === 2));
            if (level2Roots.length > 0) {
                const flexRow = sectorDiv.append('div')
                    .attr('class', 'level2-flex-row')
                    .style('display', 'flex')
                    .style('flex-wrap', 'wrap');
                level2Roots.forEach((root, rootIndex) => {
                    const rootContainer = flexRow.append('div')
                        .attr('class', 'root-container level2-flex-item level2-container')
                        .style('margin-bottom', '0')
                        .style('flex-basis', '45%')
                        .style('max-width', '45%');
                    // Add root title
                    const rootTitleRow = rootContainer.append('div')
                        .attr('class', 'root-title-row')
                        .style('display', 'flex')
                        .style('justify-content', 'space-between')
                        .style('align-items', 'center');
                    rootTitleRow.append('div')
                        .attr('class', 'root-title')
                        .text(`${root.id}: ${root.nome} (Nível ${root.nivel})`);
                    // Add indicator year headers
                    rootTitleRow.append('div')
                        .attr('class', 'indicator-years-header')
                        .style('display', 'flex')
                        .style('gap', '30px') // Match the gap used in .indicator-values-multi
                        .style('min-width', '270px')
                        .selectAll('span')
                        .data(['Presente', '2030', '2050'])
                        .enter()
                        .append('span')
                        .style('font-weight', 'bold')
                        .style('color', '#444')
                        .style('text-align', 'center')
                        .style('min-width', '70px')
                        .text(d => d);
                    renderIndentedList(rootContainer, root);
                });
            }
            // Show other roots (not Level 2) as normal blocks
            otherRoots.forEach((root, rootIndex) => {
                const rootContainer = sectorDiv.append('div')
                    .attr("class", "root-container")
                    .style("margin-bottom", "40px");
                rootContainer.append("div")
                    .attr("class", "root-title")
                    .text(`${root.id}: ${root.nome} (Nível ${root.nivel})`);
                renderIndentedList(rootContainer, root);
            });
        } else {
            sectorDiv.append("p").text("Nenhum indicador neste setor.");
        }
    });

    // Add event listeners for filters
    sectorFilter.on("change", function() {
        const selected = Array.from(this.selectedOptions).map(opt => opt.value);
        d3.selectAll(".sector").style("display", null);
        if (!selected.includes("all")) {
            d3.selectAll(".sector").style("display", "none");
            selected.forEach(sector => {
                d3.select(`#sector-${sector.replace(/\s+/g, '-')}`).style("display", null);
            });
        }
    });

    levelFilter.on("change", function() {
        const selectedLevel = this.value;
        if (selectedLevel === "all") {
            d3.selectAll(".node").style("display", null);
        } else {
            d3.selectAll(".node").style("display", function() {
                const nodeData = d3.select(this).datum();
                return (nodeData.data.nivel === selectedLevel) ? null : "none";
            });
        }
    });
}

// Function to load and process JSON data
function loadJsonData(jsonData) {
    // Check if data is already in the correct format
    if (Array.isArray(jsonData)) {
        // Map through the data to ensure consistent property names and formats
        const processedData = jsonData.map(item => ({
            id: item.id || "",
            nome: item.nome || item.name || "",
            nivel: item.nivel || item.level || "Unknown",
            setor_estrategico: item.setor_estrategico || item.setor || item.sector || "Unknown",
            indicador_pai: item.indicador_pai || item.parent_indicator || item.parent || "",
            descricao: item.descricao_simples || item.descricao || "",
            nivel_num: item.nivel ? parseInt(item.nivel) : 0
        }));

        const hierarchyData = buildHierarchy(processedData);
        renderHierarchy(hierarchyData);
    } else {
        console.error("Invalid JSON data format");
        alert("Formato de dados inválido. Certifique-se de que o arquivo JSON contém uma matriz de indicadores.");
    }
}

// --- City and L2 selection logic ---
let cityFileList = {};
let stateCityMap = {};
let selectedState = null;
let selectedCity = null;

async function loadCityFileList() {
    try {
        const resp = await fetch('data/city_filelist.json');
        if (!resp.ok) throw new Error('city_filelist.json não encontrado');
        cityFileList = await resp.json();
        // Build stateCityMap: {state: {cityId: {name, ...}}}
        stateCityMap = {};
        Object.entries(cityFileList).forEach(([cityId, info]) => {
            if (!info.state) return;
            if (!stateCityMap[info.state]) stateCityMap[info.state] = {};
            stateCityMap[info.state][cityId] = info;
        });
        populateStateDropdown();
    } catch (e) {
        alert('Erro ao carregar city_filelist.json: ' + e);
    }
}

function populateStateDropdown() {
    const stateSelect = document.getElementById('state-select');
    stateSelect.innerHTML = '<option value="">Selecione o estado...</option>';
    Object.keys(stateCityMap).sort().forEach(state => {
        const opt = document.createElement('option');
        opt.value = state;
        opt.textContent = state;
        stateSelect.appendChild(opt);
    });
    populateCityDropdown();
}

function populateCityDropdown() {
    const citySelect = document.getElementById('city-select');
    citySelect.innerHTML = '<option value="">Selecione uma cidade...</option>';
    if (!selectedState || !stateCityMap[selectedState]) return;
    Object.entries(stateCityMap[selectedState]).forEach(([cityId, info]) => {
        const opt = document.createElement('option');
        opt.value = cityId;
        opt.textContent = info.name || cityId;
        citySelect.appendChild(opt);
    });
}

document.getElementById('state-select').addEventListener('change', function(e) {
    selectedState = e.target.value;
    selectedCity = null;
    populateCityDropdown();
});

document.getElementById('city-select').addEventListener('change', async function(e) {
    selectedCity = e.target.value;
    if (!selectedState || !selectedCity || !stateCityMap[selectedState][selectedCity]) return;
    // Load all indicators for this city
    try {
        const cityInfo = stateCityMap[selectedState][selectedCity];
        // Assume cityInfo.file points to the city file (e.g., PR/city_<city_code>.json)
        const resp = await fetch(`data/${cityInfo.file}`);
        if (!resp.ok) throw new Error('Arquivo da cidade não encontrado');
        const cityData = await resp.json();
        // cityData.indicators is an array of indicator records
        updateIndicatorValues(cityData.indicators || []);
        document.getElementById('file-info').textContent = `Arquivo carregado: ${cityInfo.file}`;
    } catch (err) {
        alert('Erro ao carregar arquivo da cidade: ' + err);
    }
});

// --- Structure file logic ---
let structureLoaded = false;
let structureData = null;

// On structure file upload, build the hierarchy
document.getElementById("json-file").addEventListener("change", function(event) {
    const file = event.target.files[0];
    if (!file) return;
    document.getElementById("file-info").textContent = `Arquivo selecionado: ${file.name}`;
    const reader = new FileReader();
    reader.onload = function(e) {
        try {
            const jsonData = JSON.parse(e.target.result);
            structureData = jsonData;
            structureLoaded = true;
            loadJsonData(jsonData); // Build the tree
        } catch (error) {
            console.error("Erro ao analisar o arquivo JSON:", error);
            alert("Erro ao analisar o arquivo JSON. Por favor, verifique o formato do arquivo.");
        }
    };
    reader.readAsText(file);
});

// --- Auto-load structure file from ab_structure.json (hardcoded) ---
document.addEventListener('DOMContentLoaded', function() {
    // Try to auto-load ab_structure.json from the root directory
    fetch('ab_structure.json')
        .then(resp => {
            if (!resp.ok) throw new Error('ab_structure.json não encontrado');
            return resp.json();
        })
        .then(jsonData => {
            structureData = jsonData;
            structureLoaded = true;
            loadJsonData(jsonData);
            // Hide the manual upload UI
            const uploadDiv = document.getElementById('json-file').parentElement;
            if (uploadDiv) uploadDiv.style.display = 'none';
        })
        .catch(err => {
            // If any error, show the upload UI and log error
            const uploadDiv = document.getElementById('json-file').parentElement;
            if (uploadDiv) uploadDiv.style.display = '';
            console.error('Erro ao carregar ab_structure.json automaticamente:', err);
        });
});

// Load city_filelist.json on startup
document.addEventListener('DOMContentLoaded', loadCityFileList);

// Reload city list button
const reloadBtn = document.getElementById("reload-city-list");
if (reloadBtn) reloadBtn.addEventListener("click", populateCityDropdown);

// Populate on load
document.addEventListener("DOMContentLoaded", populateCityDropdown);

// Event listener for file upload
document.addEventListener("DOMContentLoaded", function() {
    const fileInput = document.getElementById("json-file");
    const fileInfo = document.getElementById("file-info");

    fileInput.addEventListener("change", function(event) {
        const file = event.target.files[0];
        if (!file) return;

        fileInfo.textContent = `Arquivo selecionado: ${file.name}`;

        const reader = new FileReader();
        reader.onload = function(e) {
            try {
                const jsonData = JSON.parse(e.target.result);
                structureData = jsonData;
                structureLoaded = true;
                loadJsonData(jsonData);
            } catch (error) {
                console.error("Erro ao analisar o arquivo JSON:", error);
                alert("Erro ao analisar o arquivo JSON. Por favor, verifique o formato do arquivo.");
            }
        };
        reader.readAsText(file);
    });
});

// Function to collapse all nodes in a tree
function collapseAllNodes() {
    d3.selectAll(".node").each(function(d) {
        if (d.children) {
            d._children = d.children;
            d.children = null;
        }
    });
    d3.selectAll(".node").style("display", function(d) {
        return d.depth === 0 ? null : "none";
    });
}

// Function to expand all nodes in a tree
function expandAllNodes() {
    d3.selectAll(".node").each(function(d) {
        if (d._children) {
            d.children = d._children;
            d._children = null;
        }
    });
    d3.selectAll(".node").style("display", null);
}

// --- Overlay for indicator documentation ---
// Create overlay and style if not present
function ensureDocOverlay() {
    let overlay = document.getElementById('doc-overlay');
    if (!overlay) {
        overlay = document.createElement('div');
        overlay.id = 'doc-overlay';
        overlay.style.position = 'fixed';
        overlay.style.top = '0';
        overlay.style.left = '0';
        overlay.style.width = '100vw';
        overlay.style.height = '100vh';
        overlay.style.background = 'rgba(0,0,0,0.55)';
        overlay.style.display = 'flex';
        overlay.style.alignItems = 'center';
        overlay.style.justifyContent = 'center';
        overlay.style.zIndex = '9999';
        overlay.style.visibility = 'hidden';
        overlay.style.opacity = '0';
        overlay.style.transition = 'opacity 0.2s';
        // Container for doc
        const container = document.createElement('div');
        container.id = 'doc-overlay-container';
        container.style.background = '#fff';
        container.style.borderRadius = '12px';
        container.style.boxShadow = '0 4px 32px rgba(0,0,0,0.25)';
        container.style.maxWidth = '900px';
        container.style.width = '90vw';
        container.style.maxHeight = '80vh';
        container.style.overflow = 'auto';
        container.style.position = 'relative';
        container.style.padding = '32px 24px 24px 24px';
        // Close button
        const closeBtn = document.createElement('button');
        closeBtn.textContent = '×';
        closeBtn.title = 'Fechar';
        closeBtn.style.position = 'absolute';
        closeBtn.style.top = '12px';
        closeBtn.style.right = '18px';
        closeBtn.style.fontSize = '2rem';
        closeBtn.style.background = 'none';
        closeBtn.style.border = 'none';
        closeBtn.style.cursor = 'pointer';
        closeBtn.style.color = '#444';
        closeBtn.style.zIndex = '10';
        closeBtn.onclick = function() {
            overlay.style.opacity = '0';
            setTimeout(() => { overlay.style.visibility = 'hidden'; }, 200);
        };
        container.appendChild(closeBtn);
        // Content area
        const content = document.createElement('div');
        content.id = 'doc-overlay-content';
        content.style.overflowY = 'auto';
        content.style.maxHeight = '70vh';
        container.appendChild(content);
        overlay.appendChild(container);
        overlay.addEventListener('click', function(e) {
            if (e.target === overlay) closeBtn.onclick();
        });
        document.body.appendChild(overlay);
    }
}

// Only one global for docHtmlLoaded/content
if (typeof window.docHtmlLoaded === 'undefined') window.docHtmlLoaded = false;
if (typeof window.docHtmlContent === 'undefined') window.docHtmlContent = '';

// Main function to show indicator documentation overlay
async function showIndicatorDoc(indicatorId) {
    ensureDocOverlay();
    const overlay = document.getElementById('doc-overlay');
    const content = document.getElementById('doc-overlay-content');
    async function tryFetchDoc(paths) {
        for (const path of paths) {
            try {
                const resp = await fetch(path, {cache: 'reload'});
                if (resp.ok) return await resp.text();
            } catch (e) {}
        }
        throw new Error('Não foi possível carregar a documentação.');
    }
    if (!window.docHtmlLoaded) {
        try {
            window.docHtmlContent = await tryFetchDoc([
                'indicators_doc.html',
                'frontend/indicators_doc.html',
                'backend/indicators_doc.html'
            ]);
            window.docHtmlLoaded = true;
        } catch (e) {
            content.innerHTML = '<div style="color:red">Erro ao carregar documentação.</div>';
            overlay.style.visibility = 'visible';
            overlay.style.opacity = '1';
            return;
        }
    }
    content.innerHTML = window.docHtmlContent;
    setTimeout(() => {
        const section = content.querySelector(`#indicator${indicatorId}`);
        if (section) {
            section.scrollIntoView({behavior: 'auto', block: 'center'});
            section.style.background = '#ffe';
            setTimeout(() => { section.style.background = ''; }, 1200);
        }
    }, 50);
    overlay.style.visibility = 'visible';
    overlay.style.opacity = '1';
    function escListener(ev) {
        if (ev.key === 'Escape') {
            overlay.style.opacity = '0';
            setTimeout(() => { overlay.style.visibility = 'hidden'; }, 200);
            document.removeEventListener('keydown', escListener);
        }
    }
    document.addEventListener('keydown', escListener);
}

// --- DEBUG: Add global click test ---
window._testShowIndicatorDoc = showIndicatorDoc;