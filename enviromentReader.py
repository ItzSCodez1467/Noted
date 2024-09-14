from dotenv import load_dotenv
import os

def getSecretKey() -> str:
    load_dotenv()
    return str(os.getenv('SECRET_KEY'))