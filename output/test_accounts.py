# test_accounts.py

import unittest
import datetime
try:
    from accounts import UserManager, UserAccount, get_share_price
except ImportError:
    from backend import UserManager, UserAccount, get_share_price

class TestUserManager(unittest.TestCase):
    def setUp(self):
        self.manager = UserManager()
        self.username = 'alice'
        self.username2 = 'bob'

    def test_create_user(self):
        # Creating a user should succeed
        self.assertTrue(self.manager.create_user(self.username))
        user = self.manager.get_user(self.username)
        self.assertIsNotNone(user)
        self.assertIsInstance(user, UserAccount)
        self.assertEqual(user.username, self.username)

    def test_duplicate_user(self):
        # Creating a duplicate user should fail
        self.assertTrue(self.manager.create_user(self.username))
        self.assertFalse(self.manager.create_user(self.username))
        # Creating a user with empty string username fails
        self.assertFalse(self.manager.create_user(""))
        # Creating a different user is fine
        self.assertTrue(self.manager.create_user(self.username2))

    def test_user_exists(self):
        self.manager.create_user(self.username)
        self.assertTrue(self.manager.user_exists(self.username))
        self.assertFalse(self.manager.user_exists(self.username2))


class TestUserAccountFunds(unittest.TestCase):
    def setUp(self):
        self.account = UserAccount("testuser")

    def test_deposit(self):
        self.account.deposit(1000.0)
        self.assertEqual(self.account.cash_balance, 1000.0)
        self.assertEqual(self.account.initial_deposit, 1000.0)
        self.assertEqual(len(self.account.transaction_history), 1)
        trans = self.account.transaction_history[0]
        self.assertEqual(trans['type'], 'deposit')
        self.assertEqual(trans['quantity'], 1000.0)
        self.assertIsNone(trans['symbol'])

        # Further deposit increases balance, initial_deposit unchanged
        self.account.deposit(500.0)
        self.assertEqual(self.account.cash_balance, 1500.0)
        self.assertEqual(self.account.initial_deposit, 1000.0)
        self.assertEqual(len(self.account.transaction_history), 2)

        # Negative or zero deposit raises
        with self.assertRaises(ValueError):
            self.account.deposit(0)
        with self.assertRaises(ValueError):
            self.account.deposit(-100)

    def test_withdraw_success(self):
        self.account.deposit(500.0)
        self.assertTrue(self.account.withdraw(200.0))
        self.assertEqual(self.account.cash_balance, 300.0)
        # Transaction history records withdraw
        withdraws = [t for t in self.account.transaction_history if t["type"]=="withdraw"]
        self.assertEqual(len(withdraws), 1)
        self.assertEqual(withdraws[0]['quantity'], 200.0)
        self.assertIsNone(withdraws[0]['symbol'])

    def test_withdraw_failure_negative_balance(self):
        self.account.deposit(100.0)
        # Try to withdraw more than balance
        self.assertFalse(self.account.withdraw(200.0))
        self.assertEqual(self.account.cash_balance, 100.0)
        # Try to withdraw negative or zero
        self.assertFalse(self.account.withdraw(0))
        self.assertFalse(self.account.withdraw(-10))


class TestUserAccountTrading(unittest.TestCase):
    def setUp(self):
        self.account = UserAccount("trader")
        self.account.deposit(2000.0)  # Start with good amount

    def test_buy_shares_success(self):
        # AAPL: $150, buy 5 for $750. Should succeed
        result = self.account.buy_shares('AAPL', 5)
        self.assertTrue(result)
        self.assertEqual(self.account.cash_balance, 2000.0 - 5*150.0)
        self.assertIn('AAPL', self.account.get_holdings())
        self.assertEqual(self.account.holdings['AAPL'], 5)
        latest = self.account.transaction_history[-1]
        self.assertEqual(latest['type'], 'buy')
        self.assertEqual(latest['symbol'], 'AAPL')
        self.assertEqual(latest['quantity'], 5)
        self.assertEqual(latest['price'], 150.0)

    def test_buy_shares_insufficient_funds(self):
        # Try to buy something we can't afford
        # TSLA price: $700, 4 * 700 = $2800 > 2000
        result = self.account.buy_shares('TSLA', 4)
        self.assertFalse(result)
        self.assertEqual(self.account.cash_balance, 2000.0)
        self.assertNotIn('TSLA', self.account.holdings)
        old_len = len(self.account.transaction_history)
        # Negative quantity and zero and invalid symbol
        self.assertFalse(self.account.buy_shares('AAPL', 0))
        self.assertFalse(self.account.buy_shares('AAPL', -5))
        self.assertFalse(self.account.buy_shares('', 5))
        self.assertEqual(len(self.account.transaction_history), old_len)

    def test_sell_shares_success(self):
        # Deposit extra so balance is $3000; GOOGL is $2800, leaves $200 after
        self.account.deposit(1000.0)
        self.account.buy_shares('GOOGL', 1)  # 2800, leaves $200 after
        self.account.deposit(8000)
        self.account.buy_shares('GOOGL', 2)  # 5600
        # Should now have 3 GOOGL shares
        self.assertEqual(self.account.holdings.get('GOOGL', 0), 3)
        # Now sell 2
        result = self.account.sell_shares('GOOGL', 2)
        self.assertTrue(result)
        self.assertEqual(self.account.holdings.get('GOOGL'), 1)
        self.assertTrue(self.account.cash_balance > 0)
        latest = self.account.transaction_history[-1]
        self.assertEqual(latest['type'], 'sell')
        self.assertEqual(latest['symbol'], 'GOOGL')
        self.assertEqual(latest['quantity'], 2)
        self.assertEqual(latest['price'], 2800.0)

        # Sell the final GOOGL
        result = self.account.sell_shares('GOOGL', 1)
        self.assertTrue(result)
        self.assertNotIn('GOOGL', self.account.holdings)

    def test_sell_shares_insufficient_holdings(self):
        # Try to sell without owning
        self.assertFalse(self.account.sell_shares('AAPL', 1))
        self.account.buy_shares('AAPL', 5)
        # Try to sell more than owned
        self.assertFalse(self.account.sell_shares('AAPL', 6))
        self.assertTrue(self.account.sell_shares('AAPL', 4))
        # Should have 1 AAPL left
        self.assertEqual(self.account.holdings['AAPL'], 1)
        # Can't sell 0 or negative
        self.assertFalse(self.account.sell_shares('AAPL', 0))
        self.assertFalse(self.account.sell_shares('AAPL', -2))


class TestUserAccountPortfolio(unittest.TestCase):
    def setUp(self):
        self.account = UserAccount("investor")
        self.account.deposit(1000.0)
        self.account.buy_shares('AAPL', 2)   # 2*150 = $300
        self.account.buy_shares('TSLA', 1)   # 1*700 = $700
        # $300 + $700 = $1000 spent, cash_balance=0

    def test_get_holdings(self):
        holdings = self.account.get_holdings()
        self.assertEqual(holdings, {'AAPL': 2, 'TSLA': 1})
        # Changing returned dict shouldn't affect internal
        holdings['AAPL'] = 5000
        self.assertEqual(self.account.holdings['AAPL'], 2)

    def test_get_portfolio_value(self):
        # Price hasn't changed. cash=0, AAPL*2=300, TSLA*1=700, total=1000
        value = self.account.get_portfolio_value()
        self.assertAlmostEqual(value, 1000.0)
        # If we sell AAPL, the value is same (but now 0 holdings of AAPL, cash=300, TSLA remains)
        self.account.sell_shares('AAPL', 2)
        value2 = self.account.get_portfolio_value()
        self.assertAlmostEqual(value2, 1000.0)

    def test_get_profit_loss(self):
        # No withdrawals, spent all the deposit, current value is same, so P/L = 0
        pnl = self.account.get_profit_loss()
        self.assertAlmostEqual(pnl, 0.0)
        # Let's sell all TSLA for $700
        self.account.sell_shares('TSLA', 1)
        # Now cash=700, P/L still should be 0
        pnl2 = self.account.get_profit_loss()
        self.assertAlmostEqual(pnl2, 0.0)
        # Withdraw some cash
        self.account.withdraw(100.0)
        # Portfolio value = 900 ($600 cash + $300 AAPL), net deposit = 1000 - 100 = 900, P/L = 900 - 900 = 0.0
        pnl3 = self.account.get_profit_loss()
        self.assertAlmostEqual(pnl3, 0.0)

    def test_get_transaction_history(self):
        history = self.account.get_transaction_history()
        # Should include 1 deposit, 2 buys
        types = [t['type'] for t in history]
        self.assertIn('deposit', types)
        self.assertGreaterEqual(types.count('buy'), 2)
        # Each transaction should have 'type', 'symbol', 'quantity', 'datetime'
        for t in history:
            self.assertIn('type', t)
            self.assertIn('quantity', t)
            self.assertIn('datetime', t)
        # Buy/sell increases transaction history
        n = len(history)
        self.account.sell_shares('AAPL', 1)
        history2 = self.account.get_transaction_history()
        self.assertEqual(len(history2), n+1)
        self.assertEqual(history2[-1]['type'], 'sell')

    def test_get_share_price(self):
        # Builtin test
        self.assertEqual(get_share_price('AAPL'), 150.0)
        self.assertEqual(get_share_price('tsla'), 700.0)
        self.assertEqual(get_share_price('GOOGL'), 2800.0)
        # Unknown returns 0
        self.assertEqual(get_share_price('MSFT'), 0.0)


if __name__ == "__main__":
    # Run all the test cases
    suite = unittest.TestLoader().loadTestsFromModule(__import__(__name__))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    print('---- UNIT TEST SUMMARY ----')
    print('Ran:', result.testsRun)
    print('Failures:', len(result.failures))
    print('Errors:', len(result.errors))
    if not result.failures and not result.errors:
        print('ALL TESTS PASSED.')