from kiteconnect import KiteConnect
from decouple import config

config_key = config("KITE_API_KEY")
config_secret = config("KITE_API_SECRET")
config_access_token = config("KITE_ACCESS_TOKEN")
config_request_token = config("KITE_REQUEST_TOKEN")

class KiteApp:
    def __init__(self):
        self.api_key = config_key
        self.api_secret = config_secret
        self.kite = KiteConnect(api_key=self.api_key)
        self.access_token = config_access_token

    def set_access_token(self, request_token=config_request_token):
        """Generate and set access token using request token"""
        try:
            data = self.kite.generate_session(request_token, api_secret=self.api_secret)
            self.access_token = data["access_token"]
            self.kite.set_access_token(self.access_token)
            return True
        except Exception as e:
            print(f"Error setting access token: {str(e)}")
            return False

    def get_instruments(self):
        """Fetch all instruments"""
        try:
            return self.kite.instruments()
        except Exception as e:
            print(f"Error fetching instruments: {str(e)}")
            return None 