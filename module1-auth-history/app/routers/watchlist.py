
"""JWT-protected saved stocks and watchlist endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import User, Watchlist
from app.schemas import WatchlistCreate, WatchlistOut


router = APIRouter(
    prefix="/watchlist",
    tags=["Watchlist"],
)


@router.post(
    "/",
    response_model=WatchlistOut,
    status_code=status.HTTP_201_CREATED,
)
def add_stock(
    stock: WatchlistCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Add a stock to the logged-in user's watchlist."""

    existing_stock = db.query(Watchlist).filter(
        Watchlist.user_id == current_user.id,
        Watchlist.stock_symbol == stock.stock_symbol,
        Watchlist.market == stock.market,
    ).first()

    if existing_stock:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Stock already exists in your watchlist",
        )

    new_stock = Watchlist(
        user_id=current_user.id,
        stock_symbol=stock.stock_symbol,
        market=stock.market,
    )

    try:
        db.add(new_stock)
        db.commit()
        db.refresh(new_stock)

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Stock already exists in your watchlist",
        )

    return new_stock


@router.get("/", response_model=list[WatchlistOut])
def get_watchlist(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve the logged-in user's saved stocks."""

    return (
        db.query(Watchlist)
        .filter(Watchlist.user_id == current_user.id)
        .order_by(Watchlist.created_at.desc())
        .all()
    )


@router.delete("/{stock_id}")
def delete_stock(
    stock_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Remove a stock from the logged-in user's watchlist."""

    stock = db.query(Watchlist).filter(
        Watchlist.id == stock_id,
        Watchlist.user_id == current_user.id,
    ).first()

    if not stock:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stock not found",
        )

    db.delete(stock)
    db.commit()

    return {"message": "Stock removed successfully"}
