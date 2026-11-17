"""User-specific research history.

Every query is filtered by the user id taken from the verified JWT, never from
a request parameter, so one user can never read or change another user's data.
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import delete, desc, func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import ResearchHistory, User, UserPreference
from app.schemas import HistoryCreate, HistoryList, HistoryOut

router = APIRouter(prefix="/history", tags=["Research History"])


def _get_owned_or_404(db: Session, user: User, item_id: int) -> ResearchHistory:
    item = db.scalar(
        select(ResearchHistory).where(
            ResearchHistory.id == item_id, ResearchHistory.user_id == user.id
        )
    )
    if item is None:  # same response whether it doesn't exist or belongs to someone else
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Research entry not found")
    return item


@router.post("", response_model=HistoryOut, status_code=status.HTTP_201_CREATED)
def create_history(
    payload: HistoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    data = payload.model_dump()
    # If the request omits market/period, use the user's saved preferences (if any).
    pref = db.scalar(
        select(UserPreference).where(UserPreference.user_id == current_user.id)
    )
    if pref is not None:
        if not data.get("market"):
            data["market"] = pref.preferred_market
        if not data.get("analysis_period"):
            data["analysis_period"] = pref.analysis_period
    item = ResearchHistory(user_id=current_user.id, **data)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.get("", response_model=HistoryList)
def list_history(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    q: Optional[str] = Query(None, max_length=100, description="Search in the query text"),
    market: Optional[str] = Query(None, max_length=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = select(ResearchHistory).where(ResearchHistory.user_id == current_user.id)
    if q:
        stmt = stmt.where(ResearchHistory.query.ilike(f"%{q}%"))
    if market:
        stmt = stmt.where(func.lower(ResearchHistory.market) == market.lower())

    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    items = db.scalars(
        stmt.order_by(desc(ResearchHistory.created_at), desc(ResearchHistory.id))
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return HistoryList(items=items, total=total, page=page, page_size=page_size)


@router.get("/{item_id}", response_model=HistoryOut)
def get_history_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return _get_owned_or_404(db, current_user, item_id)


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_history_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    item = _get_owned_or_404(db, current_user, item_id)
    db.delete(item)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
def clear_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete ALL of the logged-in user's research history."""
    db.execute(delete(ResearchHistory).where(ResearchHistory.user_id == current_user.id))
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
