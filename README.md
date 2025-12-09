# 1. Clone the repo
git clone https://github.com/raviprassand/AI-Powered-eHealth-Appointment-Scheduling-Agent.git
cd AI-Powered-eHealth-Appointment-Scheduling-Agent
git checkout backend

# 2. Create environment
python3 -m venv venv
source venv/bin/activate    # Mac/Linux
# venv\Scripts\activate     # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create .env file in backend folder
DB_HOST=DEV01
DB_PORT=3306
DB_USER=<your_db_user>
DB_PASSWORD=<your_db_password>
DB_NAME=<your_db_name>

# 5. Run backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
