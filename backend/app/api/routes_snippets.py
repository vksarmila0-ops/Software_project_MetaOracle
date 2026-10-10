"""
API Router for saving and loading custom Python code snippets.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database.session import get_db
from ..schemas.pydantic_models import SnippetCreateRequest, SnippetResponse
from ..services.snippet_service import (
    list_snippets,
    get_snippet,
    create_snippet,
    delete_snippet,
)

router = APIRouter(prefix="/api/snippets", tags=["Code Snippets"])


@router.get("", response_model=List[SnippetResponse])
def get_snippets(db: Session = Depends(get_db)):
    """
    Returns all saved custom Python code snippets.
    """
    snippets = list_snippets(db)
    return [s.to_dict() for s in snippets]


@router.post("", response_model=SnippetResponse)
def add_snippet(request: SnippetCreateRequest, db: Session = Depends(get_db)):
    """
    Saves a new code snippet to the database.
    """
    s = create_snippet(
        db=db,
        title=request.title,
        code=request.code,
        category=request.category,
        input_type=request.input_type,
    )
    return s.to_dict()


@router.get("/{snippet_id}", response_model=SnippetResponse)
def get_snippet_by_id(snippet_id: int, db: Session = Depends(get_db)):
    """
    Retrieves a single saved snippet by ID.
    """
    s = get_snippet(db=db, snippet_id=snippet_id)
    if not s:
        raise HTTPException(status_code=404, detail="Snippet not found")
    return s.to_dict()


@router.delete("/{snippet_id}")
def remove_snippet(snippet_id: int, db: Session = Depends(get_db)):
    """
    Deletes a snippet by ID.
    """
    success = delete_snippet(db=db, snippet_id=snippet_id)
    if not success:
        raise HTTPException(status_code=404, detail="Snippet not found")
    return {"message": "Snippet deleted", "id": snippet_id}
