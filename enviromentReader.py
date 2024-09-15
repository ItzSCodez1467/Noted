from dotenv import load_dotenv
import os

def getSecretKey() -> str:
    load_dotenv()
    return str(os.getenv('SECRET_KEY'))

def getRecaptchaSecretKey() -> str:
    load_dotenv()
    return str(os.getenv('RECAPTCHA_SECRET_KEY'))

def getRecaptchaSiteKey() -> str:
    load_dotenv()
    return str(os.getenv('RECAPTCHA_SITE_KEY'))