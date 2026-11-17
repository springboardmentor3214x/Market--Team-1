"""User preferences: preferred stock market and default analysis period.

The user id always comes from the verified JWT (never from the request), so a
user can only read or change their own preferences.
"""
from fastapi import APIRouter, Depends, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import User, UserPreference
from app.schemas import (
    DEFAULT_MARKET,
    DEFAULT_PERIOD,
    PreferenceOut,
    PreferenceUpdate,
)

router = APIRouter(prefix="/preferences", tags=["User Preferences"])


def _get_pref(db: Session, user: User) -> UserPreference | None:
    return db.scalar(select(UserPreference).where(UserPreference.user_id == user.id))


@router.get("", response_model=PreferenceOut)
def get_preferences(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    """Return saved preferences, or the defaults if the user never saved any."""
    pref = _get_pref(db, current_user)
    if pref is None:
        return PreferenceOut(
            preferred_market=DEFAULT_MARKET,
            analysis_period=DEFAULT_PERIOD,
            updated_at=None,
            is_default=True,
        )
    return PreferenceOut(
        preferred_market=pref.preferred_market,
        analysis_period=pref.analysis_period,
        updated_at=pref.updated_at,
        is_default=False,
    )


@router.put("", response_model=PreferenceOut)
def save_preferences(
    payload: PreferenceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create the preference row if missing, otherwise update it (upsert)."""
    pref = _get_pref(db, current_user)
    if pref is None:
        pref = UserPreference(user_id=current_user.id)
        db.add(pref)
    pref.preferred_market = payload.preferred_market
    pref.analysis_period = payload.analysis_period
    db.commit()
    db.refresh(pref)
    return PreferenceOut(
        preferred_market=pref.preferred_market,
        analysis_period=pref.analysis_period,
        updated_at=pref.updated_at,
        is_default=False,
    )


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
def reset_preferences(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    """Delete saved preferences; GET will return the defaults again."""
    pref = _get_pref(db, current_user)
    if pref is not None:
        db.delete(pref)
        db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
