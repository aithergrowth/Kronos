"""Offline adapter reproduction using the repository's FakeIB/FakeApi only.

Does not connect to TWS, make network requests, or load credentials.
A successful run reproduces a known defect; it is not a passing safety test.
The injected terminal parent has 25,000 filled of 100,000 requested EURUSD units.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
spec = importlib.util.spec_from_file_location('repo_fake_ibkr', ROOT / 'tests/trader/test_ibkr.py')
helpers = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helpers)

from kronos_trader.config import Settings
from kronos_trader.core import Direction
from kronos_trader.execution.ibkr import IBKRBroker


class PartialCancelIB(helpers.FakeIB):
    def __init__(self, cancel_on_bracket_transmit=False):
        super().__init__()
        self.fill_mode = 'pending'
        self.cancel_on_bracket_transmit = cancel_on_bracket_transmit
        self.cancel_requests = []

    def set_partial_then_cancel(self):
        parent = next(t for t in self.trades if t.order.orderType == 'MKT')
        parent.orderStatus.status = 'Cancelled'
        parent.orderStatus.filled = 25000.0
        parent.orderStatus.remaining = 75000.0
        parent.orderStatus.avgFillPrice = 1.1002
        self.held['EURUSD'] = 25000.0

    def placeOrder(self, contract, order):
        trade = super().placeOrder(contract, order)
        if self.cancel_on_bracket_transmit and order.orderType == 'STP' and order.transmit:
            self.set_partial_then_cancel()
        return trade

    def cancelOrder(self, order):
        self.cancel_requests.append({'id': order.orderId, 'kind': order.orderType})
        super().cancelOrder(order)


def make(ib):
    broker = IBKRBroker(Settings(), ib=ib, api=helpers.FakeApi, connect=False)
    broker.params.fill_wait_seconds = 0
    return broker


def submit(broker):
    return broker.place_market_order(
        'EURUSD', Direction.LONG, 1.0, 1.0950, 1.1200, 1000.0, 0.0051, 4.0,
        price=1.1,
    )


def snapshot(broker):
    return {
        'held_units': dict(broker.ib.held),
        'tracked_position_ids': list(broker._positions),
        'tracked_order_ids': list(broker._orders),
        'child_cancel_requests': list(broker.ib.cancel_requests),
        'orders': [
            {
                'id': t.order.orderId,
                'kind': t.order.orderType,
                'requested_units': t.order.totalQuantity,
                'status': t.orderStatus.status,
                'filled_units': getattr(t.orderStatus, 'filled', None),
                'remaining_units': getattr(t.orderStatus, 'remaining', None),
                'avg_fill_price': t.orderStatus.avgFillPrice,
            }
            for t in broker.ib.trades
        ],
        'closed_trade_count': len(broker._closed),
        'fake_connection_opened': broker.ib.connected,
    }


immediate = make(PartialCancelIB(cancel_on_bracket_transmit=True))
try:
    submit(immediate)
except RuntimeError as exc:
    immediate_exception = str(exc)
else:
    raise AssertionError('expected the current adapter to reject the partially filled cancelled parent')
assert immediate.ib.held['EURUSD'] == 25000.0
assert not immediate._positions and not immediate._orders
assert {c['kind'] for c in immediate.ib.cancel_requests} == {'STP', 'LMT'}

deferred = make(PartialCancelIB())
position = submit(deferred)
assert position.status == 'pending'
deferred.ib.set_partial_then_cancel()
before = snapshot(deferred)
reported_open = deferred.open_positions()
after = snapshot(deferred)
assert reported_open == []
assert deferred.ib.held['EURUSD'] == 25000.0
assert not deferred._positions and not deferred._orders
assert {c['kind'] for c in deferred.ib.cancel_requests} == {'STP', 'LMT'}

print(json.dumps({
    'case_1_partial_cancel_before_submit_returns': {
        'exception': immediate_exception,
        'after': snapshot(immediate),
    },
    'case_2_partial_cancel_after_pending_return': {
        'before_reconciliation': before,
        'reported_open_positions_after_reconciliation': reported_open,
        'after_reconciliation': after,
    },
    'limitation': 'Injected fake TWS state establishes adapter behavior only; actual IBKR execution, status-event ordering and child order handling were not exercised.',
}, indent=2))
