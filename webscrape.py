import requests
from bs4 import BeautifulSoup
import re
import json
from openai import OpenAI
import os
import dotenv
import warnings
from urllib3.exceptions import InsecureRequestWarning

warnings.simplefilter("ignore", InsecureRequestWarning)

# Load environment
dotenv.load_dotenv()
NVIDIA_API_KEY = os.getenv("nvidia_api_key")
if not NVIDIA_API_KEY:
    raise ValueError("NVIDIA_API_KEY not found in .env")

client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key=NVIDIA_API_KEY,
)
base_url = "https://keralapolice.gov.in"
session = requests.Session()

def extract_main_content(page_path: str):
   
    try:
        page_path=page_path.strip()
        full_url = f"{page_path}" if page_path else base_url
        response = session.get(full_url, timeout=10, verify=False)
        soup = BeautifulSoup(response.text, 'html.parser')

        for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
            tag.decompose()

        title = soup.title.string.strip() if soup.title else "Kerala Police"

        main_content = soup.find("body")

        if main_content:
            lines = (line.strip() for line in main_content.stripped_strings)
            body_text = "\n".join(line for line in lines if line)
        else:
            print("No content found")
            body_text = ""
            return 0

        return {
            "url": full_url,
            "title": title,
            "content": body_text
        }

    except Exception as e:
        print(f"Error scraping {full_url}: {e}")
        return {"url": full_url, "title": "", "content": ""}
session.get(f"{base_url}", timeout=10, verify=False)
print("Initial page loaded")
session.get(f"{base_url}/switch/language/en",verify=False)
print("loaded english content")
while True:
    print("Enter the page path:")
    page_path = input()
    data = extract_main_content(page_path)

    prompt = f"""
You are an expert data curator building a retrieval-augmented generation (RAG) knowledge base from the official Kerala Police website.  
Your task is to analyze the provided webpage content and extract **only factual, self-contained, and semantically coherent information blocks** that would be useful for citizens, researchers, or law enforcement personnel seeking accurate information.

### Instructions:
1. **Extract all meaningful content** — do not truncate, summarize, or omit details. Full context is critical for RAG.
2. **Preserve original meaning** — rephrase only if needed for clarity; never invent or assume facts.
3. **Segment unrelated topics**:  
   - If the page contains multiple distinct subjects (e.g., "Traffic Rules" and "Recruitment 2024"), treat each as a separate document.  
   - Each must have its own `Title` and `Content`.
4. **Include contact details** (phone numbers, emails, addresses) **within the relevant content section**—do not isolate them.
5. **Convert tables** into clear, natural-language descriptions or structured lists (e.g., "Eligibility Criteria: [list items]").
6. **Ignore**: navigation menus, footer links, "Print" buttons, breadcrumbs, legal disclaimers, or repetitive headers/footers.
7. **Use the original page title** only if it accurately reflects the content. Otherwise, create a concise, descriptive title.

### Output Format:
- Return **valid JSON only** — no markdown, no extra text.
- If multiple topics exist, output a **JSON array** of objects.
- Each object must have exactly two keys: `"Title"` and `"Content"` (both strings).
- If no relevant content exists, return an empty array: `[]`

### Input:
TITLE: {data['title']}
CONTENT:
{data['content']}

### Output:
"""

    folder_name='data'
    if data:
        try:
            completion = client.chat.completions.create(
                model="qwen/qwen3-coder-480b-a35b-instruct",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                top_p=0.7,
                max_tokens=28000,
            )
            result = completion.choices[0].message.content.strip()

            # Try to parse JSON (in case LLM adds ```json...```)
            if result.startswith("```json"):
                result = result[7:-3].strip()
            elif result.startswith("```"):
                result = result[3:-3].strip()

            structured_data = json.loads(result)

            if isinstance(structured_data, dict):
                structured_data = [structured_data]
            
            for idx,item in enumerate(structured_data):
                title=item['Title']
                content=item['Content']
                print("Found item ID:", idx, "item Title:", title)

                safe_title = re.sub(r'[<>:"/\\|?*]', '', title)  # Remove forbidden chars
                safe_title = safe_title.strip().replace(' ', '_')  # Optional: replace spaces with underscores
                if(len(content)<100):
                    continue
                ch=input("Proceed for writing (Y/n): ")
                if(ch=='n'):
                    continue
                filename = f"data/{safe_title}.txt"
                
                with open(filename, "w", encoding="utf-8") as f:
                    print("Writing to file:", filename)
                    f.write(json.dumps(item, indent=2, ensure_ascii=False))

        except Exception as e:
            print(f"❌ Error: {e}")
            print("Raw LLM output:")
            print(result)
