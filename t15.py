import asyncio
import os
from dotenv import load_dotenv
import lighter
from lighter.exceptions import ApiException

# Load environment variables from .env file
load_dotenv()

async def get_lighter_account_values():
    """
    Fetches total account value (collateral + unrealized PNL + allocated margins from positions)
    across all known sub-accounts using the exact working pattern from your bot.
    
    Matches the fetch_balance logic: response.accounts (list) -> find matching index.
    
    .env requirements:
    API_KEY_PRIVATE_KEY=0xYourFullPrivateKeyHere
    API_KEY_INDEX=3
    MAIN_ACCOUNT_INDEX=185609
    """
    
    api_key_private_key = os.getenv("API_KEY_PRIVATE_KEY")
    api_key_index = int(os.getenv("API_KEY_INDEX", "3"))
    main_account_index = int(os.getenv("MAIN_ACCOUNT_INDEX"))
    
    if not api_key_private_key:
        print("ERROR: API_KEY_PRIVATE_KEY not found in .env")
        return
    
    # Hardcoded from your public accounts list
    account_indices = [
        main_account_index,          # Main account
        281474976627329,             # Sub-account 1
        281474976666019,             # Sub-account 2
        281474976666171              # Sub-account 3
    ]
    
    print(f"Using API Key Index: {api_key_index}")
    print(f"Known account indices: {account_indices}\n")
    
    try:
        # Create SignerClient exactly as in your working bot
        signer = lighter.SignerClient(
            url="https://mainnet.zklighter.elliot.ai",
            account_index=main_account_index,
            api_private_keys={api_key_index: api_key_private_key}
        )
        
        err = signer.check_client()
        if err is not None:
            print(f"Signer validation failed: {err}")
            print("Regenerate your API key in the Lighter app.")
            return
        
        print("Signer validated successfully!\n")
        
        # Create standard ApiClient (no token, no signer passed directly)
        # This matches your bot's CustomLighterClient.api_client
        config = lighter.Configuration(host="https://mainnet.zklighter.elliot.ai")
        async with lighter.ApiClient(configuration=config) as api_client:
            account_api = lighter.AccountApi(api_client)
            
            total_collateral = 0.0
            total_unrealized_pnl = 0.0
            total_realized_pnl = 0.0
            total_allocated_margin = 0.0
            total_total_value = 0.0
            
            accounts_summary = []
            
            for index in account_indices:
                account_type = "Main Account" if index == main_account_index else "Sub-Account"
                try:
                    print(f"Fetching {account_type} (Index: {index})...")
                    
                    # Call the account endpoint
                    response = await account_api.account(by="index", value=str(index))
                    
                    # Critical: response.accounts is the list (as in your working bot)
                    accounts_list = response.accounts
                    
                    # Find the matching account
                    target_account = None
                    for acc in accounts_list:
                        if acc.index == index:
                            target_account = acc
                            break
                    
                    if not target_account:
                        print(f"  No data returned for index {index} (possibly empty or access denied)")
                        continue
                    
                    collateral = float(target_account.collateral or 0)
                    
                    # Sum positions
                    positions = getattr(target_account, 'positions', {}) or {}
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
                    print(f"  Error for index {index}: {e}")
                    continue
                except Exception as e:
                    print(f"  Unexpected error for index {index}: {e}")
                    continue
            
            if not accounts_summary:
                print("\nNo account data retrieved.")
                print("Possible causes:")
                print(" - API key lacks permission for private account details")
                print(" - All accounts are empty (0 collateral, no positions)")
                print(" - Try regenerating the API key in the Lighter app")
                return
            
            print("\n" + "="*60)
            print("ACCOUNT DETAILS")
            print("="*60)
            
            for acc in accounts_summary:
                print(f"\n{acc['type']} (Index: {acc['index']}):")
                print(f"  Collateral:           ${acc['collateral']:,.2f} USDC")
                print(f"  Unrealized PNL:       ${acc['unrealized_pnl']:+,.2f} USDC")
                print(f"  Realized PNL:         ${acc['realized_pnl']:+,.2f} USDC (included in collateral)")
                print(f"  Allocated Margin:     ${acc['allocated_margin']:,.2f} USDC")
                print(f"  Total Account Value:  ${acc['total_value']:,.2f} USDC")
                print("-" * 50)
            
            print("\n" + "="*60)
            print("GRAND TOTAL ACROSS ALL ACCOUNTS")
            print("="*60)
            print(f"  Total Collateral:        ${total_collateral:,.2f} USDC")
            print(f"  Total Unrealized PNL:    ${total_unrealized_pnl:+,.2f} USDC")
            print(f"  Total Realized PNL:      ${total_realized_pnl:+,.2f} USDC")
            print(f"  Total Allocated Margin:  ${total_allocated_margin:,.2f} USDC")
            print(f"  GRAND TOTAL VALUE:       ${total_total_value:,.2f} USDC")
            print("="*60)
            
            available_margin = total_collateral - total_allocated_margin
            print(f"  Available Margin:        ${available_margin:,.2f} USDC")
            
    except Exception as e:
        print(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()

# Run the script
asyncio.run(get_lighter_account_values())
