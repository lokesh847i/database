import json

# Define the users data with correct formatting
users_data = {
  "opening_mtm": "09:12",
  "start_time": "09:14",
  "chart_start_time": "09:15",
  "users": [
    {
      "userId": "ZZJ13048",
      "ip": "103.108.220.45:8556",
      "alias": "MARU_15_CR"
    },
    {
      "userId": "X12",
      "ip": "103.108.220.45:8556",
      "alias": "X12_12_CR"
    },
    {
      "userId": "NFSTVWAP",
      "ip": "103.108.220.46:8556",
      "alias": "NFSTVWAP_SIM_1X"
    },
    {
      "userId": "EQ",
      "ip": "103.108.220.46:8556",
      "alias": "EQ_SIM_1X"
    },
    {
      "userId": "X06",
      "ip": "103.108.220.45:8556",
      "alias": "X06_8_CR"
    },
    {
      "userId": "DLL1064",
      "ip": "103.108.220.45:8556",
      "alias": "AJITH_10_CR"
    },
    {
      "userId": "EQX032",
      "ip": "103.108.220.45:8556",
      "alias": "ANS_3_CR"
    },
    {
      "userId": "TY03",
      "ip": "103.108.220.47:8556",
      "alias": "SHAREINDIA_12 _CR"
    },
    {
      "userId": "MC0444",
      "ip": "103.108.220.47:8556",
      "alias": "MARWAD_10_CR"
    },
    {
      "userId": "BACKENZO",
      "ip": "103.108.220.45:8556",
      "alias": "S-SIM_1X"
    },
    {
      "userId": "MC0489",
      "ip": "103.108.220.45:8556",
      "alias": "MARWADI_10_CR"
    },
    {
      "userId": "KEVAL",
      "ip": "103.108.220.47:8556",
      "alias": "RIKHAV_5_CR"
    },
    {
      "userId": "BBUYING",
      "ip": "103.108.220.47:8556",
      "alias": "B-SIM_1X"
    },
    {
      "userId": "DLL9420",
      "ip": "103.108.220.47:8556",
      "alias": "ROHITH_3_CR"
    },
    {
      "userId": "ZZJ15639",
      "ip": "103.108.220.47:8556",
      "alias": "NISHA_2_CR"
    }
  ]
}

# Write the data to users.json with proper indentation
with open('users.json', 'w') as f:
    json.dump(users_data, f, indent=2)

print("users.json file has been successfully generated")