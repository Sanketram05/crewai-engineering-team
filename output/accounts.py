# accounts.py

import datetime
from typing import Optional, Dict, List, Any

##########################
# Utility: get_share_price
##########################

def get_share_price(symbol: str) -> float:
    """Return current price for given symbol (test implementation)."""
    fixed_prices = {
        'AAPL': 150.0,
        'TSLA': 700.0,
        'GOOGL': 2800.0
    }
    return fixed_prices.get(symbol.upper(), 0.0)

##########################
# UserAccount
##########################

class UserAccount:
    def __init__(self, username: str):
        self.username: str = username
        self.initial_deposit: float = 0.0
        self.cash_balance: float = 0.0
        self.holdings: Dict[str, int] = {}  # symbol -> quantity
        self.transaction_history: List[Dict[str, Any]] = []

    def deposit(self, amount: float) -> None:
        if amount <= 0:
            raise ValueError("Deposit amount must be positive.")
        self.cash_balance += amount
        if self.initial_deposit == 0.0:
            self.initial_deposit = amount
        self.transaction_history.append({
            'type': 'deposit',
            'symbol': None,
            'quantity': amount,
            'price': None,
            'datetime': datetime.datetime.now().isoformat()
        })

    def can_withdraw(self, amount: float) -> bool:
        return amount > 0 and (self.cash_balance - amount) >= 0

    def withdraw(self, amount: float) -> bool:
        if amount <= 0:
            # Invalid amount
            return False
        if not self.can_withdraw(amount):
            return False
        self.cash_balance -= amount
        self.transaction_history.append({
            'type': 'withdraw',
            'symbol': None,
            'quantity': amount,
            'price': None,
            'datetime': datetime.datetime.now().isoformat()
        })
        return True

    def can_buy(self, symbol: str, quantity: int) -> bool:
        if quantity <= 0 or not symbol or not isinstance(quantity, int):
            return False
        price = get_share_price(symbol)
        total_cost = price * quantity
        return (total_cost <= self.cash_balance) and (price > 0)

    def buy_shares(self, symbol: str, quantity: int) -> bool:
        if quantity <= 0 or not symbol:
            return False
        price = get_share_price(symbol)
        total_cost = price * quantity
        if not self.can_buy(symbol, quantity):
            return False
        self.cash_balance -= total_cost
        self.holdings[symbol] = self.holdings.get(symbol, 0) + quantity
        self.transaction_history.append({
            'type': 'buy',
            'symbol': symbol,
            'quantity': quantity,
            'price': price,
            'datetime': datetime.datetime.now().isoformat()
        })
        return True

    def can_sell(self, symbol: str, quantity: int) -> bool:
        if quantity <= 0 or not symbol or not isinstance(quantity, int):
            return False
        return self.holdings.get(symbol, 0) >= quantity

    def sell_shares(self, symbol: str, quantity: int) -> bool:
        if quantity <= 0 or not symbol:
            return False
        if not self.can_sell(symbol, quantity):
            return False
        price = get_share_price(symbol)
        proceeds = price * quantity
        self.holdings[symbol] -= quantity
        if self.holdings[symbol] == 0:
            del self.holdings[symbol]
        self.cash_balance += proceeds
        self.transaction_history.append({
            'type': 'sell',
            'symbol': symbol,
            'quantity': quantity,
            'price': price,
            'datetime': datetime.datetime.now().isoformat()
        })
        return True

    def get_holdings(self) -> Dict[str, int]:
        # Returns a copy for safety.
        return dict(self.holdings)

    def get_portfolio_value(self) -> float:
        """Current cash + total value of held shares at current prices."""
        equity_value = sum(get_share_price(sym) * qty for sym, qty in self.holdings.items())
        total = self.cash_balance + equity_value
        return round(total, 2)

    def get_profit_loss(self) -> float:
        """Portfolio value minus total deposits minus total withdrawals."""
        total_deposit = sum(
            trans["quantity"] for trans in self.transaction_history if trans["type"] == "deposit"
        )
        total_withdraw = sum(
            trans["quantity"] for trans in self.transaction_history if trans["type"] == "withdraw"
        )
        pnl = self.get_portfolio_value() - (total_deposit - total_withdraw)
        return round(pnl, 2)

    def get_transaction_history(self) -> List[dict]:
        return list(self.transaction_history)

##########################
# UserManager
##########################

class UserManager:
    def __init__(self):
        # username (str) -> UserAccount
        self._users: Dict[str, UserAccount] = {}

    def create_user(self, username: str) -> bool:
        if not username or username in self._users:
            return False
        self._users[username] = UserAccount(username)
        return True

    def get_user(self, username: str) -> Optional[UserAccount]:
        return self._users.get(username)

    def user_exists(self, username: str) -> bool:
        return username in self._users
