from api_helper import ShoonyaApiPy
import logging
import sys

# Enable debug logging
logging.basicConfig(level=logging.INFO)

def get_input(prompt, default=None):
    try:
        return input(prompt) or default
    except EOFError:
        return default

# Credentials
user = 'FA46356'
pwd = 'Reiner@321'
factor2 = get_input('Enter your current 2FA code (6-digit from authenticator app): ')
vc = 'FA46356_U'
app_key = '6329432903250ad6b1d25e897e11afd2'
imei = 'abc1234'

# Initialize API
api = ShoonyaApiPy()

# Login
ret = api.login(userid=user, password=pwd, twoFA=factor2, vendor_code=vc, api_secret=app_key, imei=imei)
if not ret or ret.get('stat') != 'Ok':
    print('Login failed:', ret)
    sys.exit(1)
print('Login successful!')

# Find BankNifty token (example for NFO options/futures)
search = api.searchscrip(exchange='NFO', searchtext='BANKNIFTY')
if not search or search.get('stat') != 'Ok' or not search.get('values'):
    print('Could not find BankNifty contracts:', search)
    sys.exit(1)

# List available contracts and prompt user to select one
print('Available BankNifty contracts:')
for idx, contract in enumerate(search['values']):
    print(f"{idx}: {contract['tsym']} (Token: {contract['token']})")

selected_idx = int(get_input('Select contract index for subscription: ', '0'))
selected_contract = search['values'][selected_idx]
token = selected_contract['token']
print(f"Subscribing to: {selected_contract['tsym']} (Token: {token})")

# Websocket event handlers
feed_opened = False

def event_handler_feed_update(tick_data):
    # Print LTP if available
    ltp = tick_data.get('lp') or tick_data.get('ltp')
    print(f"LTP Update for {selected_contract['tsym']}: {ltp}")

def event_handler_order_update(order_data):
    pass  # Not used for LTP

def open_callback():
    global feed_opened
    feed_opened = True
    print('WebSocket connection opened.')

# Start websocket
api.start_websocket(
    order_update_callback=event_handler_order_update,
    subscribe_callback=event_handler_feed_update,
    socket_open_callback=open_callback
)

while not feed_opened:
    pass

# Subscribe to BankNifty
api.subscribe([f'NFO|{token}'])
print('Subscribed to BankNifty. Waiting for LTP updates...')

# Keep the script running to receive updates
try:
    while True:
        pass
except KeyboardInterrupt:
    print('Exiting...')
