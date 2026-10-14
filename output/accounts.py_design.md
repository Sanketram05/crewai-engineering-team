# Account Management System for Trading Simulation Platform - DESIGN

## Overview

This system allows users to:
- Create an account
- Deposit and withdraw funds
- Buy and sell shares
- Track portfolio value and P/L
- View current holdings and transaction history

The system enforces constraints: no overdrafts, no overspending on shares, and no selling what isn't owned. Access to a `get_share_price(symbol)` function is available for price data.

All code files (backend, frontend, tests) reside in the same directory.

---

## MODULES & ASSIGNMENTS

### 1. backend.py (Assigned to: backend_engineer)
Implements all business logic, state management, and constraints.

#### Classes

- **UserAccount**
    - `def __init__(self, username: str):`
    - `def deposit(self, amount: float) -> None:`
    - `def withdraw(self, amount: float) -> bool:`
    - `def buy_shares(self, symbol: str, quantity: int) -> bool:`
    - `def sell_shares(self, symbol: str, quantity: int) -> bool:`
    - `def get_holdings(self) -> dict:`
    - `def get_portfolio_value(self) -> float:`
    - `def get_profit_loss(self) -> float:`
    - `def get_transaction_history(self) -> list:`
    - `def can_withdraw(self, amount: float) -> bool:`
    - `def can_buy(self, symbol: str, quantity: int) -> bool:`
    - `def can_sell(self, symbol: str, quantity: int) -> bool:`

- **UserManager**
    - `def __init__(self):`
    - `def create_user(self, username: str) -> bool:`
    - `def get_user(self, username: str) -> UserAccount | None:`
    - `def user_exists(self, username: str) -> bool:`

#### Utility Function

- **get_share_price (to be provided as described)**
    - `def get_share_price(symbol: str) -> float:`

---

### 2. app.py (Assigned to: frontend_engineer)
Implements the Gradio frontend, connecting to backend.py.

#### UI Components and Gradio 6 Guidance

- Use `gr.Interface` for the main app.
    - **NEW in Gradio 6:** Use `inputs` and `outputs` as `components` keyword arguments.
    - Use `gr.Textbox`, `gr.Number`, `gr.Dropdown`, `gr.Button` as needed.
    - Use `gr.Dataframe` for tabular data (holdings, transaction history).
    - Use `gr.State` objects to persist user/session info in app.
    - For all event triggers, use `.click(fn, ...)`, not `.submit`.
    - Use `value=` to set initial values, not `default`.
    - Return objects/components in the same order as listed in `outputs`.
    - For error messaging / validations: Use `gr.Markdown` or `gr.Textbox` to display error messages to users visually.
    - If uploading/downloading data is needed, use `gr.File`.

#### Functions to Build

- `def create_account(username: str) -> str:`
- `def deposit(username: str, amount: float) -> str:`
- `def withdraw(username: str, amount: float) -> str:`
- `def buy_shares(username: str, symbol: str, quantity: int) -> str:`
- `def sell_shares(username: str, symbol: str, quantity: int) -> str:`
- `def show_holdings(username: str) -> dict:`
- `def show_portfolio_value(username: str) -> float:`
- `def show_profit_loss(username: str) -> float:`
- `def show_transaction_history(username: str) -> list:`

*All functions should communicate with backend.UserManager/UserAccount and update UI components.*

#### Layout Plan

- Account creation/login section
- Funds management: deposit/withdraw
- Trading: buy/sell shares
- Portfolio info: current holdings, total value, P/L
- Transaction history
- Error/validation messaging section

---

### 3. test_backend.py (Assigned to: test_engineer)
Implements unit tests for backend.py.

#### Test Cases to Implement

- **User Account Management**
    - `def test_create_user()`
    - `def test_duplicate_user()`

- **Funds Management**
    - `def test_deposit()`
    - `def test_withdraw_success()`
    - `def test_withdraw_failure_negative_balance()`

- **Trading**
    - `def test_buy_shares_success()`
    - `def test_buy_shares_insufficient_funds()`
    - `def test_sell_shares_success()`
    - `def test_sell_shares_insufficient_holdings()`

- **Portfolio Metrics**
    - `def test_get_holdings()`
    - `def test_get_portfolio_value()`
    - `def test_get_profit_loss()`
    - `def test_get_transaction_history()`

#### Test Setup

- Use the provided `get_share_price` from backend.py.
- Create temporary accounts and simulate various flows.

---

## DESIGN DETAILS

### Data Structures

- User data is managed in memory per session (persistent storage not in scope).
- Each user has: username, initial deposit, cash balance, holdings (dict), transaction history (list).
- All amounts are in `float`.
- Each transaction records: type (deposit, withdrawal, buy, sell), symbol, quantity, price, date/time.

### Error Handling

- Actions that fail (e.g. overdraft, oversell) should return a message indicating cause and no state change.
- Negative/zero deposit/withdraw/trade attempts must be caught and rejected.

### get_share_price

- Used wherever buy/sell/portfolio value needs current price.
- Test implementation provides static values for specific symbols.

---

## FILE LIST & OWNERSHIP

- backend.py (**backend_engineer**): All business logic and state.
- app.py (**frontend_engineer**): Gradio 6 frontend, wiring to backend.
- test_backend.py (**test_engineer**): Unit tests for backend.py.

---

## SUMMARY OF ENGINEER ASSIGNMENTS

- **backend_engineer**: Implement all specified classes, methods, and utility functions in backend.py.
- **frontend_engineer**: Build complete interactive Gradio 6 UI in app.py using above functions/guidance, using only gradio (no other third-party packages).
- **test_engineer**: Implement test cases in test_backend.py, comprehensively exercising all backend logic and edge cases.

---

## SUCCESS CRITERIA

- Users can register, deposit/withdraw without violating rules, trade stocks, and view up-to-date holdings/P&L/history via the Gradio UI.
- The system strictly enforces all constraints.
- All backend tests pass.
- Gradio frontend works as expected, using v6 API correctly.

---