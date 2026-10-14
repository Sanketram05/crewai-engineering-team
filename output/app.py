# app.py

import os
import sys
from pathlib import Path

# Ensure directory is on sys.path for local module imports
sys.path.insert(0, str(Path(__file__).parent.resolve()))

import gradio as gr
try:
    from accounts import UserManager, get_share_price
except ImportError:
    from backend import UserManager, get_share_price

# === --- Color Palette for style --- ===
PRIMARY = "#209dd7"
SECONDARY = "#753991"
ACCENT = "#ecad0a"
BG_GRAY = "#f7f7fa"
DARK_BG = "#181524"
DARK_CARD = "#2a283a"
FONT_GRAY = "#252525"
DARK_FONT = "#faf9f6"

# === --- One global UserManager, manage the "single user" system --- ===
user_manager = UserManager()

# === --- Default share symbols for trading selection --- ===
SYMBOLS = [("AAPL", "🟣 AAPL"), ("TSLA", "🔵 TSLA"), ("GOOGL", "🟠 GOOGL")]

########################################
# --- Logic Functions, UI <-> Backend
########################################

def get_holdings_df(user):
    holdings = user.get_holdings() if user else {}
    rows = []
    for sym, _ in SYMBOLS:
        qty = holdings.get(sym, 0)
        price = get_share_price(sym)
        value = qty * price
        rows.append({"Symbol": sym, "Shares": qty, "Price": price, "Total Value": round(value, 2)})
    return rows

def show_transaction_history(state_username):
    if not state_username:
        return []
    user = user_manager.get_user(state_username)
    if not user:
        return []
    txns = user.get_transaction_history()[::-1][:20]  # show latest 20
    rows = []
    for x in txns:
        price_val = round(x["price"], 2) if x.get("price") is not None else 0.0
        rows.append({
            "Date/Time": str(x.get("datetime", ""))[:19].replace("T", " "),
            "Type": str(x.get("type", "")).upper(),
            "Symbol": x.get("symbol") or "-",
            "Quantity": x.get("quantity", 0),
            "Price": price_val,
        })
    return rows

def create_account(username, state_username):
    if not username or not username.strip():
        return gr.update(visible=True, value="❌ Please enter a username."), gr.update(), None
    clean_username = username.strip()
    if user_manager.user_exists(clean_username):
        return gr.update(visible=True, value=f"❌ Username '{clean_username}' already exists, please choose another."), gr.update(), None
    ok = user_manager.create_user(clean_username)
    if ok:
        return (
            gr.update(visible=True, value=f"✅ Account '{clean_username}' created! Please deposit funds to begin."),
            gr.update(value=clean_username, visible=False),  # hide input, lock in user
            clean_username,
        )
    return gr.update(visible=True, value="❌ Unknown error creating account."), gr.update(), None

def deposit_funds(state_username, amount):
    if not state_username:
        return "❌ No active user. Please create an account first.", 0.0, 0.0, 0.0, [], []
    user = user_manager.get_user(state_username)
    if not user:
        return "❌ User not found.", 0.0, 0.0, 0.0, [], []
    try:
        if amount is None or float(amount) <= 0:
            return (
                "❌ Deposit amount must be positive.",
                round(user.cash_balance, 2),
                round(user.get_portfolio_value(), 2),
                round(user.get_profit_loss(), 2),
                get_holdings_df(user),
                show_transaction_history(state_username),
            )
        user.deposit(float(amount))
    except Exception as e:
        return (
            f"❌ {str(e)}",
            round(user.cash_balance, 2),
            round(user.get_portfolio_value(), 2),
            round(user.get_profit_loss(), 2),
            get_holdings_df(user),
            show_transaction_history(state_username),
        )
    return (
        f"✅ Deposited ${float(amount):,.2f}",
        round(user.cash_balance, 2),
        round(user.get_portfolio_value(), 2),
        round(user.get_profit_loss(), 2),
        get_holdings_df(user),
        show_transaction_history(state_username),
    )

def withdraw_funds(state_username, amount):
    if not state_username:
        return "❌ No active user. Please create an account first.", 0.0, 0.0, 0.0, [], []
    user = user_manager.get_user(state_username)
    if not user:
        return "❌ User not found.", 0.0, 0.0, 0.0, [], []
    try:
        if amount is None or float(amount) <= 0:
            return (
                "❌ Withdrawal amount must be positive.",
                round(user.cash_balance, 2),
                round(user.get_portfolio_value(), 2),
                round(user.get_profit_loss(), 2),
                get_holdings_df(user),
                show_transaction_history(state_username),
            )
        ok = user.withdraw(float(amount))
        if not ok:
            return (
                "❌ Insufficient funds for withdrawal.",
                round(user.cash_balance, 2),
                round(user.get_portfolio_value(), 2),
                round(user.get_profit_loss(), 2),
                get_holdings_df(user),
                show_transaction_history(state_username),
            )
    except Exception as e:
        return (
            f"❌ {str(e)}",
            round(user.cash_balance, 2),
            round(user.get_portfolio_value(), 2),
            round(user.get_profit_loss(), 2),
            get_holdings_df(user),
            show_transaction_history(state_username),
        )
    return (
        f"✅ Withdrew ${float(amount):,.2f}",
        round(user.cash_balance, 2),
        round(user.get_portfolio_value(), 2),
        round(user.get_profit_loss(), 2),
        get_holdings_df(user),
        show_transaction_history(state_username),
    )

def buy_shares(state_username, symbol, quantity):
    if not state_username:
        return "❌ No active user. Please create an account first.", 0.0, 0.0, 0.0, [], []
    user = user_manager.get_user(state_username)
    if not user:
        return "❌ User not found.", 0.0, 0.0, 0.0, [], []
    valid_symbols = [s[0] for s in SYMBOLS]
    if not symbol or symbol not in valid_symbols:
        return (
            "❌ Please select a valid symbol.",
            round(user.cash_balance, 2),
            round(user.get_portfolio_value(), 2),
            round(user.get_profit_loss(), 2),
            get_holdings_df(user),
            show_transaction_history(state_username),
        )
    try:
        if quantity is None or int(quantity) <= 0:
            return (
                "❌ Quantity must be a positive integer.",
                round(user.cash_balance, 2),
                round(user.get_portfolio_value(), 2),
                round(user.get_profit_loss(), 2),
                get_holdings_df(user),
                show_transaction_history(state_username),
            )
        qty = int(quantity)
        if not user.can_buy(symbol, qty):
            price = get_share_price(symbol)
            need = price * qty
            if price == 0:
                msg = "❌ Invalid symbol price."
            elif need > user.cash_balance:
                msg = f"❌ Insufficient funds. Need ${need:,.2f}, have ${user.cash_balance:,.2f}."
            else:
                msg = "❌ Cannot buy shares."
            return (
                msg,
                round(user.cash_balance, 2),
                round(user.get_portfolio_value(), 2),
                round(user.get_profit_loss(), 2),
                get_holdings_df(user),
                show_transaction_history(state_username),
            )
        ok = user.buy_shares(symbol, qty)
        if not ok:
            return (
                "❌ Error executing purchase.",
                round(user.cash_balance, 2),
                round(user.get_portfolio_value(), 2),
                round(user.get_profit_loss(), 2),
                get_holdings_df(user),
                show_transaction_history(state_username),
            )
    except Exception as e:
        return (
            f"❌ {str(e)}",
            round(user.cash_balance, 2),
            round(user.get_portfolio_value(), 2),
            round(user.get_profit_loss(), 2),
            get_holdings_df(user),
            show_transaction_history(state_username),
        )
    price = get_share_price(symbol)
    total = price * qty
    return (
        f"✅ Bought {qty} {symbol} @ ${price:,.2f} each (${total:,.2f})",
        round(user.cash_balance, 2),
        round(user.get_portfolio_value(), 2),
        round(user.get_profit_loss(), 2),
        get_holdings_df(user),
        show_transaction_history(state_username),
    )

def sell_shares(state_username, symbol, quantity):
    if not state_username:
        return "❌ No active user. Please create an account first.", 0.0, 0.0, 0.0, [], []
    user = user_manager.get_user(state_username)
    if not user:
        return "❌ User not found.", 0.0, 0.0, 0.0, [], []
    valid_symbols = [s[0] for s in SYMBOLS]
    if not symbol or symbol not in valid_symbols:
        return (
            "❌ Please select a valid symbol.",
            round(user.cash_balance, 2),
            round(user.get_portfolio_value(), 2),
            round(user.get_profit_loss(), 2),
            get_holdings_df(user),
            show_transaction_history(state_username),
        )
    try:
        if quantity is None or int(quantity) <= 0:
            return (
                "❌ Quantity must be a positive integer.",
                round(user.cash_balance, 2),
                round(user.get_portfolio_value(), 2),
                round(user.get_profit_loss(), 2),
                get_holdings_df(user),
                show_transaction_history(state_username),
            )
        qty = int(quantity)
        if not user.can_sell(symbol, qty):
            have = user.holdings.get(symbol, 0)
            return (
                f"❌ Insufficient holdings: you own {have} shares of {symbol}.",
                round(user.cash_balance, 2),
                round(user.get_portfolio_value(), 2),
                round(user.get_profit_loss(), 2),
                get_holdings_df(user),
                show_transaction_history(state_username),
            )
        ok = user.sell_shares(symbol, qty)
        if not ok:
            return (
                "❌ Error executing sale.",
                round(user.cash_balance, 2),
                round(user.get_portfolio_value(), 2),
                round(user.get_profit_loss(), 2),
                get_holdings_df(user),
                show_transaction_history(state_username),
            )
    except Exception as e:
        return (
            f"❌ {str(e)}",
            round(user.cash_balance, 2),
            round(user.get_portfolio_value(), 2),
            round(user.get_profit_loss(), 2),
            get_holdings_df(user),
            show_transaction_history(state_username),
        )
    price = get_share_price(symbol)
    total = price * qty
    return (
        f"✅ Sold {qty} {symbol} @ ${price:,.2f} each (${total:,.2f})",
        round(user.cash_balance, 2),
        round(user.get_portfolio_value(), 2),
        round(user.get_profit_loss(), 2),
        get_holdings_df(user),
        show_transaction_history(state_username),
    )

def current_user(state_username):
    return state_username if state_username else ""

def reload_all(state_username):
    user = user_manager.get_user(state_username) if state_username else None
    if user:
        return (
            "",  # clear error/message
            round(user.cash_balance, 2),
            round(user.get_portfolio_value(), 2),
            round(user.get_profit_loss(), 2),
            get_holdings_df(user),
            show_transaction_history(state_username),
        )
    else:
        return (
            "",
            0.0,
            0.0,
            0.0,
            [{"Symbol": s[0], "Shares": 0, "Price": get_share_price(s[0]), "Total Value": 0.0} for s in SYMBOLS],
            [],
        )

######################################################
# --- Gradio UI Layout ---
######################################################

CUSTOM_CSS = f"""
    .account-card {{
        background: var(--card-background, {BG_GRAY});
        border-radius: 12px;
        padding: 32px 24px 16px 24px;
        box-shadow: 0 0 0.5px rgba(0,0,0,0.08);
        margin-bottom: 24px;
    }}
    .funds-section {{
        background: var(--card-background, {BG_GRAY});
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 18px;
        border: 1.5px solid #E7E7F1;
    }}
    .trade-section {{
        background: var(--card-background, {BG_GRAY});
        border-radius: 12px;
        padding: 20px;
        border: 1.5px solid #E7E7F1;
        margin-bottom: 18px;
    }}
    .portfolio-info {{
        background: var(--card-background, {BG_GRAY});
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 10px;
    }}
    .title-header {{
        font-size: 2.0rem;
        font-weight: 700;
        color: {SECONDARY};
        letter-spacing: 0.02em;
        margin-bottom: 0.1em;
    }}
    .value-key {{
        font-weight: 690;
        color: {PRIMARY};
    }}
    .value-big {{
        font-size: 1.42rem;
        color: {ACCENT};
    }}
    .gradio-container {{
        font-family: 'Inter', 'Verdana', 'Segoe UI', Arial, sans-serif;
        background: var(--background-fill, {BG_GRAY});
        color: var(--body-text-color, {FONT_GRAY});
    }}

    @media (prefers-color-scheme: dark) {{
        .account-card,
        .funds-section,
        .trade-section,
        .portfolio-info {{
            background: {DARK_CARD};
            color: {DARK_FONT};
            border-color: #2d2466 !important;
        }}
        .title-header {{
            color: {ACCENT} !important;
        }}
        .value-big {{
            color: {PRIMARY};
        }}
    }}
"""

with gr.Blocks(title="Trading Simulation Platform") as demo:
    gr.Markdown(
        f"""
        <div class='title-header'>Trading Simulation Platform - <span style='color:{ACCENT}'>Account &amp; Portfolio Management</span></div>
        <div style='color: {SECONDARY}; font-size:1.05em; margin-bottom: 0.7em;'>
            Simulate trading AAPL, TSLA, GOOGL &mdash; manage your account below.
        </div>
        """,
        elem_id="main-title"
    )

    state_username = gr.State()

    ## === --- Account --- ===
    with gr.Row():
        with gr.Column(scale=3, elem_classes=["account-card"]):
            gr.Markdown("#### 1️⃣ Create Account")
            inp_username = gr.Textbox(label="Choose Username", placeholder="Enter a unique username", value="", max_lines=1)
            btn_create = gr.Button("Create Account", variant="primary", elem_id="create-acct-btn")
            msg_create = gr.Markdown("", visible=False)
        with gr.Column(scale=2):
            gr.Markdown("#### 👤 Current User")
            txt_show_user = gr.Textbox(label="Active User", interactive=False, value="", elem_id="show-user")

    ## === --- Funds Management --- ===
    with gr.Row():
        with gr.Column(elem_classes=["funds-section"]):
            gr.Markdown("#### 💼 Manage Funds")
            with gr.Row():
                txt_deposit_amt = gr.Number(label="Deposit Amount ($)", minimum=0.01, value=None, precision=2)
                btn_deposit = gr.Button("Deposit", icon="➕", variant="secondary")
            with gr.Row():
                txt_withdraw_amt = gr.Number(label="Withdraw Amount ($)", minimum=0.01, value=None, precision=2)
                btn_withdraw = gr.Button("Withdraw", icon="➖")
            msg_funds = gr.Markdown("", visible=True)

    ## === --- Trading Section --- ===
    with gr.Row(elem_classes=["trade-section"]):
        gr.Markdown("#### 🔄 Trade Shares")
        with gr.Column():
            drp_symbol = gr.Dropdown(choices=[s[0] for s in SYMBOLS], value="AAPL", label="Stock Symbol")
            num_qty_buy = gr.Number(label="Buy Quantity", value=None, minimum=1, precision=0)
            btn_buy = gr.Button("Buy", icon="🛒", variant="primary")
        with gr.Column():
            drp_symbol_sell = gr.Dropdown(choices=[s[0] for s in SYMBOLS], value="AAPL", label="Stock Symbol")
            num_qty_sell = gr.Number(label="Sell Quantity", value=None, minimum=1, precision=0)
            btn_sell = gr.Button("Sell", icon="💸", variant="stop")
        msg_trade = gr.Markdown("", visible=True)

    # Portfolio summary info section
    with gr.Row(elem_classes=["portfolio-info"]):
        with gr.Column():
            gr.Markdown("##### 💰 Cash Balance", elem_classes=["value-key"])
            txt_cash = gr.Number(value=0.0, interactive=False, label="", elem_id="cash")
        with gr.Column():
            gr.Markdown("##### 📈 Portfolio Value", elem_classes=["value-key"])
            txt_portfolio = gr.Number(value=0.0, interactive=False, label="", elem_id="portfolio")
        with gr.Column():
            gr.Markdown("##### 💹 Profit / Loss", elem_classes=["value-key"])
            txt_profit = gr.Number(value=0.0, interactive=False, label="", elem_id="profit")

    # Holdings Table
    gr.Markdown("##### 📋 Holdings")
    tbl_holdings = gr.Dataframe(
        headers=["Symbol", "Shares", "Price", "Total Value"],
        value=[{"Symbol": s[0], "Shares": 0, "Price": get_share_price(s[0]), "Total Value": 0.0} for s in SYMBOLS],
        datatype=["str", "number", "number", "number"],
        interactive=False,
    )

    # Transaction History
    gr.Markdown("##### 📝 Transaction History (Latest 20)")
    tbl_history = gr.Dataframe(
        interactive=False,
        headers=["Date/Time", "Type", "Symbol", "Quantity", "Price"],
        value=[],
        datatype=["str", "str", "str", "number", "number"],
        max_height=260,
    )

    # --- Event Wiring ---
    btn_create.click(
        fn=create_account,
        inputs=[inp_username, state_username],
        outputs=[msg_create, inp_username, state_username],
    )

    state_username.change(
        fn=current_user,
        inputs=[state_username],
        outputs=[txt_show_user],
    )

    state_username.change(
        fn=reload_all,
        inputs=[state_username],
        outputs=[msg_trade, txt_cash, txt_portfolio, txt_profit, tbl_holdings, tbl_history],
    )

    btn_deposit.click(
        fn=deposit_funds,
        inputs=[state_username, txt_deposit_amt],
        outputs=[msg_funds, txt_cash, txt_portfolio, txt_profit, tbl_holdings, tbl_history],
    )

    btn_withdraw.click(
        fn=withdraw_funds,
        inputs=[state_username, txt_withdraw_amt],
        outputs=[msg_funds, txt_cash, txt_portfolio, txt_profit, tbl_holdings, tbl_history],
    )

    btn_buy.click(
        fn=buy_shares,
        inputs=[state_username, drp_symbol, num_qty_buy],
        outputs=[msg_trade, txt_cash, txt_portfolio, txt_profit, tbl_holdings, tbl_history],
    )

    btn_sell.click(
        fn=sell_shares,
        inputs=[state_username, drp_symbol_sell, num_qty_sell],
        outputs=[msg_trade, txt_cash, txt_portfolio, txt_profit, tbl_holdings, tbl_history],
    )

if __name__ == "__main__":
    demo.launch(css=CUSTOM_CSS)