from clients.bitvavo import BitvavoRestClient
from datetime import datetime, timedelta
from models import Asset, Portfolio, Trade
from collections import defaultdict

def get_portfolio(bitvavo: BitvavoRestClient)-> Portfolio:
    """Get the portfolio from the bitvavo client."""
    balance = bitvavo.get_balance()
    balance_map : dict[str, float] = {line['symbol']: float(line['available']) for line in balance}
    trades_map = get_trades_map(
        bitvavo.get_transaction_history(from_ts=datetime.now() - timedelta(days=3000), types=["buy", "sell"])
    )
    assets = []
    for token, token_trades in trades_map.items():
        ticker = bitvavo.get_market_ticker(token)
        asset = Asset(
            token=token,
            amount=balance_map.get(token, 0),
            ticker=ticker,
        )
        for trade in token_trades:
            asset.add_trade(trade)
        assets.append(asset)
    return Portfolio(assets=assets)

def update_portfolio(portfolio: Portfolio, bitvavo: BitvavoRestClient)-> None:
    for asset in portfolio.assets:
        ticker = bitvavo.get_market_ticker(asset.token)
        asset.ticker = ticker

def get_trades_map(trades: list[Trade]):
    trades_map : dict[str, list[Trade]] = defaultdict[str, list[Trade]](list)
    sorted_trades = sorted(trades, key=lambda x: x.ts)
    for trade in sorted_trades:
        trades_map[trade.token].append(trade)
    return trades_map
