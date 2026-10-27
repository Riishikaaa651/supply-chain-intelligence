from typing import Literal
from pydantic import BaseModel, ConfigDict, Field
#----------Request----------------
class OrderRequest(BaseModel):
    order_item_id: int = Field(..., gt=0, description="Unique ID of the order item", examples=[2])

#----------Response----------------
class DelayPrediction(BaseModel):
    order_item_id: int
    order_id: int
    shipping_mode: str
    order_region: str
    category_name: str
    delay_prob: float = Field(..., ge=0, le=1, description="Probability that the order is delivered late")
    risk_level: Literal["Low", "Medium", "High"]
    mode_avg_delay: float
    region_avg_delay: float


class ShortagePrediction(BaseModel):
    order_item_id: int
    order_id: int
    product_name: str
    category_name: str
    shortage_score: float = Field(..., description="Ranking score, NOT a probability")
    risk_level: Literal["Low", "Medium", "High"]
    product_demand_mean: float
    product_demand_std: float
    product_order_history_count: int

# ---------- GenAI ----------
class BriefingRequest(BaseModel):
    order_item_id: int = Field(..., gt=0, examples=[2])
    risk_type: Literal["delay", "shortage"]


class BriefingResponse(BaseModel):
    order_item_id: int
    risk_type: str
    briefing: str
    cached: bool


class WhatIfRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)   # remove spaces around the question

    order_item_id: int = Field(..., gt=0, examples=[2])
    risk_type: Literal["delay", "shortage"]
    question: str = Field(..., min_length=5, max_length=200,
                          examples=["What if we ship this order with First Class instead?"])


class WhatIfResponse(BaseModel):
    order_item_id: int
    risk_type: str
    question: str
    answer: str
    cached: bool


class WhatIfQuestions(BaseModel):
    risk_type: str
    questions: list[str]

# ---------- Dashboard ----------
class Summary(BaseModel):
    total_orders: int
    delay_high: int
    shortage_high: int
    both_high: int
    avg_delay_prob: float


class FilterOptions(BaseModel):
    shipping_modes: list[str]
    regions: list[str]


class RiskRow(BaseModel):
    order_item_id: int
    order_id: int
    shipping_mode: str
    order_region: str
    category_name: str
    product_name: str
    delay_prob: float
    delay_risk: str
    shortage_score: float
    shortage_risk: str


class RiskTable(BaseModel):
    total: int
    limit: int
    offset: int
    rows: list[RiskRow]


class ModeStat(BaseModel):
    shipping_mode: str
    orders: int
    avg_delay_prob: float
    high_risk_pct: float


class CategoryStat(BaseModel):
    category_name: str
    orders: int
    avg_shortage_prob: float
    high_risk_pct: float