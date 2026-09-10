import os
import json
import asyncio
from google import genai
from google.genai import types

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

domains = [
    "Công nghệ Thông tin (IT)",
    "Y khoa / Sức khỏe",
    "Kinh tế / Tài chính",
    "Kỹ thuật Cơ khí",
    "Luật / Pháp lý"
]

system_prompt = """
You are an expert bilingual lexicographer (English - Vietnamese). 
For the requested domain, generate exactly 100 common, specialized, and highly used vocabulary terms or short phrases (max 3 words).
Return the result EXACTLY as a raw JSON array of objects, with no markdown formatting, no code blocks, and no extra text.
Each object must have the following structure:
{
    "domain": "<The exact domain string provided>",
    "word": "<English word>",
    "translation": "<Vietnamese meaning>"
}
"""

async def generate_for_domain(client, domain):
    print(f"Generating 100 words for domain: {domain}...")
    user_prompt = f"Domain: '{domain}'. Generate exactly 100 entries."
    
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=f"{system_prompt}\n\n{user_prompt}",
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.2
            )
        )
        data = json.loads(response.text)
        print(f"Successfully generated {len(data)} words for {domain}.")
        return data
    except Exception as e:
        print(f"Error for domain {domain}: {e}")
        return []

async def main():
    client = genai.Client(api_key=GEMINI_API_KEY)
    
    tasks = [generate_for_domain(client, domain) for domain in domains]
    results = await asyncio.gather(*tasks)
    
    all_entries = []
    for res in results:
        all_entries.extend(res)
        
    output_file = "import_dictionary_data.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(all_entries, f, ensure_ascii=False, indent=4)
        
    print(f"\nTotal entries generated: {len(all_entries)}")
    print(f"Data saved to {output_file}")

if __name__ == "__main__":
    asyncio.run(main())
