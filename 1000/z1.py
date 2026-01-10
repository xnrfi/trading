import asyncio
import os
import sqlite3
from datetime import datetime
from dotenv import load_dotenv
import lighter
from lighter.exceptions import ApiException

load_dotenv()

API_KEY_PRIVATE_KEY = os.getenv("API_KEY_PRIVATE_KEY")
API_KEY_INDEX = int(os.getenv("API_KEY_INDEX", "3"))
MAIN_ACCOUNT_INDEX = int(os.getenv("MAIN_ACCOUNT_INDEX"))

DB_PATH = "balance.db"

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()
cursor.execute('CREATE TABLE IF NOT EXISTS balances (date TEXT PRIMARY KEY, total_value REAL)')
conn.commit()

async def fetch_value():
    try:
        signer = lighter.SignerClient(
            url="https://mainnet.zklighter.elliot.ai",
            account_index=MAIN_ACCOUNT_INDEX,
            api_private_keys={API_KEY_INDEX: API_KEY_PRIVATE_KEY}
        )
        err = signer.check_client()
        if err:
            print(f"Error: {err}")
            return None

        config = lighter.Configuration(host="https://mainnet.zklighter.elliot.ai")
        async with lighter.ApiClient(configuration=config) as api_client:
            account_api = lighter.AccountApi(api_client)
            resp = await account_api.account(by="index", value=str(MAIN_ACCOUNT_INDEX))
            acc = next((a for a in resp.accounts if a.index == MAIN_ACCOUNT_INDEX), None)
            if not acc:
                return None
            collateral = float(acc.collateral or 0)
            unrealized = sum(float(getattr(p, 'unrealized_pnl', 0) or 0) for p in getattr(acc, 'positions', []))
            return collateral + unrealized
    except Exception as e:
        print(f"Fetch failed: {e}")
        return None

def daily_task():
    value = asyncio.run(fetch_value())
    if value is None:
        print("Failed to fetch balance today")
        return
    
    today = datetime.now().strftime("%Y-%m-%d")
    cursor.execute("INSERT OR REPLACE INTO balances (date, total_value) VALUES (?, ?)", (today, value))
    conn.commit()
    print(f"{today}: ${value:,.2f} USDC saved")

# Backfill Jan 1-4 if first run
cursor.execute("SELECT COUNT(*) FROM balances")
if cursor.fetchone()[0] == 0:
    value = asyncio.run(fetch_value()) or 2782.79
    for day in range(1, 5):
        date = f"2026-01-0{day}"
        cursor.execute("INSERT OR IGNORE INTO balances VALUES (?, ?)", (date, value))
    conn.commit()
    print("Backfilled Jan 1–4")

if __name__ == "__main__":
    daily_task()  # Run now
    print("Run this script daily (e.g., via cron) to update balance.db")
