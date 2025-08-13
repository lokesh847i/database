import requests
import hmac
import hashlib
import time
import json
import webbrowser
from datetime import datetime
from typing import Dict, List, Optional
import urllib.parse

class KiteConnectAPI:
    def __init__(self, api_key: str, api_secret: str, redirect_url: str = "http://localhost:8000/login"):
        """
        Initialize the Kite Connect API client
        
        Args:
            api_key (str): Your Kite Connect API key
            api_secret (str): Your Kite Connect API secret
            redirect_url (str): Redirect URL configured in your app
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.redirect_url = redirect_url
        self.base_url = "https://api.kite.trade"
        self.session = requests.Session()
        self.access_token = None
        
    def get_login_url(self) -> str:
        """
        Generate login URL for user authentication
        
        Returns:
            str: Login URL to redirect user
        """
        params = {
            'api_key': self.api_key,
            'v': '3'
        }
        query_string = urllib.parse.urlencode(params)
        login_url = f"{self.base_url}/connect/login?{query_string}"
        return login_url
    
    def generate_session(self, request_token: str) -> Dict:
        """
        Generate session using request token
        
        Args:
            request_token (str): Request token received after login
            
        Returns:
            Dict: Session data with access token
        """
        url = f"{self.base_url}/session/token"
        
        data = {
            'api_key': self.api_key,
            'request_token': request_token,
            'checksum': self._generate_checksum(request_token)
        }
        
        try:
            response = self.session.post(url, data=data)
            response.raise_for_status()
            session_data = response.json()
            
            if session_data.get('status') == 'success':
                self.access_token = session_data['data']['access_token']
                return session_data
            else:
                return {"error": "Session generation failed"}
                
        except requests.exceptions.RequestException as e:
            return {"error": f"Session generation failed: {e}"}
    
    def _generate_checksum(self, request_token: str) -> str:
        """
        Generate checksum for API calls
        
        Args:
            request_token (str): Request token
            
        Returns:
            str: Generated checksum
        """
        message = self.api_key + request_token + self.api_secret
        checksum = hashlib.sha256(message.encode('utf-8')).hexdigest()
        return checksum
    
    def _make_authenticated_request(self, method: str, endpoint: str, params: Dict = None, data: Dict = None) -> Dict:
        """
        Make authenticated API request
        
        Args:
            method (str): HTTP method
            endpoint (str): API endpoint
            params (Dict): Query parameters
            data (Dict): Request body data
            
        Returns:
            Dict: API response
        """
        if not self.access_token:
            return {"error": "No access token. Please authenticate first."}
        
        url = f"{self.base_url}{endpoint}"
        
        headers = {
            'X-KiteConnect-Version': '3',
            'Authorization': f'token {self.api_key}:{self.access_token}'
        }
        
        try:
            if method.upper() == 'GET':
                response = self.session.get(url, headers=headers, params=params)
            elif method.upper() == 'POST':
                response = self.session.post(url, headers=headers, json=data)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"API request failed: {e}")
            return {"error": str(e)}
    
    def get_user_profile(self) -> Dict:
        """
        Get user profile information
        
        Returns:
            Dict: User profile data
        """
        return self._make_authenticated_request('GET', '/user/profile')
    
    def get_margins(self, segment: str = "equity") -> Dict:
        """
        Get margin information
        
        Args:
            segment (str): Trading segment (equity, commodity)
            
        Returns:
            Dict: Margin data
        """
        params = {'segment': segment}
        return self._make_authenticated_request('GET', '/user/margins', params=params)
    
    def get_orders(self) -> Dict:
        """
        Get order history
        
        Returns:
            Dict: Order history
        """
        return self._make_authenticated_request('GET', '/orders')
    
    def get_positions(self) -> Dict:
        """
        Get current positions
        
        Returns:
            Dict: Position data
        """
        return self._make_authenticated_request('GET', '/portfolio/positions')
    
    def get_holdings(self) -> Dict:
        """
        Get portfolio holdings
        
        Returns:
            Dict: Holdings data
        """
        return self._make_authenticated_request('GET', '/portfolio/holdings')
    
    def get_instruments(self, exchange: str = "NSE") -> Dict:
        """
        Get instruments list
        
        Args:
            exchange (str): Exchange (NSE, BSE, NFO, etc.)
            
        Returns:
            Dict: Instruments data
        """
        params = {'exchange': exchange}
        return self._make_authenticated_request('GET', '/instruments', params=params)
    
    def get_quote(self, instruments: List[str]) -> Dict:
        """
        Get quote for instruments
        
        Args:
            instruments (List[str]): List of instruments (format: exchange:token)
            
        Returns:
            Dict: Quote data
        """
        params = {'i': instruments}
        return self._make_authenticated_request('GET', '/quote', params=params)
    
    def get_historical_data(self, instrument_token: str, from_date: str, to_date: str, 
                          interval: str = "day", continuous: bool = True) -> Dict:
        """
        Get historical data
        
        Args:
            instrument_token (str): Instrument token
            from_date (str): Start date (YYYY-MM-DD)
            to_date (str): End date (YYYY-MM-DD)
            interval (str): Interval (minute, day, 3minute, 5minute, 10minute, 15minute, 30minute, 60minute)
            continuous (bool): Whether to get continuous data
            
        Returns:
            Dict: Historical data
        """
        params = {
            'instrument_token': instrument_token,
            'from': from_date,
            'to': to_date,
            'interval': interval,
            'continuous': continuous
        }
        return self._make_authenticated_request('GET', '/instruments/historical', params=params)
    
    def place_order(self, variety: str, exchange: str, tradingsymbol: str, 
                   transaction_type: str, quantity: int, product: str = "CNC",
                   order_type: str = "MARKET", price: float = None) -> Dict:
        """
        Place an order
        
        Args:
            variety (str): Order variety (regular, amo, co, iceberg)
            exchange (str): Exchange (NSE, BSE, NFO, etc.)
            tradingsymbol (str): Trading symbol
            transaction_type (str): BUY or SELL
            quantity (int): Quantity
            product (str): Product type (CNC, MIS, NRML)
            order_type (str): Order type (MARKET, LIMIT, SL, SL-M)
            price (float): Price (required for LIMIT orders)
            
        Returns:
            Dict: Order response
        """
        data = {
            'variety': variety,
            'exchange': exchange,
            'tradingsymbol': tradingsymbol,
            'transaction_type': transaction_type,
            'quantity': quantity,
            'product': product,
            'order_type': order_type
        }
        
        if price:
            data['price'] = price
            
        return self._make_authenticated_request('POST', '/orders/regular', data=data)

def main():
    """
    Main function to demonstrate Kite Connect API usage
    """
    # Your Kite Connect API credentials
    API_KEY = "rzvzfgf32o874pb2"  # Replace with your actual Kite Connect API key
    API_SECRET = "n3oj3fw2psr7fayvc0s641j07oy62ih7"  # Replace with your actual API secret
    
    # Initialize API client
    kite = KiteConnectAPI(API_KEY, API_SECRET)
    
    print("=== Kite Connect API Demo ===\n")
    
    # Step 1: Generate login URL
    print("1. Generating login URL...")
    login_url = kite.get_login_url()
    print(f"Login URL: {login_url}")
    print("Please visit this URL in your browser to authenticate.")
    print("-" * 50)
    
    # Note: In a real application, you would:
    # 1. Open the login URL in a browser
    # 2. User logs in and gets redirected with request_token
    # 3. Use the request_token to generate session
    
    print("\n2. After authentication, you can use the following methods:")
    print("   - kite.generate_session(request_token)")
    print("   - kite.get_user_profile()")
    print("   - kite.get_margins()")
    print("   - kite.get_orders()")
    print("   - kite.get_positions()")
    print("   - kite.get_holdings()")
    print("   - kite.get_instruments()")
    print("   - kite.get_quote()")
    print("   - kite.get_historical_data()")
    print("   - kite.place_order()")
    
    print("\n3. Example usage after authentication:")
    print("""
    # Generate session
    session_data = kite.generate_session(request_token)
    
    # Get user profile
    profile = kite.get_user_profile()
    print(profile)
    
    # Get quotes for specific instruments
    quotes = kite.get_quote(['NSE:RELIANCE', 'NSE:TCS'])
    print(quotes)
    
    # Get historical data
    historical = kite.get_historical_data(
        instrument_token='123456',
        from_date='2024-01-01',
        to_date='2024-01-31',
        interval='day'
    )
    print(historical)
    """)

if __name__ == "__main__":
    main() 