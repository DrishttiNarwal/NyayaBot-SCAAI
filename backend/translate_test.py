import os
from dotenv import load_dotenv
from openai import OpenAI

# Load API key from .env
load_dotenv()
API_KEY = os.getenv("DEESEEK_API_KEY")

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=API_KEY,
)

completion = client.chat.completions.create(
    model="deepseek/deepseek-r1-0528:free",  # free tier model (if available)
    messages=[
        {"role": "system", "content": "You are a helpful translator."},
        {"role": "user", "content": "Translate the following English text to Hindi: 'Hello, how are you?' "}
    ]
)

print("✅ Translation Output:", completion.choices[0].message.content)
