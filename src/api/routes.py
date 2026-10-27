import logging
from typing import Literal, Optional

from fastapi import APIRouter, HTTPException, Query

from src.database import queries
from src.database.db_connection import load_config
from src.genai.briefing import get_explanation
from src.api.schemas import (
    OrderRequest, DelayPrediction, ShortagePrediction,
    BriefingRequest, BriefingResponse,
    WhatIfRequest, WhatIfResponse, WhatIfQuestions,
    Summary, FilterOptions, RiskTable, ModeStat, CategoryStat,
)

router = APIRouter()
logger = logging.getLogger(__name__)


def _clean(row):
    """Turn numpy numbers from pandas into normal Python numbers."""
    return {k: (v.item() if hasattr(v, "item") else v) for k, v in row.items()}


def _check_order_exists(risk_type, order_item_id):
    """Return 404 if the order is not in the database."""
    if risk_type == "delay":
        facts = queries.get_delay_facts(order_item_id)
    else:
        facts = queries.get_shortage_facts(order_item_id)
    if facts is None:
        raise HTTPException(status_code=404, detail=f"No order found with order_item_id {order_item_id}")


# ---------------- Predictions ----------------
@router.post("/predict/delay", response_model=DelayPrediction, tags=["Predictions"])
def predict_delay(req: OrderRequest):
    facts = queries.get_delay_facts(req.order_item_id)
    if facts is None:
        raise HTTPException(status_code=404, detail=f"No order found with order_item_id {req.order_item_id}")
    return _clean(facts)


@router.post("/predict/shortage", response_model=ShortagePrediction, tags=["Predictions"])
def predict_shortage(req: OrderRequest):
    facts = queries.get_shortage_facts(req.order_item_id)
    if facts is None:
        raise HTTPException(status_code=404, detail=f"No order found with order_item_id {req.order_item_id}")
    facts = _clean(facts)
    facts["shortage_score"] = facts.pop("shortage_prob")   # honest name: it is a score
    return facts


# ---------------- GenAI ----------------
@router.post("/briefing", response_model=BriefingResponse, tags=["GenAI"])
def briefing(req: BriefingRequest):
    _check_order_exists(req.risk_type, req.order_item_id)
    try:
        result = get_explanation(f"{req.risk_type}_briefing", req.order_item_id)
    except Exception:
        logger.exception("Briefing failed")
        raise HTTPException(status_code=502, detail="The AI explanation service failed. Please try again.")
    return {"order_item_id": req.order_item_id, "risk_type": req.risk_type,
            "briefing": result["text"], "cached": result["cached"]}


@router.get("/whatif/questions", response_model=WhatIfQuestions, tags=["GenAI"])
def whatif_questions(risk_type: Literal["delay", "shortage"]):
    return {"risk_type": risk_type, "questions": load_config()["whatif_questions"][risk_type]}


@router.post("/whatif", response_model=WhatIfResponse, tags=["GenAI"])
def whatif(req: WhatIfRequest):
    _check_order_exists(req.risk_type, req.order_item_id)
    try:
        result = get_explanation(f"{req.risk_type}_whatif", req.order_item_id, question=req.question)
    except Exception:
        logger.exception("What-if failed")
        raise HTTPException(status_code=502, detail="The AI explanation service failed. Please try again.")
    return {"order_item_id": req.order_item_id, "risk_type": req.risk_type,
            "question": req.question, "answer": result["text"], "cached": result["cached"]}

# ---------------- Dashboard ----------------
@router.get("/summary", response_model=Summary, tags=["Dashboard"])
def get_summary():
    return _clean(queries.summary())


@router.get("/filters", response_model=FilterOptions, tags=["Dashboard"])
def get_filters():
    return queries.filter_options()


@router.get("/orders/risky", response_model=RiskTable, tags=["Dashboard"])
def risky_orders(
    risk_type: Literal["delay", "shortage", "both"] = "both",
    risk_level: Literal["Low", "Medium", "High"] = "High",
    shipping_mode: Optional[str] = None,
    region: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    total, rows = queries.risky_orders(risk_type, risk_level, shipping_mode, region, limit, offset)
    return {"total": total, "limit": limit, "offset": offset, "rows": [_clean(r) for r in rows]}


@router.get("/charts/delay-by-mode", response_model=list[ModeStat], tags=["Dashboard"])
def chart_delay_by_mode():
    return [_clean(r) for r in queries.delay_by_mode().to_dict("records")]


@router.get("/charts/shortage-by-category", response_model=list[CategoryStat], tags=["Dashboard"])
def chart_shortage_by_category(limit: int = Query(10, ge=1, le=30)):
    return [_clean(r) for r in queries.shortage_by_category(limit).to_dict("records")]