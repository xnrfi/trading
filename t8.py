import asyncio
import os
from dotenv import load_dotenv
import lighter
from lighter.exceptions import ApiException

load_dotenv()

async def get_lighter_account_values(l1_address: str = None):
    api_key_private_key = os.getenv("API_KEY_PRIVATE_KEY")
    api_key_index = int(os.getenv("API_KEY_INDEX", "3"))
    account_index = int(os.getenv("MAIN_ACCOUNT_INDEX"))
    l1_address = l1_address or os.getenv("L1_ADDRESS")
    
    if not all([api_key_private_key, l1_address]):
        print("ERROR: Missing required .env vars")
        return
    
    print(f"Using L1: {l1_address}")
    print(f"Using Account Index: {account_index}")
    print(f"Using API Key Index: {api_key_index}")
    
    try:
        # Try this first (matches some docs)
        signer = lighter.SignerClient(
            url="https://mainnet.zklighter.elliot.ai",
            account_index=account_index,
            private_key=api_key_private_key,
            api_key_index=api_key_index
        )
    except TypeError:
        # Fallback to dict version (matches your bot and some examples)
        signer = lighter.SignerClient(
            url="https://mainnet.zklighter.elliot.ai",
            account_index=account_index,
            api_private_keys={api_key_index: api_key_private_key}
        )
    
    print("Signer created")
    
    err = signer.check_client()
    if err is not None:
        print(f"CRITICAL: Signer validation failed: {err}")
        print("→ Wrong MAIN_ACCOUNT_INDEX, API_KEY_PRIVATE_KEY, or API_KEY_INDEX")
        print("→ Regenerate API key in app and update .env")
        return
    print("Signer validated successfully with server!")
    
    auth_token, err = signer.create_auth_token_with_expiry()
    if err is not None:
        print(f"Token generation failed: {err}")
        return
    print("Auth token generated")
    
    config = lighter.Configuration(host="https://mainnet.zklighter.elliot.ai")
    config.access_token = auth_token
    
    async with lighter.ApiClient(config) as api_client:
        account_api = lighter.AccountApi(api_client)
        
        try:
            accounts_resp = await account_api.accounts_by_l1_address(l1_address=l1_address.lower())
            sub_accounts = accounts_resp.data.sub_accounts or []
            print(f"Success! Found {len(sub_accounts)} account(s)")
            # ... rest of printing code same as before
        except ApiException as e:
            print(f"API call failed: {e}")
            if '21100' in str(e):
                print("Still 'account not found' → API key not linked to this L1/main index")

def main():
    import sys
    l1_address = sys.argv[1] if len(sys.argv) > 1 else None
    asyncio.run(get_lighter_account_values(l1_address))

if __name__ == "__main__":
    main()
