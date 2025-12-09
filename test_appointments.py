import requests
import json

url = "https://aetab8pjmb.us-east-1.awsapprunner.com/table/appointments"

print("📡 Sending GET request to:", url)

try:
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()

    print("\n✅ Response received successfully!")
    print(f"🔢 Type of response: {type(data)}")
    print(f"🧩 Keys in response (if dict): {list(data.keys()) if isinstance(data, dict) else 'N/A'}")

    # Check if the data is a dict containing rows
    if isinstance(data, dict):
        # Some APIs return data under a key like 'rows' or 'data'
        for key, value in data.items():
            if isinstance(value, list):
                print(f"\n📄 Showing first 2 rows from key '{key}':")
                print(json.dumps(value[:2], indent=2))
                break
    elif isinstance(data, list):
        print("\n📄 Showing first 2 rows directly:")
        print(json.dumps(data[:2], indent=2))
    else:
        print("❌ Unexpected data format:", data)

except requests.exceptions.RequestException as e:
    print("❌ Error fetching appointments:", e)
