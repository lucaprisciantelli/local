from __future__ import annotations
from pydantic import BaseModel
from datetime import datetime
from dataclasses import dataclass

class Ticker(BaseModel):
    """Ticker for a given token."""
    buy_price: float
    sell_price: float


@dataclass
class Position:
    """Base class for positions."""
    amount: float
    price: float

    @property
    def investment(self)-> float:
        """Investment of the position."""
        return self.amount * self.price

@dataclass
class ClosedPosition(Position):
    """Closed position."""
    close_ts: datetime
    close_price: float
    open_ts: datetime | None = None

    @property
    def revenue(self)-> float:
        """Revenue of the closed position."""
        return self.amount * (self.close_price - self.price)

@dataclass
class OpenPosition(Position):
    """Open position."""
    open_ts: datetime

    def get_unresolved_revenue(self, current_price: float)-> float:
        """Get the unresolved revenue of the position."""
        return self.amount * (current_price - self.price)
    
    def get_price_relative_distance(self, current_price: float)-> float:
        """Get the price relative distance of the position."""
        return (self.price - current_price) / current_price

    def close(self, close_price: float, close_ts: datetime)-> ClosedPosition:
        """Close the position."""
        return ClosedPosition(
            amount=self.amount,
            price=self.price,
            close_ts=close_ts,
            close_price=close_price,
            open_ts=self.open_ts,
        )
    
    def partial_close(self, close_price: float, close_ts: datetime, close_amount: float)-> tuple[OpenPosition, ClosedPosition]:
        """Close the position partially."""
        if close_amount > self.amount:
            raise ValueError(f"Amount {close_amount} is greater than the open position amount {self.amount}")
        return OpenPosition(
            amount=self.amount - close_amount, 
            price=self.price, 
            open_ts=self.open_ts
        ), ClosedPosition(
            amount=close_amount,
            price=close_price,
            close_ts=close_ts,
            close_price=close_price,
            open_ts=self.open_ts,
        )