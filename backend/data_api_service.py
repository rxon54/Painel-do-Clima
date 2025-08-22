#!/usr/bin/env python3
"""
Painel do Clima Data API Service

A FastAPI service that provides access to climate indicator data from AdaptaBrasil API structure.
Serves filtered climate indicators with efficient caching and proper error handling.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from functools import lru_cache

import uvicorn
from fastapi import FastAPI, HTTPException, Path as PathParam, Query, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

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

# Initialize FastAPI app
app = FastAPI(
    title="Painel do Clima Data API",
    description="Climate indicator data API for Brazilian municipalities based on AdaptaBrasil structure",
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
async def get_indicators_count():
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
async def get_available_sectors():
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

if __name__ == "__main__":
    logger.info("Starting Painel do Clima Data API Service")
    uvicorn.run(
        "data_api_service:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )
