from fastmcp import FastMCP
import os
import sqlite3
import json

# Setup exact paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "expenses.db")
CAT_PATH = os.path.join(BASE_DIR, "categories.json")

mcp = FastMCP("Expense_Tracker")

def init_db():
    with sqlite3.connect(DB_PATH) as c:
        c.execute("""
                 CREATE TABLE IF NOT EXISTS expenses(
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 date TEXT NOT NULL,
                 amount REAL NOT NULL,
                 category TEXT NOT NULL,
                 subcategory TEXT DEFAULT '',
                 note TEXT DEFAULT '')
        """)

init_db()

# Read the categories once when the server starts for the Tool description
try:
    with open(CAT_PATH, "r", encoding="utf-8") as f:
        CATEGORY_RULES = f.read()
except FileNotFoundError:
    CATEGORY_RULES = "Categories file not found."

# --- RESOURCES ---
# This allows you to attach the file manually using the paperclip icon if you want to
@mcp.resource("expense://categories", mime_type="application/json")
def get_categories() -> str:
    """Provides Claude with the current strict list of valid categories and subcategories."""
    try:
        with open(CAT_PATH, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return '{"error": "categories.json file not found! Please create it."}'

# --- TOOLS ---
# The categories are ALSO injected directly here so it works automatically!
@mcp.tool(description=f"Add a new expense. STRICT RULE: You MUST map the expense to the exact categories and subcategories provided here:\n{CATEGORY_RULES}")
def add_expense(date: str, amount: float, category: str, subcategory: str = "", note: str = "") -> str:
    with sqlite3.connect(DB_PATH) as c:
        cur = c.execute(
            "INSERT INTO expenses(date,amount,category,subcategory,note) VALUES (?,?,?,?,?)",
            (date, amount, category, subcategory, note)
        )
        return f"Success! Expense added with ID: {cur.lastrowid} under category '{category} -> {subcategory}'"

@mcp.tool()
def list_expenses() -> str:
    """List all expense entries from the database."""
    with sqlite3.connect(DB_PATH) as c:
        cur = c.execute("SELECT id,date,amount,category,subcategory,note FROM expenses ORDER BY id ASC")
        cols = [d[0] for d in cur.description]
        data = [dict(zip(cols, r)) for r in cur.fetchall()]
        return json.dumps(data, indent=2)


if __name__=="__main__":
    # ERROR 3 FIXED: Changed "http" to "sse"
    # NOTE: Change this to mcp.run() if you want to test in the UI below!
    mcp.run(transport="sse", host="0.0.0.0", port=8000)