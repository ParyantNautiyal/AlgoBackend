from kiteconnect import KiteConnect
import os,time
from datetime import datetime

def generate_access_token():
    # Kite Connect API credentials
    api_key = "009u7xstbslxsuxd"
    api_secret = "x5093s6jiybch29fw4dgydnhcwvnai89"
    request_token = "HOXIHJNX0NfIbSqPjw4rOcVJwdswPFOC"  # You'll need to get this from the Kite login URL
    while True:
        # Initialize Kite Connect
        kite = KiteConnect(api_key=api_key)
        print(kite.login_url())
        
        request_token = input("Press Enter to continue...")
        time.sleep(30)
        break

    try:
        # Generate session
        data = kite.generate_session(request_token, api_secret=api_secret)
        access_token = data["access_token"]
        
        # Save to file
        token_file = "access_token.txt"
        with open(token_file, "w") as f:
            f.write(f"access_token={access_token}\n")
            f.write(f"generated_at={datetime.now().isoformat()}")
        
        print(f"Access token generated and saved to {token_file}")
        print(f"Access Token: {access_token}")
        
        # Set access token for kite instance
        kite.set_access_token(access_token)
        return access_token

    except Exception as e:
        print(f"Error generating access token: {str(e)}")
        return None

if __name__ == "__main__":
    generate_access_token()
