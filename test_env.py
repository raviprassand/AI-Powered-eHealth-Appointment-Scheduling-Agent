import os
from dotenv import load_dotenv

print("📁 Current working directory:", os.getcwd())

env_path = os.path.join(os.getcwd(), ".env")
print("🔍 Looking for:", env_path)

loaded = load_dotenv(dotenv_path=env_path)
print("✅ load_dotenv() returned:", loaded)

key = os.getenv("OPENAI_API_KEY")
print("🔑 OPENAI_API_KEY:", key[:20] if key else "❌ Not found")

