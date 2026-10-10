"""
Service for managing default and custom Metamorphic Relations.
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from metaoracle.relations.registry import default_registry
from metaoracle.relations.base import MetamorphicRelation
from ..database.models import CustomRelation


def list_relations(db: Optional[Session] = None) -> List[dict]:
    """
    Returns combined list of default catalog relations and user-defined custom relations.
    """
    results = []
    # 1. Built-in catalog relations
    for rel in default_registry.list_all():
        results.append({
            "relation_id": rel.relation_id,
            "name": rel.name,
            "description": rel.description,
            "category": rel.category,
            "formula": getattr(rel, "formula", ""),
            "domain_constraints": getattr(rel, "domain_constraints", ""),
            "is_custom": False,
        })

    # 2. Custom relations from database
    if db:
        custom_rels = db.query(CustomRelation).all()
        for cr in custom_rels:
            # Check if not already in results
            if not any(r["relation_id"] == cr.relation_id for r in results):
                results.append({
                    "relation_id": cr.relation_id,
                    "name": cr.name,
                    "description": cr.description,
                    "category": cr.category,
                    "formula": cr.formula,
                    "domain_constraints": "User-defined custom relation constraints",
                    "is_custom": True,
                })

    return results


def get_relation_by_id(relation_id: str, db: Optional[Session] = None) -> Optional[dict]:
    """Retrieves a single relation by ID."""
    rel = default_registry.get(relation_id)
    if rel:
        return {
            "relation_id": rel.relation_id,
            "name": rel.name,
            "description": rel.description,
            "category": rel.category,
            "formula": getattr(rel, "formula", ""),
            "domain_constraints": getattr(rel, "domain_constraints", ""),
            "is_custom": False,
        }
    if db:
        cr = db.query(CustomRelation).filter(CustomRelation.relation_id == relation_id).first()
        if cr:
            return {
                "relation_id": cr.relation_id,
                "name": cr.name,
                "description": cr.description,
                "category": cr.category,
                "formula": cr.formula,
                "domain_constraints": "User-defined custom relation constraints",
                "is_custom": True,
            }
    return None


def create_custom_relation(
    db: Session,
    relation_id: str,
    name: str,
    description: str,
    category: str,
    formula: str,
) -> CustomRelation:
    """Creates and persists a new custom relation."""
    # Check if exists
    existing = db.query(CustomRelation).filter(CustomRelation.relation_id == relation_id).first()
    if existing:
        existing.name = name
        existing.description = description
        existing.category = category
        existing.formula = formula
        db.commit()
        db.refresh(existing)
        return existing

    new_rel = CustomRelation(
        relation_id=relation_id,
        name=name,
        description=description,
        category=category,
        formula=formula,
    )
    db.add(new_rel)
    db.commit()
    db.refresh(new_rel)
    return new_rel
