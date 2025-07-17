from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class IndicatorData(BaseModel):
    indicator_id: str
    indicator_name: str = Field(alias="indicator_name:")
    descricao_completa: str
    proporcao_direta: str
    anos: str
    value: float
    rangelabel: str
    future_trends: dict
    valuecolor: str

class NarrativeComponent(BaseModel):
    component_type: str
    title: str
    body_text: Optional[str] = None # Made optional for all components
    # Optional fields that might be present in specific components
    current_value: Optional[float] = None
    current_label: Optional[str] = None
    projected_value: Optional[float] = None
    projected_label: Optional[str] = None
    stat_change: Optional[str] = None
    unit: Optional[str] = None
    examples: Optional[List[str]] = None
    action_items: Optional[List[str]] = None
    icon: Optional[str] = None # Emojis will be added by human-in-the-loop
    implications: Optional[List[str]] = None # Added for daily_implications component
    solutions: Optional[List[Dict[str, str]]] = None # Added for solutions component
    supporting_indicators: Optional[List[Dict[str, Any]]] = None # NEW: Attach supporting indicator data

class ClimateNarrative(BaseModel):
    city_id: str
    city_name: str
    narrative_components: List[NarrativeComponent]


