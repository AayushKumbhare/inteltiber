import requests
from bs4 import BeautifulSoup
from googlesearch import search
import re
import os
from dotenv import load_dotenv
from newspaper import Article
from urllib.parse import urlencode
from datetime import datetime


load_dotenv()
API_KEY = os.getenv("SCRAPER_API")

def search_websites(prompt):
    websites = []
    text = []
    for url in search(prompt, num_results=7):
        print(f"Fetching: {url}")
        try:
            article = Article(url)
            article.download()
            article.parse()

            websites.append(article.html)
            text.append(article.text.strip())
        except Exception as e:
            print(f"Error processing {url}: {e}")
            text.append('')

    return text

# --- MAIN EXECUTION ---
prompt = input("Enter your prompt: ")
texts = search_websites(prompt)

# Join all scraped text into one string
combined_text = "\n\n---\n\n".join(texts)

# Save to file
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
raw_output_path = f"raw_model_output.txt"

with open(raw_output_path, "w", encoding="utf-8") as f:
    f.write(combined_text)

print(f"Raw model output saved to {raw_output_path}")