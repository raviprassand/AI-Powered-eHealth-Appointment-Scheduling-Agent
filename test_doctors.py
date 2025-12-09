import requests
import json

# URL to your doctors table in the E-Hospital API
url = "https://aetab8pjmb.us-east-1.awsapprunner.com/table/doctors_registration"

print("📡 Sending GET request to:", url)

try:
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()

    print("\n✅ Response received successfully!")
    print(f"🔢 Type of response: {type(data)}")
    print(f"🧩 Keys in response (if dict): {list(data.keys()) if isinstance(data, dict) else 'N/A'}")

    if isinstance(data, dict) and "data" in data:
        print("\n📄 Showing first 2 rows from 'data':")
        print(json.dumps(data["data"][:2], indent=2))
    else:
        print("❌ Unexpected data format:", data)

except requests.exceptions.RequestException as e:
    print("❌ Error fetching doctor records:", e)
