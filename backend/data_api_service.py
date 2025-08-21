#!/usr/bin/env python3
"""
Painel do Clima Data API Service

A FastAPI service that provides access to climate indicator data from AdaptaBrasil API structure.
Serves filtered climate indicators with efficient caching and proper error handling.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from functools import lru_cache

import uvicorn
from fastapi import FastAPI, HTTPException, Path as PathParam, Request, status
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
_data_file_path = Path(__file__).parent / "adaptaBrasilAPIEstrutura_filtered.json"

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

if __name__ == "__main__":
    logger.info("Starting Painel do Clima Data API Service")
    uvicorn.run(
        "data_api_service:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )
