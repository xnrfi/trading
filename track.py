import requests

def get_lighter_account_values(l1_address):
    base_url = "https://mainnet.zklighter.elliot.ai/api/v1"
    
    # Step 1: Fetch account indices associated with the L1 address
    resp = requests.get(f"{base_url}/accountsByL1Address", params={"l1_address": l1_address})
    if resp.status_code != 200:
        print(f"Error fetching accounts: {resp.status_code} - {resp.text}")
        return
    
    data = resp.json()
    sub_accounts = data.get("sub_accounts", [])
    if not sub_accounts:
        print("No accounts found for this L1 address.")
        return
    
    # Step 2: For each account index (main and subs), fetch account details
    for index in sub_accounts:
        resp = requests.get(f"{base_url}/account", params={"by": "index", "value": str(index)})
        if resp.status_code != 200:
            print(f"Error fetching details for account {index}: {resp.status_code} - {resp.text}")
            continue
        
        acc_data = resp.json()
        
        # Extract relevant data (based on API response structure)
        collateral = float(acc_data.get("collateral", "0"))
        positions = acc_data.get("positions", {})
        
        unrealized_pnl = sum(float(pos.get("unrealized_pnl", "0")) for pos in positions.values())
        realized_pnl = sum(float(pos.get("realized_pnl", "0")) for pos in positions.values())
        allocated_margins = sum(float(pos.get("allocated_margin", "0")) for pos in positions.values())
        
        # Total account value as per Lighter docs: Collateral + Unrealized PNL
        # (Realized PNL is already reflected in collateral)
        total_value = collateral + unrealized_pnl
        
        # Print results
        account_type = "Main Account" if index == sub_accounts[0] else f"Sub-Account {sub_accounts.index(index)}"
        print(f"\n{account_type} (Index: {index}):")
        print(f"  Collateral: {collateral} USDC")
        print(f"  Unrealized PNL: {unrealized_pnl} USDC")
        print(f"  Realized PNL: {realized_pnl} USDC (integrated into collateral)")
        print(f"  Allocated Margins for Positions: {allocated_margins} USDC")
        print(f"  Total Account Value: {total_value} USDC")

# Usage: Replace with your L1 (Ethereum) address
l1_address = "0xF8C515E3E0065a28F9F24478fCd6Ec9d8DbF3955"  # e.g., "0x1234567890abcdef1234567890abcdef12345678"
get_lighter_account_values(l1_address)
