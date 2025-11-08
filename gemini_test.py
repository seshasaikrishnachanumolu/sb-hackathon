import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

print("Listing models...")
for m in genai.list_models():
    print(" -", m.name)

response = genai.GenerativeModel("gemini-1.5-flash").generate_content("Say hello in one line.")
print("\nResponse:", response.text)
