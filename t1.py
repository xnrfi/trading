import asyncio
import os
from dotenv import load_dotenv
import lighter
from lighter.exceptions import ApiException

# Load environment variables from .env file
load_dotenv()

async def get_lighter_account_values(l1_address: str = None):
    """
    Fetches total account value (collateral + unrealized PNL) across all sub-accounts
    for a given L1 address using authenticated Lighter API calls.
    
    Expects these values in your .env file:
    API_KEY_PRIVATE_KEY=0xyour_api_key_private_key_here
    API_KEY_INDEX=3  # Usually 3 or higher - check in Lighter app
    L1_ADDRESS=0xF8C515E3E0065a28F9F24478fCd6Ec9d8DbF3955  # Optional, can pass as arg
    """
    
    # Extract from .env
    api_key_private_key = os.getenv("API_KEY_PRIVATE_KEY")
    api_key_index = int(os.getenv("API_KEY_INDEX", 3))
    l1_address = l1_address or os.getenv("L1_ADDRESS")
    
    if not api_key_private_key:
        print("ERROR: API_KEY_PRIVATE_KEY not found in .env file")
        print("1. Create API key in Lighter app (Settings -> API)")
        print("2. Copy the PRIVATE KEY (starts with 0x)")
        print("3. Add to .env: API_KEY_PRIVATE_KEY=0x...")
        return
    
    if not l1_address:
        print("ERROR: L1_ADDRESS not found in .env file or not provided")
        return
    
    print(f"Fetching accounts for L1: {l1_address}")
    
    try:
        # Step 1: Create authenticated SignerClient (works for ALL your accounts)
        client = lighter.SignerClient(
            url="https://mainnet.zklighter.elliptiq.ai",
            private_key=api_key_private_key,
            account_index=0,  # Can be 0 - signer works across all your accounts
            api_key_index=api_key_index,
        )
        
        # Verify client setup
        err = client.check_client()
        if err is not None:
            print(f"Client setup error: {err}")
            print("Check your API_KEY_PRIVATE_KEY, API_KEY_INDEX, and account permissions")
            return
        
        print("Authenticated client ready")
        
        async with lighter.ApiClient(client) as api_client:
            account_api = lighter.AccountApi(api_client)
            
            # Step 2: Get ALL account indices for this L1 address (public endpoint)
            accounts_resp = await account_api.accounts_by_l1_address(
                l1_address=l1_address.lower()
            )
            sub_accounts = accounts_resp.data.sub_accounts or []
            
            if not sub_accounts:
                print("No accounts found for this L1 address.")
                return
            
            print(f"Found {len(sub_accounts)} account(s):\n")
            
            # Track totals across ALL sub-accounts
            total_collateral = 0.0
            total_unrealized_pnl = 0.0
            total_realized_pnl = 0.0
            total_allocated_margin = 0.0
            total_total_value = 0.0
            
            accounts_summary = []
            
            # Step 3: Fetch details for EACH account (requires auth)
            for i, acc in enumerate(sub_accounts):
                index = acc.index
                account_type = "Main Account" if acc.account_type == 0 else f"Sub-Account #{i}"
                
                try:
                    print(f"Fetching {account_type} (Index: {index})...")
                    
                    # Get full account details
                    detail_resp = await account_api.account(by="index", value=str(index))
                    data = detail_resp.data
                    
                    # Extract key metrics (handle None values safely)
                    collateral = float(data.collateral or 0)
                    
                    # Sum across all positions
                    positions = getattr(data, 'positions', {}) or {}
                    unrealized_pnl = sum(float(pos.unrealized_pnl or 0) for pos in positions.values())
                    realized_pnl = sum(float(pos.realized_pnl or 0) for pos in positions.values())
                    allocated_margin = sum(float(pos.allocated_margin or 0) for pos in positions.values())
                    
                    # Total Account Value = Collateral (includes realized PNL) + Unrealized PNL
                    total_value = collateral + unrealized_pnl
                    
                    # Update grand totals
                    total_collateral += collateral
                    total_unrealized_pnl += unrealized_pnl
                    total_realized_pnl += realized_pnl
                    total_allocated_margin += allocated_margin
                    total_total_value += total_value
                    
                    # Store for summary
                    accounts_summary.append({
                        'type': account_type,
                        'index': index,
                        'collateral': collateral,
                        'unrealized_pnl': unrealized_pnl,
                        'realized_pnl': realized_pnl,
                        'allocated_margin': allocated_margin,
                        'total_value': total_value
                    })
                    
                except ApiException as e:
                    print(f"Error for index {index}: {e.body}")
                    continue
            
            # Step 4: Pretty print results
            print("\n" + "="*60)
            print("ACCOUNT DETAILS")
            print("="*60)
            
            for acc in accounts_summary:
                print(f"\n{acc['type']} (Index: {acc['index']}):")
                print(f"Collateral:           ${acc['collateral']:,.2f} USDC")
                print(f"Unrealized PNL:       ${acc['unrealized_pnl']:+.2f} USDC")
                print(f"Realized PNL:         ${acc['realized_pnl']:+.2f} USDC (in collateral)")
                print(f"Allocated Margin:     ${acc['allocated_margin']:,.2f} USDC")
                print(f"Total Account Value:  ${acc['total_value']:,.2f} USDC")
                print("-" * 40)
            
            print("\n" + "="*60)
            print("GRAND TOTAL ACROSS ALL ACCOUNTS")
            print("="*60)
            print(f"Total Collateral:        ${total_collateral:,.2f} USDC")
            print(f"Total Unrealized PNL:    ${total_unrealized_pnl:+.2f} USDC")
            print(f"Total Realized PNL:      ${total_realized_pnl:+.2f} USDC")
            print(f"Total Allocated Margin:  ${total_allocated_margin:,.2f} USDC")
            print(f"GRAND TOTAL VALUE:       ${total_total_value:,.2f} USDC")
            print("="*60)
            
            # Optional: Available margin (collateral - allocated)
            available_margin = total_collateral - total_allocated_margin
            print(f"Available Margin:        ${available_margin:,.2f} USDC")
            
    except Exception as e:
        print(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Run the script - gets L1 address from .env or command line"""
    import sys
    l1_address = sys.argv[1] if len(sys.argv) > 1 else None
    asyncio.run(get_lighter_account_values(l1_address))

if __name__ == "__main__":
    main()
