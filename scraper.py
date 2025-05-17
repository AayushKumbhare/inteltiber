import requests
import torch
import tiktoken
from bs4 import BeautifulSoup
from googlesearch import search
import re
import os
from dotenv import load_dotenv
from transformers import pipeline
from huggingface_hub import hf_hub_download
from sentence_transformers import SentenceTransformer, util
from langchain.text_splitter import RecursiveCharacterTextSplitter, TokenTextSplitter
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
from newspaper import Article
from urllib.parse import urlencode
from pinecone import Pinecone
import hashlib


load_dotenv()
HUGGING_FACE_API_KEY = os.getenv("HUGGING_FACE_API_KEY")
API_KEY = os.getenv("SCRAPER_API")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")

pipe = pipeline("text-generation", model="TinyLlama/TinyLlama-1.1B-Chat-v1.0", torch_dtype=torch.bfloat16, device_map="auto")
tokenizer = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
pc = Pinecone(api_key=PINECONE_API_KEY, environment="us-west1-gcp")

def search_websites(prompt):
    websites = []
    text = []
    s = search(prompt, num_results=3)


    for website in s:
        article = Article(website)
        payload = {'api_key': API_KEY, 'url': website}
        response = requests.get('https://api.scraperapi.com', params=urlencode(payload))
        article.download(input_html=response.text)
        article.parse()
        websites.append(article.html)
        text.append(article.text)
        
    return text


def chunk_text(texts, max_token_limit=1600, model_name="gpt2"):
    splitter = TokenTextSplitter(encoding_name=model_name, chunk_size=max_token_limit, chunk_overlap=50)

    all_chunks = []
    for text in texts:
        chunks = splitter.split_text(text)
        all_chunks.extend(chunks)
    return all_chunks

def call_llm(text, resume=None):
    messages = [
        {
            "role": "system", 
            "content": """
                        You are a question extraction engine. Your task is to read scraped text related to job interviews and extract only professional interview questions. 

                            - Do NOT repeat or summarize any part of the input.
                            - Do NOT generate answers, commentary, or explanations.
                            - Do NOT copy article sentences or paragraphs.
                            - Only extract short, clear, professional interview questions that a human might ask during a real interview.
                            - Return a valid JSON array of question strings, each 1-2 lines max.
                            - Each string must be a grammatically correct, stand-alone question.
                            - If no questions are present, return an empty array: []
            """},
        {
            "role": "user",
            "content": f"Text: {text}\nResume: {resume if resume else ''}"
        }
    ]
    try:
        prompt = pipe.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )
        
        outputs = pipe(
            prompt,
            max_new_tokens=256,
            do_sample=True,
            temperature=0.7,
            top_k=50,
            top_p=0.95,
            num_return_sequences=1
        )
        
        return outputs[0]["generated_text"]
        
    except Exception as e:
        print(f"Error generating questions: {str(e)}")
        return ""
    

def question_optimize(chunks):
    all_questions = []
    for chunk in chunks:
        questions = call_llm(chunk)
        all_questions.append(questions)
    return all_questions


#gets model answer to interview question
def model_response(question, resume=None):
    messages = [
        {
            "role": "system",
            "content": "You are a model interviewee currently in a job interview. You always answers using proper interview format and ettiquette to ensure the most accurate, efficient, and canonical solutions to interview questions",
        },
        {"role": "user", "content": question},
    ]
    if resume is not None:
        messages.append({"role": "user", "content": resume})
    prompt = pipe.tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    outputs = pipe(prompt, max_new_tokens=256, do_sample=True, temperature=0.7, top_k=50, top_p=0.95)
    text_output = outputs[0]["generated_text"]
    return text_output


#converts into tokens
def embed(input):
    return tokenizer.encode(input).tolist()

#generates similarty score
def similarity_score(input1, input2):
    return util.pytorch_cos_sim(input1, input2).item()

def vector_storage(texts):
    index_name = 'interview-questions'

    if index_name not in pc.list_indexes():
        pc.create_index(
            name=index_name,
            dimension=384,
            metric="cosine",
        )

    index = pc.Index(index_name)

    chunks = chunk_text(texts)
    vectors = []

    for chunk in chunks:
        vector_id = hash_text(chunk)
        vector = embed(chunk)
        vectors.append((vector_id, vector, {"text": chunk}))

    index.upsert(vectors)


def hash_text(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


texts = search_websites("software engineer interview questions")
vector_storage(texts)

chunks = chunk_text(texts)
questions = question_optimize(chunks)

for q in questions:
    print(q)
