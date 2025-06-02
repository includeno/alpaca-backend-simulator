import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
from alpaca_simulator.domain.trading.models import OrderRequest
from alpaca_simulator.data_access import in_memory_trading_repository as repo

# --- Account Service ---
def get_account_information() -> Dict[str, Any]:
    account_data = repo.get_account_data()
    positions = repo.get_all_positions()
    current_portfolio_value = float(account_data.get('cash', '0.00'))
    for pos in positions:
        current_portfolio_value += float(pos.get('market_value', '0.00'))
    account_data['portfolio_value'] = str(current_portfolio_value)
    account_data['equity'] = str(current_portfolio_value) # Simplified equity
    repo.update_account_data(account_data) # Persist updates
    return account_data

# --- Positions Service ---
def list_all_positions() -> List[Dict[str, Any]]:
    live_positions = [p for p in repo.get_all_positions() if float(p.get('qty', '0')) != 0]
    return live_positions

# --- Orders Service ---
def place_new_order(order_request: OrderRequest) -> Dict[str, Any]:
    order_id = str(uuid.uuid4())
    client_order_id = order_request.client_order_id or f'mock_client_{str(uuid.uuid4())[:12]}'
    now_utc = datetime.now(timezone.utc)
    now_iso = now_utc.isoformat(timespec='milliseconds').replace('+00:00', 'Z')

    order_data = {
        'id': order_id,
        'client_order_id': client_order_id,
        'created_at': now_iso,
        'updated_at': now_iso,
        'submitted_at': now_iso,
        'filled_at': None, 'expired_at': None, 'canceled_at': None, 'failed_at': None,
        'replaced_at': None, 'replaced_by': None, 'replaces': None,
        'asset_id': str(uuid.uuid4()),
        'symbol': order_request.symbol.upper(),
        'asset_class': 'us_equity',
        'notional': None,
        'qty': str(order_request.qty),
        'filled_qty': '0',
        'filled_avg_price': None,
        'order_class': '',
        'order_type': order_request.type,
        'type': order_request.type,
        'side': order_request.side,
        'time_in_force': order_request.time_in_force,
        'limit_price': str(order_request.limit_price) if order_request.limit_price is not None else None,
        'stop_price': str(order_request.stop_price) if order_request.stop_price is not None else None,
        'status': 'accepted',
        'extended_hours': False, 'legs': None, 'trail_percent': None, 'trail_price': None, 'hwm': None
    }

    if order_request.type == 'market':
        order_data['status'] = 'filled'
        order_data['filled_at'] = now_iso
        order_data['filled_qty'] = str(order_request.qty)

        mock_fill_price = 0.0
        sym_upper = order_request.symbol.upper()
        if sym_upper == 'AAPL': mock_fill_price = 150.0
        elif sym_upper == 'MSFT': mock_fill_price = 300.0
        elif sym_upper == 'TSLA': mock_fill_price = 250.0
        elif sym_upper == 'GOOG': mock_fill_price = 140.0
        else: mock_fill_price = 50.0
        order_data['filled_avg_price'] = str(mock_fill_price)

        # Update positions (simplified logic, needs careful refactoring from original)
        # This part interacts heavily with account and position data in the repository
        account_data = repo.get_account_data()
        positions = repo.get_all_positions()
        found_position = False
        for pos_idx, pos in enumerate(positions): # Changed to enumerate(positions)
            if pos['symbol'] == sym_upper:
                current_qty = float(pos['qty'])
                current_avg_entry = float(pos['avg_entry_price'])
                current_cost_basis = float(pos.get('cost_basis', str(current_qty * current_avg_entry)))
                order_value = order_request.qty * mock_fill_price

                if order_request.side == 'buy':
                    new_qty = current_qty + order_request.qty
                    new_cost_basis = current_cost_basis + order_value
                    pos['avg_entry_price'] = str(new_cost_basis / new_qty if new_qty != 0 else 0)
                    pos['qty'] = str(new_qty)
                    pos['cost_basis'] = str(new_cost_basis)
                    pos['side'] = 'long'
                else: # sell
                    new_qty = current_qty - order_request.qty
                    sold_cost_basis_reduction = order_request.qty * current_avg_entry
                    pos['cost_basis'] = str(current_cost_basis - sold_cost_basis_reduction)
                    pos['qty'] = str(new_qty)
                    if new_qty == 0: pos['avg_entry_price'] = '0'

                pos['market_value'] = str(float(pos['qty']) * mock_fill_price)
                pos['current_price'] = str(mock_fill_price)
                if float(pos['qty']) != 0:
                    pos['unrealized_pl'] = str((mock_fill_price - float(pos['avg_entry_price'])) * float(pos['qty']))
                else:
                    pos['unrealized_pl'] = '0.00'
                # repo.update_position(sym_upper, pos) # Persist changes to this position
                # Instead of direct update_position, modify the list and then save all positions or rely on mock_positions_data being mutable
                positions[pos_idx] = pos # Update the position in the list
                found_position = True
                break

        # If the list `positions` is a copy, this change won't persist unless we save it back.
        # The current repo.update_position takes symbol and a dict of changes.
        # For simplicity, if using global mock_positions_data directly in repo, this loop already modified it.
        # If repo functions return copies, then we'd need a repo.save_all_positions(positions) or similar.
        # Given current repo.update_position signature, it's better to call it inside the loop for the specific position.
        # Reverting to calling update_position inside the loop for clarity of intent.
        # This was present in the prompt's code, so re-adding it.
        if found_position:
             # Find the updated position again to pass to repo.update_position, or ensure pos is the latest dict
             for p_to_update in positions:
                 if p_to_update['symbol'] == sym_upper:
                      repo.update_position(sym_upper, p_to_update)
                      break


        if not found_position and order_request.side == 'buy':
            new_position_cost = order_request.qty * mock_fill_price
            new_pos_data = {
                'asset_id': str(uuid.uuid4()), 'symbol': sym_upper, 'exchange': 'NASDAQ',
                'asset_class': 'us_equity', 'avg_entry_price': str(mock_fill_price),
                'qty': str(order_request.qty), 'side': 'long', 'market_value': str(new_position_cost),
                'cost_basis': str(new_position_cost), 'unrealized_pl': '0.00',
                'unrealized_plpc': '0.0000', 'unrealized_intraday_pl': '0.00',
                'unrealized_intraday_plpc': '0.0000', 'current_price': str(mock_fill_price),
                'lastday_price': str(mock_fill_price - 1.0), 'change_today': '0.0000'
            }
            repo.add_position(new_pos_data)

        # Update cash and buying power in account_data
        current_cash = float(account_data['cash'])
        order_total_value = order_request.qty * mock_fill_price
        if order_request.side == 'buy':
            account_data['cash'] = str(current_cash - order_total_value)
        else: # sell
            account_data['cash'] = str(current_cash + order_total_value)
        account_data['buying_power'] = account_data['cash'] # Simplified
        account_data['regt_buying_power'] = account_data['cash']
        account_data['non_marginable_buying_power'] = account_data['cash']

        # Update portfolio value and equity
        current_portfolio_value = float(account_data['cash'])
        current_long_market_value = 0.0
        all_current_positions = repo.get_all_positions() # Re-fetch for latest state
        for p_val_calc in all_current_positions:
            if float(p_val_calc.get('qty', '0')) > 0:
                p_market_val = float(p_val_calc.get('qty')) * float(p_val_calc.get('current_price', str(mock_fill_price)))
                current_portfolio_value += p_market_val
                current_long_market_value += p_market_val
        account_data['portfolio_value'] = str(current_portfolio_value)
        account_data['equity'] = str(current_portfolio_value)
        account_data['long_market_value'] = str(current_long_market_value)
        repo.update_account_data(account_data) # Persist final account updates

    elif order_request.type == 'limit':
        order_data['status'] = 'new'

    repo.save_order(order_data)
    return order_data

def list_orders(status: Optional[str], limit: Optional[int], after: Optional[str], until: Optional[str], direction: Optional[str], symbols: Optional[str]) -> List[Dict[str, Any]]:
    orders_to_return = repo.get_all_orders()
    if status and status != 'all':
        statuses = status.split(',')
        orders_to_return = [o for o in orders_to_return if o['status'] in statuses]
    if symbols:
        symbol_list = [s.strip().upper() for s in symbols.split(',')]
        orders_to_return = [o for o in orders_to_return if o['symbol'] in symbol_list]
    if after:
        orders_to_return = [o for o in orders_to_return if o['submitted_at'] > after]
    if until:
        orders_to_return = [o for o in orders_to_return if o['submitted_at'] < until]
    orders_to_return.sort(key=lambda x: x['submitted_at'], reverse=(direction == 'desc'))
    if limit:
        orders_to_return = orders_to_return[:limit]
    return orders_to_return

def get_order(order_id: str) -> Optional[Dict[str, Any]]:
    order = repo.get_order_by_id(order_id)
    if not order:
        order = repo.get_order_by_client_order_id(order_id) # Check by client_order_id as fallback
    return order
