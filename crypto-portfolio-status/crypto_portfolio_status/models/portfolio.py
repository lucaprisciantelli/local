from dataclasses import dataclass, field
from datetime import datetime
from models.positions import OpenPosition, ClosedPosition, Ticker
from models.trades import Trade, TradeType

from logging import getLogger

logger = getLogger(__name__)

@dataclass
class Asset:
    """Asset in the portfolio."""
    token: str
    amount: float
    ticker: Ticker
    fees: float = 0.0
    _closed_positions: list[ClosedPosition] = field(init=False, default_factory=list)
    _open_positions: list[OpenPosition] = field(init=False, default_factory=list)
    
    @property
    def investment(self)-> float:
        """Investment of the asset."""
        return self.amount * self.ticker.sell_price
    
    @property
    def open_positions(self)-> list[OpenPosition]:
        """Open positions of the asset."""
        return self._open_positions
    
    @property
    def closed_positions(self)-> list[ClosedPosition]:
        """Closed positions of the asset."""
        return self._closed_positions

    def _ensure_time_consistency(self, trade_ts: datetime):
        """Ensure time consistency of the trades."""
        if self.open_positions:
            if self.open_positions[-1].open_ts > trade_ts:
                raise ValueError(f"Time consistency error: Trade {trade_ts} is older than the last open position {self.open_positions[-1].open_ts}")

    def add_trade(self, trade: Trade):
        """Add a trade to the asset."""
        self._ensure_time_consistency(trade.ts)
        self.fees += trade.fee
        if trade.type == TradeType.BUY:
            self.add_buy_trade(trade)
        else:
            self.add_sell_trade(trade)

    def add_buy_trade(self, trade: Trade):
        """Add a buy trade to the asset."""
        self._open_positions.append(
            OpenPosition(
                amount=trade.amount, 
                price=trade.price, 
                open_ts=trade.ts,
            )
        )
    
    def add_sell_trade(self, trade: Trade):
        """Add a sell trade to the asset."""
        price_sorted_open_positions = sorted(self.open_positions, key=lambda x: x.price)
        new_closed_positions = []
        remaining_open_positions = []
        closed_amount = 0
        for open_position in price_sorted_open_positions:
            unclosed_amount = trade.amount - closed_amount
            if unclosed_amount > open_position.amount:
                closed_position = open_position.close(trade.price, trade.ts)
                closed_amount += closed_position.amount
                new_closed_positions.append(closed_position)
            elif unclosed_amount > 0:
                remaining_open_position, closed_position = open_position.partial_close(trade.price, trade.ts, close_amount=unclosed_amount)
                remaining_open_positions.append(remaining_open_position)
                new_closed_positions.append(closed_position)
                closed_amount += closed_position.amount
            else:
                remaining_open_positions.append(open_position)
        
        if closed_amount < trade.amount:
            difference = trade.amount - closed_amount
            logger.info(f"Difference of {difference} in {self.token} found, allocating it as a close staking position")
            self._closed_positions.append(
                ClosedPosition(
                    amount=difference,
                    price=0,
                    close_ts=trade.ts,
                    close_price=trade.price,
                )
            )
        
        self._closed_positions += new_closed_positions
        self._open_positions = remaining_open_positions
    
    @property
    def closed_revenue(self)-> float:
        """Closed revenue of the asset."""
        return sum(closed_position.revenue for closed_position in self.closed_positions) - self.fees
    
    @property
    def open_revenue(self)-> float:
        """Open revenue of the asset."""
        return sum(open_position.get_unresolved_revenue(self.ticker.sell_price) 
            for open_position in self.open_positions)
    
    @property
    def relative_open_positions(self)-> list[dict]:
        """Relative open positions of the asset."""
        return [
            {
                'token': self.token,
                'amount': open_position.amount,
                'price': open_position.price,
                'investment': open_position.investment,
                'open_ts': open_position.open_ts,
                'price_distance': open_position.get_price_relative_distance(self.ticker.sell_price),
                'unresolved_revenue': open_position.get_unresolved_revenue(self.ticker.sell_price),
            }
            for open_position in self.open_positions
        ]

@dataclass
class Portfolio:
    """Portfolio of assets."""
    assets: list[Asset]

    def assets_tokens(self)-> list[str]:
        """Tokens of the assets in the portfolio."""
        return [asset.token for asset in sorted(self.assets, key=lambda x: x.investment, reverse=True)]
    
    def get_asset_by_token(self, token: str)-> Asset:
        """Get the asset by token."""
        return next(asset for asset in self.assets if asset.token == token)

    
    @property
    def investment(self)-> float:
        """Investment of the portfolio."""
        return sum(asset.investment for asset in self.assets)
    
    @property
    def closed_revenue(self)-> float:
        """Closed revenue of the portfolio."""
        return sum(asset.closed_revenue for asset in self.assets)

    @property
    def open_revenue(self)-> float:
        """Open revenue of the portfolio."""
        return sum(asset.open_revenue for asset in self.assets)

    @property
    def open_positions(self)-> list[OpenPosition]:
        """Open positions of the portfolio."""
        return [position for asset in self.assets for position in asset.open_positions]
    
    @property
    def closed_positions(self)-> list[ClosedPosition]:
        """Closed positions of the portfolio."""
        return [position for asset in self.assets for position in asset.closed_positions]
    
    @property
    def relative_open_positions(self)-> list[dict]:
        """Relative open positions of the portfolio."""
        return [position for asset in self.assets for position in asset.relative_open_positions]