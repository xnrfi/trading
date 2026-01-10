import asyncio
import os
from dotenv import load_dotenv
import lighter
from lighter.exceptions import ApiException

load_dotenv()

async def get_lighter_account_values():
    api_key_private_key = os.getenv("API_KEY_PRIVATE_KEY")
    api_key_index = int(os.getenv("API_KEY_INDEX", "3"))
    main_account_index = int(os.getenv("MAIN_ACCOUNT_INDEX"))
    
    if not api_key_private_key:
        print("ERROR: API_KEY_PRIVATE_KEY missing")
        return
    
    account_indices = [
        main_account_index,
        281474976627329,
        281474976666019,
        281474976666171
    ]
    
    print(f"Using API Key Index: {api_key_index}")
    print(f"Known account indices: {account_indices}\n")
    
    try:
        signer = lighter.SignerClient(
            url="https://mainnet.zklighter.elliot.ai",
            account_index=main_account_index,
            api_private_keys={api_key_index: api_key_private_key}
        )
        
        err = signer.check_client()
        if err is not None:
            print(f"Signer validation failed: {err}")
            return
        
        print("Signer validated successfully!\n")
        
        # Use the SignerClient as the client - but add missing attributes to avoid connection_pool error
        # The SDK expects a Configuration object, so we create one and attach the signer for signing
        config = lighter.Configuration(host="https://mainnet.zklighter.elliot.ai")
        config.connection_pool_maxsize = 10  # Add the missing attribute
        
        api_client = lighter.ApiClient(configuration=config)
        # Attach the signer to the api_client for signing private requests
        api_client.signer = signer
        
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
                
                # Call the account endpoint - the attached signer will sign the request for private data
                detail_resp = await account_api.account(by="index", value=str(index))
                
                target_account = None
                for acc in detail_resp:
                    if acc.index == index:
                        target_account = acc
                        break
                
                if not target_account:
                    print(f"  No data returned for index {index}")
                    continue
                
                collateral = float(target_account.collateral or 0)
                
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
            print("No data retrieved.")
            print("Possible reasons:")
            print(" - API key does not have read permissions for account details")
            print(" - Account has no funds and no positions (empty response)")
            print(" - SDK version mismatch")
            return
        
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

asyncio.run(get_lighter_account_values())
