import json

# Define the users data with correct formatting
users_data = {
  "opening_mtm": "15:58",
  "start_time": "15:59",
  "chart_start_time": "16:00",
  "users": [
    {
      "userId": "SIM",
      "ip": "103.108.220.45:8556",
      "alias": "MCX"
    },
    {
      "userId": "MCX049",
      "ip": "103.108.220.45:8556",
      "alias": "Marwadi_1CR"
    },
    {
      "userId": "EQX031",
      "ip": "103.108.220.45:8556",
      "alias": "ANS_3CR"
    },
    {
      "userId": "SIM1",
      "ip": "103.108.220.46:8556",
      "alias": "SIM_1X_TESTSERVER"
    },
    {
      "userId": "CR-ROLL-STR-4L_10X",
      "ip": "103.108.220.46:8556",
      "alias": "CR-ROLL"
    },
    {
      "userId": "FA79178",
      "ip": "103.108.220.45:8556",
      "alias": "1CR"
    }
  ]
}

# Write the data to users.json with proper indentation
with open('users.json', 'w') as f:
    json.dump(users_data, f, indent=2)

print("users.json file has been successfully generated")