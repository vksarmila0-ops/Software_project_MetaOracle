"""
Service for managing saved user code snippets.
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from ..database.models import CodeSnippet


def list_snippets(db: Session) -> List[CodeSnippet]:
    """Returns all saved snippets ordered by updated_at."""
    return db.query(CodeSnippet).order_by(CodeSnippet.updated_at.desc()).all()


def get_snippet(db: Session, snippet_id: int) -> Optional[CodeSnippet]:
    """Retrieves a snippet by ID."""
    return db.query(CodeSnippet).filter(CodeSnippet.id == snippet_id).first()


def create_snippet(
    db: Session,
    title: str,
    code: str,
    category: str = "Custom",
    input_type: str = "list",
) -> CodeSnippet:
    """Creates a new code snippet."""
    snippet = CodeSnippet(
        title=title,
        code=code,
        category=category,
        input_type=input_type,
    )
    db.add(snippet)
    db.commit()
    db.refresh(snippet)
    return snippet


def delete_snippet(db: Session, snippet_id: int) -> bool:
    """Deletes a snippet by ID."""
    snippet = db.query(CodeSnippet).filter(CodeSnippet.id == snippet_id).first()
    if not snippet:
        return False
    db.delete(snippet)
    db.commit()
    return True
