import os
import boto3
from dotenv import load_dotenv
import requests
import re
import time
from collections import Counter
import spacy
from datetime import datetime
from amazon_transcribe.client import TranscribeStreamingClient
from amazon_transcribe.handlers import TranscriptResultStreamHandler
from amazon_transcribe.model import TranscriptEvent
import json

load_dotenv()
access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")
region = os.getenv("AWS_REGION")

transcribe_client = boto3.client('transcribe', region_name=region, aws_access_key_id=access_key_id, aws_secret_access_key=secret_access_key)
s3 = boto3.client('s3', region_name=region, aws_access_key_id=access_key_id, aws_secret_access_key=secret_access_key)
s3_bucket = 'forenses-transcribe'

def upload_to_s3(file_name, bucket, object_name=None):
    if object_name is None:
        object_name = file_name
    try:
        s3.upload_file(file_name, bucket, object_name)
    except Exception as e:
        print(e)
        return False
    return True

def generate_unique_job_name(base_name="transcribe_job"):
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    return f"{base_name}_{timestamp}"

def transcribe_text(job_name, media_uri, media_format, language_code, transcribe_client, vocabulary_name=None):
    try:
        job_args = {
            "TranscriptionJobName": job_name,
            "Media": {"MediaFileUri": media_uri},
            "MediaFormat": media_format,
            "LanguageCode": language_code,
        }

        if vocabulary_name is not None:
            job_args["Settings"] = {"VocabularyName": vocabulary_name}

        response = transcribe_client.start_transcription_job(**job_args)
        return response["TranscriptionJob"]

    except Exception:
        print(f"Couldn't start transcription job {job_name}.")
        raise

def get_job(job_name, transcribe_client):
    try:
        response = transcribe_client.get_transcription_job(TranscriptionJobName=job_name)
        return response["TranscriptionJob"]
    except Exception:
        print(f"Couldn't get job {job_name}.")
        raise

nlp = spacy.load("en_core_web_sm")

filler_words = {
    'um', 'uh', 'like', 'you know', 'sort of', 'kind of', 'basically',
    'actually', 'literally', 'just', 'really', 'so', 'well', 'right', 'i mean'
}

def get_audio_duration_from_transcript(transcript_json):
    items = transcript_json.get("results", {}).get("items", [])
    for item in reversed(items):
        if "end_time" in item:
            return float(item["end_time"])
    return 0.0

def count_words_spacy(transcript_text):
    doc = nlp(transcript_text.lower())
    return len([t for t in doc if not t.is_punct])

def is_probable_filler(token):
    if token.text == 'just':
        return token.pos_ == 'ADV'
    elif token.text == 'like':
        return token.pos_ == 'INTJ' or (token.pos_ == 'VERB' and token.dep_ == 'discourse')
    elif token.text == 'so':
        return token.pos_ == 'ADV' and token.dep_ == 'discourse'
    elif token.text == 'well':
        return token.pos_ == 'INTJ'
    elif token.text == 'right':
        return token.pos_ in {'INTJ', 'ADV'}
    elif token.text == 'really':
        return token.pos_ == 'ADV'
    elif token.text == 'actually':
        return token.pos_ == 'ADV'
    elif token.text in {'um', 'uh'}:
        return True
    elif token.text in {'you know', 'i mean', 'sort of', 'kind of', 'basically', 'literally'}:
        return True
    return False

def analyze_filler_words(transcript_text):
    doc = nlp(transcript_text.lower())
    total_words = len([t for t in doc if not t.is_punct])
    filler_counts = Counter()
    total_filler_words = 0

    for token in doc:
        if token.text in filler_words and is_probable_filler(token):
            filler_counts[token.text] += 1
            total_filler_words += 1

    text_str = doc.text
    multi_word_fillers = [f for f in filler_words if " " in f]
    for mwf in multi_word_fillers:
        count = text_str.count(mwf)
        if count > 0:
            filler_counts[mwf] += count
            total_filler_words += count

    filler_percentages = {
        word: round((count / total_words) * 100, 2)
        for word, count in filler_counts.items()
    }

    return {
        'total_words': total_words,
        'filler_word_counts': filler_counts,
        'filler_word_percentages': filler_percentages,
        'total_filler_words': total_filler_words
    }

def print_analysis(analysis_results):
    print("\n=== Filler Word Analysis ===")
    print(f"Total words in transcript: {analysis_results['total_words']}")
    print(f"Total filler words found: {analysis_results['total_filler_words']}")
    print("\nFiller Word Breakdown:")
    print("-" * 40)
    print(f"{'Filler Word':<15} {'Count':<10} {'Percentage':<10}")
    print("-" * 40)

    for filler, count in analysis_results['filler_word_counts'].items():
        if count > 0:
            percentage = analysis_results['filler_word_percentages'][filler]
            print(f"{filler:<15} {count:<10} {percentage:>5.2f}%")

    print("-" * 40)
    total_percentage = (analysis_results['total_filler_words'] / analysis_results['total_words']) * 100
    print(f"Overall filler word percentage: {total_percentage:.2f}%")

def main():
    local_file = st.session_state.get("uploaded_audio_path", "tmp/default.wav")
    s3_key = os.path.basename(local_file)

    if not upload_to_s3(local_file, s3_bucket, s3_key):
        print("Failed to upload file to S3.")
        return

    job_name = generate_unique_job_name()
    media_uri = f"s3://{s3_bucket}/{s3_key}"

    try:
        transcribe_text(job_name, media_uri, "m4a", "en-US", transcribe_client)

        while True:
            job_info = get_job(job_name, transcribe_client)
            status = job_info["TranscriptionJobStatus"]
            if status in ["COMPLETED", "FAILED"]:
                break
            time.sleep(5)

        if status == "COMPLETED":
            transcript_uri = job_info["Transcript"]["TranscriptFileUri"]
            transcript_json = requests.get(transcript_uri).json()
            transcript_text = transcript_json["results"]["transcripts"][0]["transcript"]
            transcript_words = count_words_spacy(transcript_text)
            transcript_time = round(get_audio_duration_from_transcript(transcript_json), 2)
            transcript_wpm = round(transcript_words / (transcript_time / 60))

            print("\nTranscription result:")
            print(transcript_text)

            print("\nNumber of Words: ")
            print(transcript_words)

            print("\nTime: ")
            print(f"{transcript_time} seconds")

            print("\nWPM: ")
            print(transcript_wpm)

            analysis_results = analyze_filler_words(transcript_text)
            print_analysis(analysis_results)
        else:
            print(f"Transcription job failed: {job_info}")
    except Exception as e:
        print(f"Error in main execution: {e}")

if __name__ == "__main__":
    main()
