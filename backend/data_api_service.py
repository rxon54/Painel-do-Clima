#!/usr/bin/env python3
"""
Painel do Clima Data API Service

A FastAPI service that provides access to climate indicator data from AdaptaBrasil API structure.
Serves filtered climate indicators with efficient caching and proper error handling.
"""

import json
import logging
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List
from functools import lru_cache

import uvicorn
from fastapi import FastAPI, HTTPException, Path as PathParam, Query, Request, status, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load configuration
def load_config() -> Dict[str, Any]:
    """Load configuration from config.yaml"""
    config_path = Path(__file__).parent.parent / "config.yaml"
    try:
        with open(config_path, 'r', encoding='utf-8') as file:
            config = yaml.safe_load(file)
        logger.info(f"Configuration loaded from {config_path}")
        return config
    except Exception as e:
        logger.warning(f"Could not load config.yaml: {e}")
        return {}

# Global configuration
_config = load_config()

# Authentication configuration
class AuthConfig:
    """Authentication configuration class"""
    def __init__(self, config: Dict[str, Any]):
        api_security = config.get('api_security', {})
        self.enabled = api_security.get('enabled', False)
        self.valid_keys = set(api_security.get('keys', {}).values()) if self.enabled else set()
        self.public_endpoints = set(api_security.get('public_endpoints', []))
        
        if self.enabled:
            logger.info(f"API Security enabled with {len(self.valid_keys)} keys")
            logger.info(f"Public endpoints: {', '.join(self.public_endpoints)}")
        else:
            logger.info("API Security disabled")

auth_config = AuthConfig(_config)

# Authentication dependency
async def verify_api_key(
    request: Request,
    x_api_key: Optional[str] = Header(None, alias="X-API-Key")
) -> bool:
    """
    Verify API key from X-API-Key header.
    
    Args:
        request: FastAPI request object
        x_api_key: API key from X-API-Key header
        
    Returns:
        bool: True if authenticated or endpoint is public
        
    Raises:
        HTTPException: 401 if authentication required but invalid/missing key
    """
    # Skip authentication if disabled
    if not auth_config.enabled:
        return True
        
    # Allow public endpoints
    if request.url.path in auth_config.public_endpoints:
        return True
        
    # Check API key
    if not x_api_key:
        logger.warning(f"Missing API key for {request.url.path} from {request.client.host if request.client else 'unknown'}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required. Include X-API-Key header.",
            headers={"WWW-Authenticate": "ApiKey"}
        )
        
    if x_api_key not in auth_config.valid_keys:
        logger.warning(f"Invalid API key attempted for {request.url.path} from {request.client.host if request.client else 'unknown'}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "ApiKey"}
        )
        
    # Log successful authentication (without exposing the key)
    logger.debug(f"Valid API key used for {request.url.path}")
    return True

# Response models for OpenAPI documentation
class IndicatorResponse(BaseModel):
    """Climate indicator data response model"""
    id: str = Field(description="Unique indicator identifier")
    nome: str = Field(description="Indicator name in Portuguese")
    url_mostra_mapas_na_tela: str = Field(description="URL to display maps")
    url_obtem_dados_indicador: str = Field(description="URL to obtain indicator data")
    descricao_simples: str = Field(description="Simple description")
    descricao_completa: str = Field(description="Complete description with methodology")
    nivel: str = Field(description="Indicator hierarchy level")
    proporcao_direta: str = Field(description="Direct proportion flag")
    indicador_pai: str = Field(description="Parent indicator ID")
    anos: str = Field(description="Available years as JSON array string")
    setor_estrategico: str = Field(description="Strategic sector")
    tipo_geometria: str = Field(description="Geometry type")
    unidade_medida: str = Field(description="Unit of measurement")
    cenarios: str = Field(description="Available scenarios as JSON array string")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "2",
                "nome": "Risco de estresse hídrico",
                "url_mostra_mapas_na_tela": "https://sistema.adaptabrasil.mcti.gov.br/2/1/2020/null/BR/municipio/adaptabrasil",
                "url_obtem_dados_indicador": "https://sistema.adaptabrasil.mcti.gov.br/api/mapa-dados/BR/municipio/2/2020/null/adaptabrasil",
                "descricao_simples": "Risco de impacto das mudanças climáticas no balanço hídrico dos sistemas socioecológicos",
                "nivel": "2",
                "setor_estrategico": "Recursos Hídricos",
                "anos": "[2020, 2030, 2050]"
            }
        }

class IndicatorListResponse(BaseModel):
    """Response model for list of indicators"""
    indicators: list[IndicatorResponse] = Field(description="List of climate indicators")
    total_count: int = Field(description="Total number of indicators")
    sectors: list[str] = Field(description="Available sectors")
    
    class Config:
        json_schema_extra = {
            "example": {
                "indicators": [
                    {
                        "id": "2",
                        "nome": "Risco de estresse hídrico",
                        "setor_estrategico": "Recursos Hídricos",
                        "nivel": "2"
                    }
                ],
                "total_count": 378,
                "sectors": ["Recursos Hídricos", "Saúde", "Segurança Alimentar"]
            }
        }

class IndicatorValue(BaseModel):
    """Individual indicator data value for a specific year"""
    year: int = Field(description="Year of the data point")
    value: float = Field(description="Indicator value")
    valuecolor: str = Field(description="Color code for visualization")
    rangelabel: str = Field(description="Human-readable range description")
    
    class Config:
        json_schema_extra = {
            "example": {
                "year": 2020,
                "value": 3.5,
                "valuecolor": "#ff6b6b",
                "rangelabel": "Alto risco"
            }
        }

class FutureTrend(BaseModel):
    """Future trend projection data"""
    year: int = Field(description="Future projection year (2030 or 2050)")
    scenario: str = Field(description="Climate scenario (RCP4.5, RCP8.5)")
    value: float = Field(description="Projected value")
    valuecolor: str = Field(description="Color code for projected value")
    rangelabel: str = Field(description="Range description for projection")
    
    class Config:
        json_schema_extra = {
            "example": {
                "year": 2030,
                "scenario": "RCP4.5",
                "value": 4.2,
                "valuecolor": "#ff4444",
                "rangelabel": "Risco muito alto"
            }
        }

class IndicatorDataResponse(BaseModel):
    """Climate indicator actual data values response"""
    geocod_ibge: str = Field(description="IBGE code of the municipality")
    city_name: str = Field(description="Municipality name")
    state: str = Field(description="State abbreviation")
    indicator_id: str = Field(description="Climate indicator ID")
    indicator_name: str = Field(description="Climate indicator name")
    present_data: List[IndicatorValue] = Field(description="Current/present data points")
    future_trends: List[FutureTrend] = Field(description="Future projection data")
    
    class Config:
        json_schema_extra = {
            "example": {
                "geocod_ibge": "4106902",
                "city_name": "Curitiba",
                "state": "PR",
                "indicator_id": "2",
                "indicator_name": "Risco de estresse hídrico",
                "present_data": [
                    {
                        "year": 2020,
                        "value": 3.5,
                        "valuecolor": "#ff6b6b",
                        "rangelabel": "Alto risco"
                    }
                ],
                "future_trends": [
                    {
                        "year": 2030,
                        "scenario": "RCP4.5",
                        "value": 4.2,
                        "valuecolor": "#ff4444",
                        "rangelabel": "Risco muito alto"
                    }
                ]
            }
        }

class ErrorResponse(BaseModel):
    """Error response model"""
    detail: str = Field(description="Error description")
    indicator_id: Optional[str] = Field(description="Requested indicator ID", default=None)
    
    class Config:
        json_schema_extra = {
            "example": {
                "detail": "Indicator with ID '999999' not found",
                "indicator_id": "999999"
            }
        }

class PanoramaIndicator(BaseModel):
    """Indicator data for city panorama"""
    indicator_id: str = Field(description="Climate indicator ID")
    indicator_name: str = Field(description="Climate indicator name")
    level: str = Field(description="Indicator hierarchy level")
    present_data: List[IndicatorValue] = Field(description="Current/present data points")
    future_trends: List[FutureTrend] = Field(description="Future projection data")
    
    class Config:
        json_schema_extra = {
            "example": {
                "indicator_id": "2",
                "indicator_name": "Risco de estresse hídrico",
                "level": "2",
                "present_data": [
                    {
                        "year": 2020,
                        "value": 0.42,
                        "valuecolor": "#FFCD00",
                        "rangelabel": "Médio"
                    }
                ],
                "future_trends": [
                    {
                        "year": 2030,
                        "scenario": "RCP4.5",
                        "value": 0.55,
                        "valuecolor": "#FF8C00",
                        "rangelabel": "Alto"
                    }
                ]
            }
        }

class PanoramaSector(BaseModel):
    """Sector with its level 2 indicators"""
    sector_name: str = Field(description="Strategic sector name")
    indicators: List[PanoramaIndicator] = Field(description="Level 2 indicators in this sector")
    
    class Config:
        json_schema_extra = {
            "example": {
                "sector_name": "Recursos Hídricos",
                "indicators": [
                    {
                        "indicator_id": "2",
                        "indicator_name": "Risco de estresse hídrico",
                        "level": "2"
                    }
                ]
            }
        }

class PanoramaSummary(BaseModel):
    """Summary statistics for the panorama"""
    total_sectors: int = Field(description="Number of sectors with level 2 indicators")
    total_indicators: int = Field(description="Total number of level 2 indicators")
    indicators_with_present_data: int = Field(description="Indicators with present data")
    indicators_with_future_trends: int = Field(description="Indicators with future projections")
    
    class Config:
        json_schema_extra = {
            "example": {
                "total_sectors": 6,
                "total_indicators": 12,
                "indicators_with_present_data": 12,
                "indicators_with_future_trends": 8
            }
        }

class PanoramaResponse(BaseModel):
    """City climate indicators panorama response"""
    geocod_ibge: str = Field(description="IBGE code of the municipality")
    city_name: str = Field(description="Municipality name")
    state: str = Field(description="State abbreviation")
    sectors: List[PanoramaSector] = Field(description="Sectors with their level 2 indicators")
    summary: PanoramaSummary = Field(description="Summary statistics")
    
    class Config:
        json_schema_extra = {
            "example": {
                "geocod_ibge": "4119905",
                "city_name": "Ponta Grossa/PR",
                "state": "PR",
                "sectors": [
                    {
                        "sector_name": "Recursos Hídricos",
                        "indicators": [
                            {
                                "indicator_id": "2",
                                "indicator_name": "Risco de estresse hídrico",
                                "level": "2",
                                "present_data": [],
                                "future_trends": []
                            }
                        ]
                    }
                ],
                "summary": {
                    "total_sectors": 6,
                    "total_indicators": 12,
                    "indicators_with_present_data": 12,
                    "indicators_with_future_trends": 8
                }
            }
        }

# Hierarchical Indicator Models
class HierarchicalIndicator(BaseModel):
    """Single indicator with its hierarchical information and children"""
    id: str = Field(description="Indicator ID")
    nome: str = Field(description="Indicator name") 
    nivel: str = Field(description="Indicator level (2, 3, 4, 5, 6)")
    setor_estrategico: str = Field(description="Strategic sector")
    indicador_pai: Optional[str] = Field(description="Parent indicator ID", default=None)
    descricao_simples: Optional[str] = Field(description="Simple description", default=None)
    descricao_completa: Optional[str] = Field(description="Complete description", default=None)
    anos: Optional[str] = Field(description="Available years as JSON string", default=None)
    unidade_medida: Optional[str] = Field(description="Unit of measurement", default=None)
    children: List['HierarchicalIndicator'] = Field(description="Child indicators", default_factory=list)
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "50001",
                "nome": "Malária",
                "nivel": "2",
                "setor_estrategico": "Saúde",
                "indicador_pai": "50000",
                "descricao_simples": "Risco de impacto das mudanças climáticas...",
                "children": [
                    {
                        "id": "50002", 
                        "nome": "Vulnerabilidade",
                        "nivel": "3",
                        "children": []
                    }
                ]
            }
        }

class HierarchyResponse(BaseModel):
    """Response containing hierarchical indicator structure"""
    indicator: HierarchicalIndicator = Field(description="Root indicator with nested children")
    total_indicators: int = Field(description="Total number of indicators in the hierarchy")
    depth_levels: List[str] = Field(description="Unique levels present in the hierarchy")
    
    class Config:
        json_schema_extra = {
            "example": {
                "indicator": {
                    "id": "50001",
                    "nome": "Malária", 
                    "nivel": "2",
                    "setor_estrategico": "Saúde",
                    "children": []
                },
                "total_indicators": 5,
                "depth_levels": ["2", "3", "6"]
            }
        }

# Forward reference resolution for self-referencing model
HierarchicalIndicator.model_rebuild()

# Initialize FastAPI app
app_description = """
Climate indicator data API for Brazilian municipalities based on AdaptaBrasil structure.

## Authentication
"""

if auth_config.enabled:
    app_description += """
**API Key Required**: Include `X-API-Key` header with your API key.

**Example:**
```bash
curl -H "X-API-Key: your-api-key-here" \\
     http://localhost:8001/api/v1/indicadores/count
```

**Public Endpoints** (no authentication required):
- `/health` - Service health check
- `/docs` - API documentation
- `/redoc` - Alternative API documentation
"""
else:
    app_description += """
**No Authentication**: All endpoints are publicly accessible.
"""

app = FastAPI(
    title="Painel do Clima Data API",
    description=app_description,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {
            "name": "indicators",
            "description": "Climate indicators data endpoints"
        },
        {
            "name": "health",
            "description": "Service health monitoring"
        },
        {
            "name": "auth",
            "description": "Authentication information"
        }
    ]
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# Global variables for caching
_indicators_data: Optional[Dict[str, Any]] = None
_city_filelist: Optional[Dict[str, Any]] = None
_city_data_cache: Dict[str, Dict[str, Any]] = {}
_data_file_path = Path(__file__).parent / "adaptaBrasilAPIEstrutura_filtered.json"
_data_dir_path = Path(__file__).parent.parent / "data"
_city_filelist_path = _data_dir_path / "city_filelist.json"

@lru_cache(maxsize=1)
def load_city_filelist() -> Dict[str, Any]:
    """
    Load and cache the city filelist data.
    
    Returns:
        Dictionary mapping city IDs to their metadata
        
    Raises:
        FileNotFoundError: If the city filelist file doesn't exist
        json.JSONDecodeError: If the JSON file is malformed
    """
    global _city_filelist
    
    if _city_filelist is None:
        logger.info(f"Loading city filelist from {_city_filelist_path}")
        
        if not _city_filelist_path.exists():
            error_msg = f"City filelist not found: {_city_filelist_path}"
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)
        
        try:
            with open(_city_filelist_path, 'r', encoding='utf-8') as file:
                _city_filelist = json.load(file)
            
            # Ensure we have a valid dictionary
            if _city_filelist is None:
                _city_filelist = {}
            
            logger.info(f"Successfully loaded {len(_city_filelist)} cities")
            
        except json.JSONDecodeError as e:
            error_msg = f"Invalid JSON in city filelist: {e}"
            logger.error(error_msg)
            raise json.JSONDecodeError(error_msg, e.doc, e.pos)
        except Exception as e:
            logger.error(f"Unexpected error loading city filelist: {e}")
            raise
    
    return _city_filelist or {}

def find_city_by_geocod_ibge(city_filelist: Dict[str, Any], geocod_ibge: str) -> Optional[str]:
    """
    Find city ID by IBGE geocode by searching through city data files.
    
    Args:
        city_filelist: Dictionary of city metadata
        geocod_ibge: IBGE geocode to search for
        
    Returns:
        City ID if found, None otherwise
    """
    # First check if the provided value is already a city ID in the filelist
    if geocod_ibge in city_filelist:
        return geocod_ibge
    
    # If not found as city ID, search through data files for geocod_ibge
    for city_id, city_info in city_filelist.items():
        state = city_info.get("state")
        if state:
            # Try to load city data to check geocod_ibge
            city_data = load_city_data(state, city_id)
            if city_data and city_data.get("indicators"):
                # Check first indicator for geocod_ibge
                first_indicator = city_data["indicators"][0]
                if str(first_indicator.get("geocod_ibge")) == geocod_ibge:
                    return city_id
    
    return None

def load_city_data(state: str, city_id: str) -> Optional[Dict[str, Any]]:
    """
    Load city climate data with caching.
    
    Args:
        state: State abbreviation (e.g., 'PR')
        city_id: City IBGE code
        
    Returns:
        Dictionary with city climate data or None if not found
        
    Raises:
        FileNotFoundError: If city data file doesn't exist
        json.JSONDecodeError: If the JSON file is malformed
    """
    cache_key = f"{state}_{city_id}"
    
    # Return from cache if available
    if cache_key in _city_data_cache:
        return _city_data_cache[cache_key]
    
    # Construct file path
    city_file_path = _data_dir_path / state / f"city_{city_id}.json"
    
    if not city_file_path.exists():
        logger.warning(f"City data file not found: {city_file_path}")
        return None
    
    try:
        logger.info(f"Loading city data from {city_file_path}")
        
        with open(city_file_path, 'r', encoding='utf-8') as file:
            city_data = json.load(file)
        
        # Cache the data
        _city_data_cache[cache_key] = city_data
        
        logger.info(f"Successfully loaded city data for {state}/{city_id}")
        return city_data
        
    except json.JSONDecodeError as e:
        error_msg = f"Invalid JSON in city data file: {e}"
        logger.error(error_msg)
        raise json.JSONDecodeError(error_msg, e.doc, e.pos)
    except Exception as e:
        logger.error(f"Unexpected error loading city data: {e}")
        raise

@lru_cache(maxsize=1)
def load_indicators_data() -> Dict[str, Any]:
    """
    Load and cache the indicators data from JSON file.
    Uses LRU cache to avoid reloading on every request.
    
    Returns:
        Dictionary mapping indicator IDs to their data
        
    Raises:
        FileNotFoundError: If the data file doesn't exist
        json.JSONDecodeError: If the JSON file is malformed
    """
    global _indicators_data
    
    if _indicators_data is None:
        logger.info(f"Loading indicators data from {_data_file_path}")
        
        if not _data_file_path.exists():
            error_msg = f"Data file not found: {_data_file_path}"
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)
        
        try:
            with open(_data_file_path, 'r', encoding='utf-8') as file:
                indicators_list = json.load(file)
            
            # Convert list to dictionary for O(1) lookup by ID
            _indicators_data = {
                indicator['id']: indicator 
                for indicator in indicators_list 
                if 'id' in indicator
            }
            
            logger.info(f"Successfully loaded {len(_indicators_data)} indicators")
            
        except json.JSONDecodeError as e:
            error_msg = f"Invalid JSON in data file: {e}"
            logger.error(error_msg)
            raise json.JSONDecodeError(error_msg, e.doc, e.pos)
        except Exception as e:
            logger.error(f"Unexpected error loading data: {e}")
            raise
    
    return _indicators_data

# Hierarchy Helper Functions
def build_hierarchical_indicator(indicator_id: str, indicators_data: Dict[str, Any], processed: Optional[set] = None) -> Optional[HierarchicalIndicator]:
    """
    Build a hierarchical indicator structure with all its children.
    
    Args:
        indicator_id: The ID of the indicator to build hierarchy for
        indicators_data: Dictionary of all indicators
        processed: Set of processed indicator IDs to avoid circular references
        
    Returns:
        HierarchicalIndicator with nested children or None if not found
    """
    if processed is None:
        processed = set()
        
    # Avoid circular references
    if indicator_id in processed:
        logger.warning(f"Circular reference detected for indicator {indicator_id}")
        return None
        
    # Get indicator data
    indicator_info = indicators_data.get(indicator_id)
    if not indicator_info:
        logger.warning(f"Indicator {indicator_id} not found in data")
        return None
        
    processed.add(indicator_id)
    
    # Create the base indicator
    hierarchical_indicator = HierarchicalIndicator(
        id=indicator_info.get('id', indicator_id),
        nome=indicator_info.get('nome', 'Unknown'),
        nivel=indicator_info.get('nivel', 'Unknown'),
        setor_estrategico=indicator_info.get('setor_estrategico', 'Unknown'),
        indicador_pai=indicator_info.get('indicador_pai'),
        descricao_simples=indicator_info.get('descricao_simples'),
        descricao_completa=indicator_info.get('descricao_completa'),
        anos=indicator_info.get('anos'),
        unidade_medida=indicator_info.get('unidade_medida'),
        children=[]
    )
    
    # Find all children of this indicator
    children = []
    for child_id, child_info in indicators_data.items():
        if child_info.get('indicador_pai') == indicator_id and child_id not in processed:
            child_hierarchy = build_hierarchical_indicator(child_id, indicators_data, processed.copy())
            if child_hierarchy:
                children.append(child_hierarchy)
    
    # Sort children by ID for consistent ordering
    children.sort(key=lambda x: x.id)
    hierarchical_indicator.children = children
    
    return hierarchical_indicator

def build_direct_children_only(indicator_id: str, indicators_data: Dict[str, Any]) -> Optional[HierarchicalIndicator]:
    """
    Build a hierarchical indicator structure with only direct children (one level down).
    
    Args:
        indicator_id: The ID of the indicator to build hierarchy for
        indicators_data: Dictionary of all indicators
        
    Returns:
        HierarchicalIndicator with only direct children or None if not found
    """
    # Get indicator data
    indicator_info = indicators_data.get(indicator_id)
    if not indicator_info:
        logger.warning(f"Indicator {indicator_id} not found in data")
        return None
    
    # Create the base indicator
    hierarchical_indicator = HierarchicalIndicator(
        id=indicator_info.get('id', indicator_id),
        nome=indicator_info.get('nome', 'Unknown'),
        nivel=indicator_info.get('nivel', 'Unknown'),
        setor_estrategico=indicator_info.get('setor_estrategico', 'Unknown'),
        indicador_pai=indicator_info.get('indicador_pai'),
        descricao_simples=indicator_info.get('descricao_simples'),
        descricao_completa=indicator_info.get('descricao_completa'),
        anos=indicator_info.get('anos'),
        unidade_medida=indicator_info.get('unidade_medida'),
        children=[]
    )
    
    # Find direct children only
    direct_children = []
    for child_id, child_info in indicators_data.items():
        if child_info.get('indicador_pai') == indicator_id:
            child_indicator = HierarchicalIndicator(
                id=child_info.get('id', child_id),
                nome=child_info.get('nome', 'Unknown'),
                nivel=child_info.get('nivel', 'Unknown'),
                setor_estrategico=child_info.get('setor_estrategico', 'Unknown'),
                indicador_pai=child_info.get('indicador_pai'),
                descricao_simples=child_info.get('descricao_simples'),
                descricao_completa=child_info.get('descricao_completa'),
                anos=child_info.get('anos'),
                unidade_medida=child_info.get('unidade_medida'),
                children=[]  # No grandchildren for direct children endpoint
            )
            direct_children.append(child_indicator)
    
    # Sort children by ID for consistent ordering
    direct_children.sort(key=lambda x: x.id)
    hierarchical_indicator.children = direct_children
    
    return hierarchical_indicator

def count_hierarchy_indicators(indicator: HierarchicalIndicator) -> int:
    """Count total indicators in a hierarchical structure"""
    count = 1  # Count the current indicator
    for child in indicator.children:
        count += count_hierarchy_indicators(child)
    return count

def get_hierarchy_levels(indicator: HierarchicalIndicator, levels: Optional[set] = None) -> List[str]:
    """Get all unique levels in a hierarchical structure"""
    if levels is None:
        levels = set()
    
    levels.add(indicator.nivel)
    for child in indicator.children:
        get_hierarchy_levels(child, levels)
    
    return sorted(list(levels))

# Middleware for request logging
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests with basic metrics"""
    start_time = request.headers.get("X-Request-Start")
    
    logger.info(f"Request: {request.method} {request.url.path} from {request.client.host if request.client else 'unknown'}")
    
    response = await call_next(request)
    
    logger.info(f"Response: {response.status_code} for {request.method} {request.url.path}")
    
    return response

@app.get(
    "/health", 
    tags=["health"],
    summary="Health check endpoint",
    description="Returns the health status of the API service"
)
async def health_check():
    """Health check endpoint to verify service availability"""
    try:
        # Test data loading capability
        data = load_indicators_data()
        indicators_count = len(data)
        
        return {
            "status": "healthy",
            "service": "Painel do Clima Data API",
            "version": "1.0.0",
            "indicators_loaded": indicators_count,
            "data_file": str(_data_file_path.name)
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy",
                "service": "Painel do Clima Data API",
                "error": str(e)
            }
        )

@app.get(
    "/auth/status",
    tags=["auth"],
    summary="Authentication status",
    description="Check authentication configuration and test API key"
)
async def auth_status(authenticated: bool = Depends(verify_api_key)):
    """
    Get authentication status and configuration information.
    
    Returns information about the current authentication setup and validates
    the provided API key if authentication is enabled.
    """
    return {
        "authentication_enabled": auth_config.enabled,
        "authenticated": authenticated,
        "public_endpoints": list(auth_config.public_endpoints),
        "total_valid_keys": len(auth_config.valid_keys) if auth_config.enabled else 0,
        "message": "Authentication successful" if authenticated else "No authentication required"
    }

@app.get(
    "/api/v1/indicadores/estrutura",
    response_model=IndicatorListResponse,
    responses={
        200: {
            "description": "List of all indicators retrieved successfully",
            "model": IndicatorListResponse
        },
        500: {
            "description": "Internal server error",
            "model": ErrorResponse
        }
    },
    tags=["indicators"],
    summary="Get all indicators structure",
    description="Retrieve complete list of all climate indicators with optional filtering by sector, level, or search term"
)
async def get_all_indicators(
    authenticated: bool = Depends(verify_api_key),
    setor: Optional[str] = Query(
        None, 
        description="Filter by strategic sector (e.g., 'Recursos Hídricos', 'Saúde')",
        example="Recursos Hídricos"
    ),
    nivel: Optional[str] = Query(
        None,
        description="Filter by indicator level (e.g., '2', '3', '4')", 
        example="2"
    ),
    search: Optional[str] = Query(
        None,
        description="Search in indicator names (case-insensitive)",
        example="hídrico"
    ),
    limit: int = Query(
        1000,
        description="Maximum number of indicators to return",
        ge=1,
        le=1000
    ),
    offset: int = Query(
        0,
        description="Number of indicators to skip (for pagination)",
        ge=0
    )
) -> IndicatorListResponse:
    """
    Get all climate indicators structure data with optional filtering.
    
    This endpoint retrieves climate indicators from the filtered AdaptaBrasil 
    structure with support for:
    - Filtering by strategic sector
    - Filtering by hierarchy level  
    - Text search in indicator names
    - Pagination with limit/offset
    
    Args:
        setor: Filter by strategic sector name
        nivel: Filter by indicator hierarchy level
        search: Search term for indicator names
        limit: Maximum results to return (default: 1000)
        offset: Number of results to skip (default: 0)
        
    Returns:
        IndicatorListResponse: Filtered list of indicators with metadata
        
    Raises:
        HTTPException: 500 for server errors
    """
    logger.info(f"Requesting indicators - setor:{setor}, nivel:{nivel}, search:'{search}', limit:{limit}, offset:{offset}")
    
    try:
        # Load indicators data
        indicators_data = load_indicators_data()
        
        # Apply filters
        filtered_indicators = []
        for indicator in indicators_data.values():
            # Filter by sector
            if setor and indicator.get('setor_estrategico', '').lower() != setor.lower():
                continue
                
            # Filter by level
            if nivel and indicator.get('nivel') != nivel:
                continue
                
            # Filter by search term in name
            if search and search.lower() not in indicator.get('nome', '').lower():
                continue
                
            filtered_indicators.append(indicator)
        
        # Get total count before pagination
        total_filtered = len(filtered_indicators)
        
        # Apply pagination
        paginated_indicators = filtered_indicators[offset:offset + limit]
        
        # Convert to response objects
        indicators = [
            IndicatorResponse(**indicator) 
            for indicator in paginated_indicators
        ]
        
        # Get unique sectors from ALL data (not just filtered)
        sectors = set()
        for indicator in indicators_data.values():
            if 'setor_estrategico' in indicator:
                sectors.add(indicator['setor_estrategico'])
        
        logger.info(f"Retrieved {len(indicators)} indicators (filtered: {total_filtered}, total: {len(indicators_data)})")
        
        return IndicatorListResponse(
            indicators=indicators,
            total_count=total_filtered,  # Count of filtered results, not paginated
            sectors=sorted(list(sectors))
        )
        
    except Exception as e:
        logger.error(f"Unexpected error retrieving indicators: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while retrieving indicators data"
        )

@app.get(
    "/api/v1/indicadores/estrutura/{indicador_id}",
    response_model=IndicatorResponse,
    responses={
        200: {
            "description": "Indicator data retrieved successfully",
            "model": IndicatorResponse
        },
        404: {
            "description": "Indicator not found",
            "model": ErrorResponse
        },
        500: {
            "description": "Internal server error",
            "model": ErrorResponse
        }
    },
    tags=["indicators"],
    summary="Get indicator structure by ID",
    description="Retrieve detailed climate indicator information by its unique identifier from the AdaptaBrasil filtered structure"
)
async def get_indicator_structure(
    authenticated: bool = Depends(verify_api_key),
    indicador_id: str = PathParam(
        ...,
        description="Unique identifier of the climate indicator",
        examples=["2"],
        pattern=r"^[0-9]+$"  # Only numeric IDs allowed
    )
) -> IndicatorResponse:
    """
    Get climate indicator structure data by ID.
    
    This endpoint retrieves detailed information about a specific climate indicator
    from the filtered AdaptaBrasil structure, including metadata, descriptions,
    URLs for data access, and hierarchical relationships.
    
    Args:
        indicador_id: The unique numeric identifier of the climate indicator
        
    Returns:
        IndicatorResponse: Complete indicator data structure
        
    Raises:
        HTTPException: 404 if indicator not found, 500 for server errors
    """
    logger.info(f"Requesting indicator structure for ID: {indicador_id}")
    
    try:
        # Load indicators data
        indicators_data = load_indicators_data()
        
        # Check if indicator exists
        if indicador_id not in indicators_data:
            logger.warning(f"Indicator not found: {indicador_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Indicator with ID '{indicador_id}' not found",
            )
        
        # Get indicator data
        indicator = indicators_data[indicador_id]
        
        logger.info(f"Successfully retrieved indicator: {indicador_id} - {indicator.get('nome', 'Unknown')}")
        
        return IndicatorResponse(**indicator)
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"Unexpected error retrieving indicator {indicador_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error while retrieving indicator data"
        )

@app.get(
    "/api/v1/indicadores/count",
    tags=["indicators"],
    summary="Get total indicators count",
    description="Returns the total number of available indicators in the system"
)
async def get_indicators_count(authenticated: bool = Depends(verify_api_key)):
    """Get the total count of available indicators"""
    try:
        data = load_indicators_data()
        return {
            "total_indicators": len(data),
            "data_source": "adaptaBrasilAPIEstrutura_filtered.json"
        }
    except Exception as e:
        logger.error(f"Error getting indicators count: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving indicators count"
        )

@app.get(
    "/api/v1/indicadores/setores",
    tags=["indicators"],
    summary="Get available sectors",
    description="Returns a list of all available strategic sectors (setores estratégicos)"
)
async def get_available_sectors(authenticated: bool = Depends(verify_api_key)):
    """Get list of all unique strategic sectors"""
    try:
        data = load_indicators_data()
        sectors = set()
        
        for indicator in data.values():
            if 'setor_estrategico' in indicator:
                sectors.add(indicator['setor_estrategico'])
        
        return {
            "sectors": sorted(list(sectors)),
            "total_sectors": len(sectors)
        }
    except Exception as e:
        logger.error(f"Error getting sectors: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving sectors"
        )

@app.get(
    "/api/v1/indicadores/dados/{estado}/{cidade_ou_geocod}/panorama",
    response_model=PanoramaResponse,
    responses={
        200: {
            "description": "City climate indicators panorama retrieved successfully",
            "model": PanoramaResponse
        },
        404: {
            "description": "City or state not found",
            "model": ErrorResponse
        },
        500: {
            "description": "Internal server error",
            "model": ErrorResponse
        }
    },
    tags=["indicators"],
    summary="Get city climate indicators panorama",
    description="Retrieve complete panorama of all level 2 climate indicators for a city, organized by strategic sectors"
)
async def get_city_panorama(
    authenticated: bool = Depends(verify_api_key),
    estado: str = PathParam(
        ...,
        description="State abbreviation (e.g., 'PR', 'SP', 'RJ')",
        examples=["PR"],
        pattern=r"^[A-Z]{2}$"
    ),
    cidade_ou_geocod: str = PathParam(
        ...,
        description="City ID or IBGE geocode (7-digit IBGE code)",
        examples=["5387", "4119905"],
        pattern=r"^[0-9]+$"
    )
) -> PanoramaResponse:
    """
    Get complete panorama of climate indicators for a specific city.
    
    This endpoint retrieves all level 2 climate indicators for a city, organized by
    strategic sectors (setores estratégicos). Each indicator includes:
    - Present data points with values, colors, and range labels
    - Future climate projections (2030, 2050) with scenarios
    - Summary statistics for data availability
    
    Perfect for:
    - City-wide climate risk assessment dashboards
    - LLM agents generating comprehensive climate narratives
    - Municipal planning and adaptation strategies
    - Climate vulnerability overviews
    
    Args:
        estado: Two-letter state abbreviation (BR state codes)
        cidade_ou_geocod: City ID or 7-digit IBGE geocode
        
    Returns:
        PanoramaResponse: Complete city climate indicators organized by sectors
        
    Raises:
        HTTPException: 404 if city not found, 500 for server errors
    """
    logger.info(f"Requesting panorama - Estado: {estado}, Cidade/Geocod: {cidade_ou_geocod}")
    
    try:
        # Load city filelist to resolve city ID from geocod_ibge if needed
        city_filelist = load_city_filelist()
        
        # Try to resolve city ID (could be city ID or geocod_ibge)
        cidade = find_city_by_geocod_ibge(city_filelist, cidade_ou_geocod)
        if cidade is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"City not found for {estado}/{cidade_ou_geocod} (tried both city ID and IBGE geocode)"
            )
        
        # Load city data
        city_data = load_city_data(estado, cidade)
        if city_data is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"City data not found for {estado}/{cidade}"
            )
        
        # Get city info from filelist
        city_info = city_filelist.get(cidade)
        if city_info is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"City metadata not found for city {cidade}"
            )
        
        # Load indicators data to get level 2 indicators and their sectors
        indicators_data = load_indicators_data()
        
        # Get all level 2 indicators grouped by sector
        level2_indicators_by_sector = {}
        for indicator_id, indicator_info in indicators_data.items():
            if indicator_info.get('nivel') == '2':
                sector = indicator_info.get('setor_estrategico', 'Unknown')
                if sector not in level2_indicators_by_sector:
                    level2_indicators_by_sector[sector] = []
                level2_indicators_by_sector[sector].append({
                    'id': indicator_id,
                    'info': indicator_info
                })
        
        # Process each sector and its indicators
        sectors = []
        total_indicators = 0
        indicators_with_present = 0
        indicators_with_future = 0
        
        for sector_name, sector_indicators in level2_indicators_by_sector.items():
            panorama_indicators = []
            
            for indicator_data in sector_indicators:
                indicator_id = indicator_data['id']
                indicator_info = indicator_data['info']
                total_indicators += 1
                
                # Process data for this indicator (reuse logic from single indicator endpoint)
                present_data_points = []
                future_trends_data = []
                present_seen = set()
                future_seen = set()
                
                indicators_list = city_data.get("indicators", [])
                
                for data_point in indicators_list:
                    if str(data_point.get("indicator_id")) == indicator_id:
                        year = data_point.get("year")
                        scenario_id = data_point.get("scenario_id")
                        value = data_point.get("value")
                        
                        if year and year <= 2020:
                            # Present data
                            present_key = (year, value, data_point.get("valuecolor"), data_point.get("rangelabel"))
                            if present_key not in present_seen:
                                present_seen.add(present_key)
                                present_data_points.append(IndicatorValue(
                                    year=year,
                                    value=float(value or 0),
                                    valuecolor=data_point.get("valuecolor", "#cccccc"),
                                    rangelabel=data_point.get("rangelabel", "N/A")
                                ))
                        elif year and year > 2020:
                            # Future projections
                            scenario = "RCP4.5"
                            if scenario_id:
                                scenario = f"Scenario_{scenario_id}"
                            
                            future_key = (year, scenario_id, value, data_point.get("valuecolor"), data_point.get("rangelabel"))
                            if future_key not in future_seen:
                                future_seen.add(future_key)
                                future_trends_data.append(FutureTrend(
                                    year=year,
                                    scenario=scenario,
                                    value=float(value or 0),
                                    valuecolor=data_point.get("valuecolor", "#cccccc"),
                                    rangelabel=data_point.get("rangelabel", "N/A")
                                ))
                
                # Check for dedicated future_trends structure
                processed_future_trends = set()
                for data_point in indicators_list:
                    if str(data_point.get("indicator_id")) == indicator_id:
                        future_trends_obj = data_point.get('future_trends', {})
                        if future_trends_obj:
                            trends_key = str(sorted(future_trends_obj.items()))
                            if trends_key not in processed_future_trends:
                                processed_future_trends.add(trends_key)
                                
                                for year_str, trend_data in future_trends_obj.items():
                                    try:
                                        year = int(year_str)
                                        future_trends_data.append(FutureTrend(
                                            year=year,
                                            scenario="RCP4.5",
                                            value=float(trend_data.get('value', 0)),
                                            valuecolor=trend_data.get('valuecolor', '#000000'),
                                            rangelabel=trend_data.get('valuelabel', trend_data.get('rangelabel', ''))
                                        ))
                                    except (ValueError, TypeError):
                                        continue
                
                # Sort data by year
                present_data_points.sort(key=lambda x: x.year)
                future_trends_data.sort(key=lambda x: x.year)
                
                # Update counters
                if present_data_points:
                    indicators_with_present += 1
                if future_trends_data:
                    indicators_with_future += 1
                
                # Create panorama indicator
                panorama_indicators.append(PanoramaIndicator(
                    indicator_id=indicator_id,
                    indicator_name=indicator_info.get('nome', 'Unknown'),
                    level=indicator_info.get('nivel', '2'),
                    present_data=present_data_points,
                    future_trends=future_trends_data
                ))
            
            # Only add sectors that have indicators
            if panorama_indicators:
                sectors.append(PanoramaSector(
                    sector_name=sector_name,
                    indicators=panorama_indicators
                ))
        
        # Create summary
        summary = PanoramaSummary(
            total_sectors=len(sectors),
            total_indicators=total_indicators,
            indicators_with_present_data=indicators_with_present,
            indicators_with_future_trends=indicators_with_future
        )
        
        logger.info(f"Successfully retrieved panorama: {total_indicators} indicators across {len(sectors)} sectors")
        
        return PanoramaResponse(
            geocod_ibge=city_data.get("indicators", [{}])[0].get("geocod_ibge", cidade_ou_geocod) if city_data.get("indicators") else cidade_ou_geocod,
            city_name=city_info.get("name", city_data.get("name", "Unknown")),
            state=estado,
            sectors=sectors,
            summary=summary
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"Unexpected error retrieving panorama for {estado}/{cidade_ou_geocod}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error while retrieving panorama data"
        )

@app.get(
    "/api/v1/indicadores/dados/{estado}/{cidade_ou_geocod}/{indicador_id}",
    response_model=IndicatorDataResponse,
    responses={
        200: {
            "description": "Indicator data retrieved successfully",
            "model": IndicatorDataResponse
        },
        404: {
            "description": "City, state, or indicator data not found",
            "model": ErrorResponse
        },
        500: {
            "description": "Internal server error",
            "model": ErrorResponse
        }
    },
    tags=["indicators"],
    summary="Get indicator data values",
    description="Retrieve actual climate indicator data values for a specific city using either city ID or IBGE geocode, including present data and future projections"
)
async def get_indicator_data(
    authenticated: bool = Depends(verify_api_key),
    estado: str = PathParam(
        ...,
        description="State abbreviation (e.g., 'PR', 'SP', 'RJ')",
        examples=["PR"],
        pattern=r"^[A-Z]{2}$"
    ),
    cidade_ou_geocod: str = PathParam(
        ...,
        description="City ID from Adapta Brasil structure or IBGE geocode (7-digit IBGE code)",
        examples=["5387", "4119905"],
        pattern=r"^[0-9]+$"
    ),
    indicador_id: str = PathParam(
        ...,
        description="Climate indicator ID",
        examples=["2"],
        pattern=r"^[0-9]+$"
    )
) -> IndicatorDataResponse:
    """
    Get actual climate indicator data values for a specific city.
    
    This endpoint retrieves the actual climate data values for a given indicator
    in a specific city, supporting lookup by either city ID or IBGE geocode:
    - Present data points with values, colors, and range labels (current year)
    - Future climate projections (2030, 2050) with different scenarios
    - City and indicator metadata for context
    
    Perfect for:
    - Frontend data visualization (colors and labels included)
    - LLM climate narrative analysis (structured data with trends)
    - Climate impact assessment and reporting
    
    Args:
        estado: Two-letter state abbreviation (BR state codes)
        cidade_ou_geocod: City ID or 7-digit IBGE geocode
        indicador_id: Numeric climate indicator identifier
        
    Returns:
        IndicatorDataResponse: Complete indicator data with present values and projections
        
    Raises:
        HTTPException: 404 if city/indicator not found, 500 for server errors
    """
    logger.info(f"Requesting indicator data - Estado: {estado}, Cidade/Geocod: {cidade_ou_geocod}, Indicator: {indicador_id}")
    
    try:
        # Load city filelist to resolve city ID from geocod_ibge if needed
        city_filelist = load_city_filelist()
        
        # Try to resolve city ID (could be city ID or geocod_ibge)
        cidade = find_city_by_geocod_ibge(city_filelist, cidade_ou_geocod)
        if cidade is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"City not found for {estado}/{cidade_ou_geocod} (tried both city ID and IBGE geocode)"
            )
        
        # Load city data
        city_data = load_city_data(estado, cidade)
        if city_data is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"City data not found for {estado}/{cidade}"
            )
        
        # Get city info from filelist
        city_info = city_filelist.get(cidade)
        if city_info is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"City metadata not found for city {cidade}"
            )
        
        # Load indicator structure for metadata
        indicators_data = load_indicators_data()
        indicator_info = indicators_data.get(indicador_id)
        if indicator_info is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Indicator with ID '{indicador_id}' not found"
            )
        
        # Filter city data for this specific indicator
        present_data_points = []
        future_trends_data = []
        
        # Track unique combinations to avoid duplicates
        present_seen = set()
        future_seen = set()
        
        # City data structure: {"indicators": [{"indicator_id": ..., "year": ..., etc}]}
        indicators_list = city_data.get("indicators", [])
        
        for data_point in indicators_list:
            if str(data_point.get("indicator_id")) == indicador_id:
                # Check if this is present data or future trend
                year = data_point.get("year")
                scenario_id = data_point.get("scenario_id")
                value = data_point.get("value")
                
                if year and year <= 2020:
                    # Present data - create unique key for deduplication
                    present_key = (year, value, data_point.get("valuecolor"), data_point.get("rangelabel"))
                    if present_key not in present_seen:
                        present_seen.add(present_key)
                        present_data_points.append(IndicatorValue(
                            year=year,
                            value=float(value or 0),
                            valuecolor=data_point.get("valuecolor", "#cccccc"),
                            rangelabel=data_point.get("rangelabel", "N/A")
                        ))
                elif year and year > 2020:
                    # Future projections - check for scenario information
                    scenario = "RCP4.5"  # Default scenario
                    if scenario_id:
                        # Map scenario IDs to scenario names if needed
                        scenario = f"Scenario_{scenario_id}"
                    
                    # Create unique key for future trends deduplication
                    future_key = (year, scenario_id, value, data_point.get("valuecolor"), data_point.get("rangelabel"))
                    if future_key not in future_seen:
                        future_seen.add(future_key)
                        future_trends_data.append(FutureTrend(
                            year=year,
                            scenario=scenario,
                            value=float(value or 0),
                            valuecolor=data_point.get("valuecolor", "#cccccc"),
                            rangelabel=data_point.get("rangelabel", "N/A")
                        ))
        
        # Also check for dedicated future_trends structure (process only once)
        processed_future_trends = set()
        for data_point in indicators_list:
            if str(data_point.get("indicator_id")) == indicador_id:
                future_trends_obj = data_point.get('future_trends', {})
                if future_trends_obj:
                    # Use a unique key to avoid processing the same future_trends multiple times
                    trends_key = str(sorted(future_trends_obj.items()))
                    if trends_key not in processed_future_trends:
                        processed_future_trends.add(trends_key)
                        
                        # future_trends is a dictionary keyed by year (2030, 2050)
                        for year_str, trend_data in future_trends_obj.items():
                            try:
                                year = int(year_str)
                                future_trends_data.append(FutureTrend(
                                    year=year,
                                    scenario="RCP4.5",  # Default scenario
                                    value=float(trend_data.get('value', 0)),
                                    valuecolor=trend_data.get('valuecolor', '#000000'),
                                    rangelabel=trend_data.get('valuelabel', trend_data.get('rangelabel', ''))
                                ))
                            except (ValueError, TypeError):
                                continue
        
        # Sort data by year
        present_data_points.sort(key=lambda x: x.year)
        future_trends_data.sort(key=lambda x: x.year)
        
        if not present_data_points and not future_trends_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No data found for indicator {indicador_id} in city {cidade}/{estado}"
            )
        
        logger.info(f"Successfully retrieved {len(present_data_points)} present data points and {len(future_trends_data)} future projections")
        
        return IndicatorDataResponse(
            geocod_ibge=city_data.get("indicators", [{}])[0].get("geocod_ibge", cidade_ou_geocod) if city_data.get("indicators") else cidade_ou_geocod,
            city_name=city_info.get("name", city_data.get("name", "Unknown")),
            state=estado,
            indicator_id=indicador_id,
            indicator_name=indicator_info.get("nome", "Unknown Indicator"),
            present_data=present_data_points,
            future_trends=future_trends_data
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"Unexpected error retrieving indicator data for {estado}/{cidade_ou_geocod}/{indicador_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error while retrieving indicator data"
        )

@app.get(
    "/api/v1/indicadores/estrutura/{indicator_id}/arvore-completa",
    response_model=HierarchyResponse,
    responses={
        200: {
            "description": "Complete indicator hierarchy retrieved successfully",
            "model": HierarchyResponse
        },
        404: {
            "description": "Indicator not found",
            "model": ErrorResponse
        },
        500: {
            "description": "Internal server error",
            "model": ErrorResponse
        }
    },
    tags=["indicators"],
    summary="Get complete indicator hierarchy tree",
    description="Retrieve the complete hierarchical structure of an indicator including ALL descendants at any level"
)
async def get_complete_indicator_hierarchy(
    authenticated: bool = Depends(verify_api_key),
    indicator_id: str = PathParam(
        ...,
        description="Climate indicator ID to get complete hierarchy for",
        examples=["50001", "50004"],
        pattern=r"^[0-9]+$"
    )
) -> HierarchyResponse:
    """
    Get complete hierarchical tree for a climate indicator.
    
    Returns the indicator plus ALL its descendants at any level, creating a complete
    tree structure. Perfect for comprehensive analysis and visualization of complex
    indicator relationships.
    
    Examples:
    - indicator_id=50001: Returns 50001 + all children, grandchildren, etc.
    - indicator_id=50004: Returns 50004 + 50027 + 50028 + 50029 + any deeper levels
    
    Args:
        indicator_id: The ID of the root indicator
        
    Returns:
        HierarchyResponse: Complete nested hierarchy with metadata
        
    Raises:
        HTTPException: 404 if indicator not found, 500 for server errors
    """
    logger.info(f"Requesting complete hierarchy for indicator: {indicator_id}")
    
    try:
        # Load indicators data
        indicators_data = load_indicators_data()
        
        # Build complete hierarchy
        hierarchy = build_hierarchical_indicator(indicator_id, indicators_data)
        
        if hierarchy is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Indicator {indicator_id} not found"
            )
        
        # Calculate metadata
        total_indicators = count_hierarchy_indicators(hierarchy)
        depth_levels = get_hierarchy_levels(hierarchy)
        
        logger.info(f"Successfully built complete hierarchy for {indicator_id}: {total_indicators} indicators across {len(depth_levels)} levels")
        
        return HierarchyResponse(
            indicator=hierarchy,
            total_indicators=total_indicators,
            depth_levels=depth_levels
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"Unexpected error building complete hierarchy for {indicator_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error while building indicator hierarchy"
        )

@app.get(
    "/api/v1/indicadores/estrutura/{indicator_id}/filhos",
    response_model=HierarchyResponse,
    responses={
        200: {
            "description": "Direct children hierarchy retrieved successfully",
            "model": HierarchyResponse
        },
        404: {
            "description": "Indicator not found",
            "model": ErrorResponse
        },
        500: {
            "description": "Internal server error",
            "model": ErrorResponse
        }
    },
    tags=["indicators"],
    summary="Get direct children of indicator",
    description="Retrieve indicator with only its direct children (one level down)"
)
async def get_indicator_direct_children(
    authenticated: bool = Depends(verify_api_key),
    indicator_id: str = PathParam(
        ...,
        description="Climate indicator ID to get direct children for",
        examples=["50001", "50004"],
        pattern=r"^[0-9]+$"
    )
) -> HierarchyResponse:
    """
    Get direct children hierarchy for a climate indicator.
    
    Returns the indicator plus only its direct children (one level down).
    Perfect for exploring indicator structure level by level without overwhelming
    detail from deeper hierarchies.
    
    Examples:
    - indicator_id=50001: Returns 50001 (L2) + 50002 (L3) + 50003 (L3) + 50004 (L3)
    - No grandchildren or deeper levels included
    
    Args:
        indicator_id: The ID of the parent indicator
        
    Returns:
        HierarchyResponse: Indicator with direct children only
        
    Raises:
        HTTPException: 404 if indicator not found, 500 for server errors
    """
    logger.info(f"Requesting direct children for indicator: {indicator_id}")
    
    try:
        # Load indicators data
        indicators_data = load_indicators_data()
        
        # Build direct children hierarchy
        hierarchy = build_direct_children_only(indicator_id, indicators_data)
        
        if hierarchy is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Indicator {indicator_id} not found"
            )
        
        # Calculate metadata
        total_indicators = count_hierarchy_indicators(hierarchy)
        depth_levels = get_hierarchy_levels(hierarchy)
        
        logger.info(f"Successfully built direct children hierarchy for {indicator_id}: {total_indicators} indicators across {len(depth_levels)} levels")
        
        return HierarchyResponse(
            indicator=hierarchy,
            total_indicators=total_indicators,
            depth_levels=depth_levels
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"Unexpected error building direct children hierarchy for {indicator_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error while building indicator hierarchy"
        )

if __name__ == "__main__":
    logger.info("Starting Painel do Clima Data API Service")
    uvicorn.run(
        "data_api_service:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )
