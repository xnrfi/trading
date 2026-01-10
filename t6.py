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
    
    Requires in .env:
    API_KEY_PRIVATE_KEY=0x... (your API private key)
    API_KEY_INDEX=3 (your API key index)
    MAIN_ACCOUNT_INDEX=185609 (your main account index - REQUIRED!)
    L1_ADDRESS=0xF8C515E3E0065a28F9F24478fCd6Ec9d8DbF3955 (optional)
    """
    
    api_key_private_key = os.getenv("API_KEY_PRIVATE_KEY")
    api_key_index = int(os.getenv("API_KEY_INDEX", "3"))
    account_index = int(os.getenv("MAIN_ACCOUNT_INDEX"))
    l1_address = l1_address or os.getenv("L1_ADDRESS")
    
    if not api_key_private_key:
        print("ERROR: API_KEY_PRIVATE_KEY missing in .env")
        return
    if not l1_address:
        print("ERROR: L1_ADDRESS missing")
        return
    
    print(f"Fetching accounts for L1: {l1_address}")
    
    try:
        # Use the correct SignerClient constructor per current official docs
        signer = lighter.SignerClient(
            url="https://mainnet.zklighter.elliot.ai",
            private_key=api_key_private_key,
            account_index=account_index,
            api_key_index=api_key_index,
        )
        
        err = signer.check_client()
        if err is not None:
            print(f"Signer setup error: {err}")
            print("Possible causes:")
            print(" - Wrong MAIN_ACCOUNT_INDEX (must be your main account index, e.g. 185609)")
            print(" - Wrong API_KEY_PRIVATE_KEY or API_KEY_INDEX")
            print(" - API key not enabled or revoked")
            return
        
        print("Signer ready - generating read-only auth token")
        
        # Generate short-lived read-only auth token
        auth_token, err = signer.create_auth_token_with_expiry()
        if err is not None:
            print(f"Auth token error: {err}")
            return
        
        print("Auth token generated")
        
        # Configure ApiClient with auth header
        config = lighter.Configuration(
            host="https://mainnet.zklighter.elliot.ai"
        )
        config.access_token = auth_token
        
        async with lighter.ApiClient(config) as api_client:
            account_api = lighter.AccountApi(api_client)
            
            # Get account list (now authenticated, should work)
            accounts_resp = await account_api.accounts_by_l1_address(
                l1_address=l1_address.lower()
            )
            sub_accounts = accounts_resp.data.sub_accounts or []
            
            if not sub_accounts:
                print("No accounts found.")
                return
            
            print(f"Found {len(sub_accounts)} account(s):\n")
            
            total_collateral = 0.0
            total_unrealized_pnl = 0.0
            total_realized_pnl = 0.0
            total_allocated_margin = 0.0
            total_total_value = 0.0
            
            accounts_summary = []
            
            for i, acc in enumerate(sub_accounts):
                index = acc.index
                account_type = "Main Account" if acc.account_type == 0 else f"Sub-Account #{i}"
                
                try:
                    print(f"Fetching {account_type} (Index: {index})...")
                    
                    detail_resp = await account_api.account(by="index", value=str(index))
                    data = detail_resp.data
                    
                    collateral = float(data.collateral or 0)
                    
                    positions = getattr(data, 'positions', {}) or {}
                    unrealized_pnl = sum(float(pos.unrealized_pnl or 0) for pos in positions.values())
                    realized_pnl = sum(float(pos.realized_pnl or 0) for pos in positions.values())
                    allocated_margin = sum(float(pos.allocated_margin or 0) for pos in positions.values())
                    
                    total_value = collateral + unrealized_pnl
                    
                    total_collateral += collateral
                    total_unrealized_pnl += unrealized_pnl
                    total_realized_pnl += realized_pnl
                    total_allocated_margin += allocated_margin
                    total_total_value += total_value
                    
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
                    print(f"Error for index {index}: {e.body if hasattr(e, 'body') else str(e)}")
                    continue
            
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
            
            available_margin = total_collateral - total_allocated_margin
            print(f"Available Margin:        ${available_margin:,.2f} USDC")
            
    except Exception as e:
        print(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()

def main():
    import sys
    l1_address = sys.argv[1] if len(sys.argv) > 1 else None
    asyncio.run(get_lighter_account_values(l1_address))

if __name__ == "__main__":
    main()
