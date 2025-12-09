import requests
import json

# Your App Runner API URL
BASE_URL = "https://aetab8pjmb.us-east-1.awsapprunner.com"
PATIENT_ID = "1"

def check_real_data():
    print(f"📡 Asking the API about Patient {PATIENT_ID}...\n")
    
    url = f"{BASE_URL}/table/patients_registration"
    try:
        # Ask the API directly
        response = requests.get(url, params={"patient_id": PATIENT_ID})
        
        if response.status_code != 200:
            print(f"❌ API Error: {response.status_code}")
            return

        data = response.json().get("data", [])
        
        if not data:
            print("❌ The API says: Patient 1 does not exist!")
            return

        patient = data[0]
        
        print(f"✅ The API sees this data for Patient 1:")
        print(json.dumps(patient, indent=2))
        
        print("\n------------------------------------------------")
        doctor_id = patient.get("family_doctor_id")
        print(f"👉 FAMILY DOCTOR ID IS: {doctor_id}")
        
        if str(doctor_id) == "1":
            print("🚨 VERDICT: The API still sees ID 1 (Makayla). Your Workbench update did not affect this app.")
        elif str(doctor_id) == "2":
            print("✅ VERDICT: The API sees ID 2 (Robin). The code logic must be stuck.")
        else:
            print(f"⚠️ VERDICT: The API sees ID {doctor_id}.")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_real_data()