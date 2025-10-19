from dotenv import load_dotenv
import os

load_dotenv()
print("Mode:", os.getenv("QBO_MODE"))
print("Logs path:", os.getenv("LOGS_CSV"))
