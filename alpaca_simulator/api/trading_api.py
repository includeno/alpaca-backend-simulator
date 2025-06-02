from fastapi import FastAPI, HTTPException, status as http_status
import uvicorn
from typing import List, Optional, Any, Dict # Added Dict
from urllib.parse import urlparse
from alpaca_simulator.domain.trading.models import OrderRequest
from alpaca_simulator.domain.trading import service as trading_service
from alpaca_simulator.common.config import MOCK_API_BASE_URL

app = FastAPI()

@app.get('/v2/account')
async def get_account_info_endpoint():
    return trading_service.get_account_information()

@app.get('/v2/positions')
async def list_positions_endpoint():
    return trading_service.list_all_positions()

@app.post('/v2/orders', status_code=http_status.HTTP_200_OK)
async def place_order_endpoint(order_request: OrderRequest):
    return trading_service.place_new_order(order_request)

@app.get('/v2/orders')
async def list_orders_endpoint(status: Optional[str] = None, limit: Optional[int] = None,
                               after: Optional[str] = None, until: Optional[str] = None,
                               direction: Optional[str] = 'desc', nested: Optional[bool] = False, # nested not used by service yet
                               symbols: Optional[str] = None):
    return trading_service.list_orders(status, limit, after, until, direction, symbols)

@app.get('/v2/orders/{order_id}')
async def get_order_by_id_endpoint(order_id: str):
    order = trading_service.get_order(order_id)
    if order:
        return order
    raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail='Order not found')

if __name__ == "__main__":
    parsed_url = urlparse(MOCK_API_BASE_URL)
    host = parsed_url.hostname if parsed_url.hostname else "localhost"
    port = parsed_url.port if parsed_url.port else 8000
    uvicorn.run(app, host=host, port=port)
