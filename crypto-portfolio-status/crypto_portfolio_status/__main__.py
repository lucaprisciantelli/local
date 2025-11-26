from clients.bitvavo import BitvavoRestClient
from dotenv import dotenv_values
from utils import get_portfolio
from logging import getLogger

logger = getLogger(__name__)

def main():
    config = dotenv_values()
    bitvavo = BitvavoRestClient(
        api_key=config["B_API_KEY"],
        api_secret=config["B_API_SECRET"],
    )
    portfolio = get_portfolio(bitvavo)
    logger.info(f"Portfolio Investment: {portfolio.investment}")
    logger.info(f"Portfolio Closed Revenue: {portfolio.closed_revenue}")
    logger.info(f"Portfolio Open Revenue: {portfolio.open_revenue}")
    logger.info("Asset Details:")
    for asset in portfolio.assets:
        logger.info(f"Asset: {asset.token}")
        logger.info(f"Asset Investment: {asset.investment}")
        logger.info(f"Asset Closed Revenue: {asset.closed_revenue}")
        logger.info(f"Asset Open Revenue: {asset.open_revenue}")

    
if __name__ == "__main__":
    main()