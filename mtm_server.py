# mtm_server.py
# File 3: Server setup and configuration

from mtm_imports import *
from mtm_cache import *

app = FastAPI(title="MarvelQuant Central Hub")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files (for logo)
# Create a static directory if it doesn't exist
os.makedirs("static", exist_ok=True)

# Copy the logo to the static directory
if os.path.exists("MQ-Logo-Main.svg"):
    import shutil
    shutil.copy("MQ-Logo-Main.svg", "static/MQ-Logo-Main.svg")
    logger.info("Copied logo to static directory")

# Mount the static directory
app.mount("/static", StaticFiles(directory="static"), name="static")

# Standard headers for requests
headers = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'Accept-Language': 'en-US,en;q=0.9',
    'Cache-Control': 'max-age=0',
    'Connection': 'keep-alive',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
}

# Function to get user data from users.json
def get_user_data():
    try:
        with open("users.json", "r") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load users.json: {str(e)}", exc_info=True)
        # Return empty user data instead of defaults
        return {"users": []}

# Create default users.json if it doesn't exist
if not os.path.exists("users.json"):
    with open("users.json", "w") as f:
        # Creating an empty users array
        json.dump({"users": []}, f, indent=2)
    logger.info("Created empty users.json file")
