# ratio_engine.py
import pandas as pd
from typing import Dict, Optional

def _get_amount(df: pd.DataFrame, keywords):
    """Find the first matching line item by keywords (case-insensitive)."""
    if df is None or df.empty:
        return None
    for kw in keywords:
        match = df[df['line_item'].str.lower().str.contains(kw.lower(), na=False)]
        if not match.empty:
            # return the first matched amount as float
            return float(match.iloc[0]['amount'])
    return None

def compute_ratios(balance_df: pd.DataFrame, pnl_df: pd.DataFrame) -> Dict[str, Optional[float]]:
    """
    Compute a set of standard financial ratios.
    Returns a dict {ratio_name: value_or_None}
    """
    # extract key line items (attempt multiple synonyms)
    cash = _get_amount(balance_df, ['cash', 'cash and cash equivalents'])
    ar = _get_amount(balance_df, ['accounts receivable', 'receivables'])
    inventory = _get_amount(balance_df, ['inventory', 'inventories'])
    total_current_assets = _get_amount(balance_df, ['total current assets', 'current assets'])
    total_assets = _get_amount(balance_df, ['total assets', 'assets'])
    accounts_payable = _get_amount(balance_df, ['accounts payable', 'payables'])
    short_term_debt = _get_amount(balance_df, ['short term debt', 'short-term debt','current portion of debt'])
    total_current_liabilities = _get_amount(balance_df, ['total current liabilities', 'current liabilities'])
    long_term_debt = _get_amount(balance_df, ['long term debt', 'non-current debt','long-term debt'])
    total_liabilities = _get_amount(balance_df, ['total liabilities', 'liabilities'])
    shareholders_equity = _get_amount(balance_df, ['shareholders equity', "shareholders' equity", 'equity', 'total equity'])

    revenue = _get_amount(pnl_df, ['revenue', 'sales', 'total revenue'])
    cogs = _get_amount(pnl_df, ['cost of goods sold','cogs','cost of sales'])
    gross_profit = _get_amount(pnl_df, ['gross profit'])
    operating_expenses = _get_amount(pnl_df, ['operating expenses','opex'])
    ebit = _get_amount(pnl_df, ['ebit','operating income','operating profit'])
    interest_expense = _get_amount(pnl_df, ['interest expense','finance costs'])
    tax_expense = _get_amount(pnl_df, ['tax expense','income tax'])
    net_income = _get_amount(pnl_df, ['net income','profit for the period','profit after tax'])
    depreciation = _get_amount(pnl_df, ['depreciation','depreciation & amortization','d&a'])

    def safe_div(n, d):
        try:
            if d is None or d == 0:
                return None
            return float(n) / float(d)
        except Exception:
            return None

    ratios = {}

    # Liquidity
    ratios['Current Ratio'] = safe_div(total_current_assets, total_current_liabilities)
    ratios['Quick Ratio'] = safe_div((cash or 0) + (ar or 0), total_current_liabilities)
    ratios['Cash Ratio'] = safe_div(cash, total_current_liabilities)

    # Leverage
    ratios['Debt-to-Equity'] = safe_div(total_liabilities, shareholders_equity)
    total_debt = (short_term_debt or 0) + (long_term_debt or 0)
    ratios['Debt Ratio (Debt/Assets)'] = safe_div(total_debt, total_assets)

    # Profitability
    ratios['Gross Margin'] = safe_div(gross_profit, revenue)
    ratios['Operating Margin'] = safe_div(ebit, revenue)
    ratios['Net Profit Margin'] = safe_div(net_income, revenue)
    ratios['Return on Assets (ROA)'] = safe_div(net_income, total_assets)
    ratios['Return on Equity (ROE)'] = safe_div(net_income, shareholders_equity)

    # Coverage
    # Basic DSCR approximation: (EBIT + Depreciation) / (Interest + Principal repayments)
    # We don't always have principal repayment; we will approximate using short_term_debt as principal due.
    principal_due = short_term_debt or 0
    dscr_numerator = (ebit or 0) + (depreciation or 0)
    dscr_denominator = (interest_expense or 0) + principal_due
    ratios['Debt Service Coverage Ratio (DSCR)'] = safe_div(dscr_numerator, dscr_denominator if dscr_denominator != 0 else None)

    # Efficiency
    ratios['Asset Turnover'] = safe_div(revenue, total_assets)
    ratios['Inventory Turnover'] = None
    if cogs is not None and inventory is not None and inventory != 0:
        ratios['Inventory Turnover'] = safe_div(cogs, inventory)

    # Round numeric ratios to reasonable decimals
    rounded = {}
    for k, v in ratios.items():
        if v is None:
            rounded[k] = None
        else:
            # for margins & ratios -> 2-4 decimals
            rounded[k] = round(v, 4) if abs(v) < 100 else round(v, 2)
    return rounded
