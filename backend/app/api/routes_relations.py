"""
API Router for Metamorphic Relations Catalog, Suggestions, and Custom Relations.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database.session import get_db
from ..schemas.pydantic_models import (
    RelationDetail,
    CreateCustomRelationRequest,
    SuggestRequest,
    SuggestResponse,
)
from ..services.relation_service import (
    list_relations,
    get_relation_by_id,
    create_custom_relation,
)
from ..services.suggester_service import suggest_relations_for_target

router = APIRouter(prefix="/api/relations", tags=["Relations Catalog & Suggestions"])


@router.get("", response_model=List[RelationDetail])
def get_all_relations(db: Session = Depends(get_db)):
    """
    Returns the comprehensive catalog of built-in and user-defined metamorphic relations.
    """
    return list_relations(db=db)


@router.get("/{relation_id}", response_model=RelationDetail)
def get_relation(relation_id: str, db: Session = Depends(get_db)):
    """
    Retrieves metadata, mathematical formula, and constraints for a specific relation.
    """
    rel = get_relation_by_id(relation_id=relation_id, db=db)
    if not rel:
        raise HTTPException(status_code=404, detail="Relation not found")
    return rel


@router.post("/custom", response_model=RelationDetail)
def add_custom_relation(request: CreateCustomRelationRequest, db: Session = Depends(get_db)):
    """
    Registers and persists a new custom metamorphic relation in the database.
    """
    rel_record = create_custom_relation(
        db=db,
        relation_id=request.relation_id,
        name=request.name,
        description=request.description,
        category=request.category,
        formula=request.formula,
    )
    return {
        "relation_id": rel_record.relation_id,
        "name": rel_record.name,
        "description": rel_record.description,
        "category": rel_record.category,
        "formula": rel_record.formula,
        "is_custom": True,
    }


@router.post("/suggest", response_model=SuggestResponse)
def suggest_relations(request: SuggestRequest):
    """
    Performs AST static inspection on the supplied code or preset to recommend candidate relations.
    """
    try:
        results = suggest_relations_for_target(
            category=request.category,
            variant=request.variant,
            custom_code=request.code,
        )
        return results
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"AST analysis failed: {str(e)}")
