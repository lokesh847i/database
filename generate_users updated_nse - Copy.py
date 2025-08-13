import json

# Define the users data with correct formatting
users_data = {
  "opening_mtm": "09:12",
  "start_time": "09:14",
  "chart_start_time": "09:15",
  "users": [
    {
      "userId": "ZZJ13048",
      "ip": "35.154.139.5:8554",
      "alias": "MARU_20_CR"
    },
    {
      "userId": "NFSTVWAP",
      "ip": "106.51.63.60:8556",
      "alias": "NFSTVWAP_1X"
    },
    {
      "userId": "DLL11594",
      "ip": "35.154.139.5:8554",
      "alias": "NAREN_20_CR"
    },
    {
      "userId": "DLL1064",
      "ip": "35.154.139.5:8554",
      "alias": "AJITH_10_CR"
    },
    {
      "userId": "EQX032",
      "ip": "35.154.139.5:8554",
      "alias": "ANS_3_CR"
    },
    {
      "userId": "NIFSG",
      "ip": "35.154.139.5:8554",
      "alias": "SIM_1X"
    },
    {
      "userId": "TY03",
      "ip": "15.207.159.210:8554",
      "alias": "SHAREINDIA_12 _CR"
    },
    {
      "userId": "MC0444",
      "ip": "15.207.159.210:8554",
      "alias": "MARWAD_10_CR"
    },
    {
      "userId": "BACKENZO",
      "ip": "15.207.159.210:8554",
      "alias": "S-SIM_1X"
    },
    {
      "userId": "MC0489",
      "ip": "15.207.159.210:8554",
      "alias": "MARWADI_10_CR"
    },
    {
      "userId": "X01",
      "ip": "52.66.83.113:8554",
      "alias": "SHAREINDIA_20_CR"
    },
    {
      "userId": "KEVAL",
      "ip": "52.66.83.113:8554",
      "alias": "RIKHAV_5_CR"
    },
    {
      "userId": "USER17",
      "ip": "52.66.83.113:8554",
      "alias": "ADROIT_5_CR"
    },
    {
      "userId": "BBUYING",
      "ip": "52.66.83.113:8554",
      "alias": "B-SIM_1X"
    },
    {
      "userId": "DLL9420",
      "ip": "52.66.83.113:8554",
      "alias": "ROHITH_3_CR"
    },
    {
      "userId": "DLL13227",
      "ip": "52.66.83.113:8554",
      "alias": "NISHA_2_CR"
    }
  ]
}

# Write the data to users.json with proper indentation
with open('users.json', 'w') as f:
    json.dump(users_data, f, indent=2)

print("users.json file has been successfully generated")