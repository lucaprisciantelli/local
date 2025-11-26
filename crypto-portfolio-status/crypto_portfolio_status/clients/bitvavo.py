import hashlib
import hmac
import json
import requests
import time
from datetime import datetime

from models import Trade, Ticker

class BitvavoRestClient:
    """Client to interact with the Bitvavo REST API."""
    def __init__(self, api_key: str, api_secret: str, access_window: int = 10000):
        self.api_key = api_key
        self.api_secret = api_secret
        self.access_window = access_window
        self.base = 'https://api.bitvavo.com/v2'

    def get_market_ticker(self, token: str)-> Ticker:
        response = self.private_request(method='GET', endpoint='/ticker/book', body={'market': f'{token}-EUR'})
        return Ticker(
            buy_price=response['ask'],
            sell_price=response['bid'],
        )

    def get_balance(self)-> list[dict]:
        return self.private_request(method='GET', endpoint='/balance')

    def get_transaction_history(self, from_ts: datetime | None = None, to_ts: datetime | None = None, types: list[str] | None = None)-> list[Trade]:
        body = {'maxItems': 100, 'page': 1}
        if from_ts:
            body['fromDate'] = int(from_ts.timestamp() * 1000)
        if to_ts:
            body['toDate'] = int(to_ts.timestamp() * 1000)
        # paginate
        last_page = False
        data = []
        while not last_page:
            batch = self.private_request(method='GET', endpoint='/account/history', body=body)
            if batch['totalPages'] == batch['currentPage']:
                last_page = True
            else:
                body['page'] += 1
            data.extend(batch['items'])
        # filter by types
        if types:
            data = [transaction for transaction in data if transaction['type'] in types]
        return [Trade.from_transaction(transaction) for transaction in data]

    def private_request(self, endpoint: str, body: dict | None = None, method: str = 'GET', data: dict | None = None):
        """
        Create the headers to authenticate your request, then make the call to Bitvavo API.
        :param endpoint: the endpoint you are calling. For example, `/order`.
        :param body: for GET requests, this can be an empty string. For all other methods, a string
                     representation of the call body.
        :param method: the HTTP method of the request.
        :param params: the parameters of the request.
        """
        now = int(time.time() * 1000)
        sig = self.create_signature(now, method, endpoint, body)
        url = self.base + endpoint
        headers = {
            'Accept': 'application/json',
            'bitvavo-access-key': self.api_key,
            'bitvavo-access-signature': sig,
            'bitvavo-access-timestamp': str(now),
            'bitvavo-access-window': str(self.access_window),
        }
        r = requests.request(method=method, url=url, headers=headers, json=body, data=data)
        r.raise_for_status()
        parsed_request = r.json()
        return parsed_request

    def create_signature(self, timestamp: int, method: str, url: str, body: dict | None):
        """
        Create a hashed code to authenticate requests to Bitvavo API.
        :param timestamp: a unix timestamp showing the current time.
        :param method: the HTTP method of the request.
        :param url: the endpoint you are calling. For example, `/order`.
        :param body: for GET requests, this can be an empty string. For all other methods, a string
                     representation of the call body. For example, for a call to `/order`:
                     `{"market":"BTC-EUR","side":"buy","price":"5000","amount":"1.23", "orderType":"limit"}`.
        """
        string = str(timestamp) + method + '/v2' + url
        if (body is not None) and (len(body.keys()) != 0):
            string += json.dumps(body, separators=(',', ':'))
        signature = hmac.new(self.api_secret.encode('utf-8'), string.encode('utf-8'), hashlib.sha256).hexdigest()
        return signature