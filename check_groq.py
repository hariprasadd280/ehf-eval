import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    print("❌ GROQ_API_KEY is missing from your .env file!")
    exit(1)

client = Groq(api_key=api_key)

print("🔍 Fetching active models from Groq...")
try:
    models_list = client.models.list()
    active_models = [m.id for m in models_list.data]
    print("✅ Groq Connection Successful!")
    print("\nAvailable Groq Models on your key:")
    for m in active_models:
        print(f"  - {m}")
        
    # Quick test completion on the first available chat model
    test_model = active_models[0]
    print(f"\n🚀 Testing completion on model: '{test_model}'...")
    res = client.chat.completions.create(
        model=test_model,
        messages=[{"role": "user", "content": "Return the single word: OK"}],
        max_tokens=10
    )
    print(f"Response: {res.choices[0].message.content.strip()}")

except Exception as e:
    print(f"❌ Error testing Groq: {e}")