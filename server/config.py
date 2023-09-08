from dotenv import load_dotenv
import os
import openai

load_dotenv("../.env")
OPENAI_API_KEY = os.environ.get('OPENAI-API-KEY')
MY_API_KEY = os.environ.get('MY_API_KEY')

openai.api_key = OPENAI_API_KEY