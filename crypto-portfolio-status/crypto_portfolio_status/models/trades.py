from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from pydantic import BaseModel

from logging import getLogger

logger = getLogger(__name__)

class TradeType(StrEnum):
    """Type of trades."""
    BUY = "buy"
    SELL = "sell"
              

class Trade(BaseModel):
    type: TradeType
    token: str
    amount: float
    price: float
    ts: datetime
    amount_eur: float
    fee: float
    
    @classmethod
    def from_transaction(cls, transaction: dict):
        if transaction['type'] == TradeType.BUY:
            return cls(
                type=TradeType.BUY,
                token=transaction['receivedCurrency'],
                amount=transaction['receivedAmount'],
                price=transaction['priceAmount'],
                ts=datetime.fromisoformat(transaction['executedAt']),
                amount_eur= -(float(transaction['sentAmount']) + float(transaction['feesAmount'])),
                fee=transaction['feesAmount'],
            )
        return cls(
            type=TradeType.SELL,
            token=transaction['sentCurrency'],
            amount=transaction['sentAmount'],
            price=transaction['priceAmount'],
            ts=datetime.fromisoformat(transaction['executedAt']),
            amount_eur=transaction['receivedAmount'],
            fee=transaction['feesAmount'],
        )

