import requests
import nltk
import torch
import tiktoken
from bs4 import BeautifulSoup
from googlesearch import search
import re
import os
from dotenv import load_dotenv
from newspaper import Article
from urllib.parse import urlencode



load_dotenv()
API_KEY = os.getenv("SCRAPER_API")

def search_websites(prompt):
    websites = []
    text = []
    for url in search(prompt, num_results=5):
        print(f"Fetching: {url}")
        try:
            article = Article(url)
            article.download()
            article.parse()

            websites.append(article.html)
            text.append(article.text[0:])
        except Exception as e:
            print(f"Error processing {url}: {e}")
            text.append('')

    return text

prompt = input("Enter your prompt: ")
text = search_websites(prompt)
raw_output_path = f"raw_model_output_{i}.txt"
with open(raw_output_path, "w", encoding="utf-8") as f:
    f.write(result)
print(f"📝 Raw model output saved to {raw_output_path}")

