import os
import boto3
from dotenv import load_dotenv
import requests
import json

load_dotenv()
access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")
region = os.getenv("AWS_REGION")

transcribe_client = boto3.client('transcribe', region_name=region, aws_access_key_id=access_key_id, aws_secret_access_key=secret_access_key)
s3 = boto3.client('s3', region_name=region, aws_access_key_id=access_key_id, aws_secret_access_key=secret_access_key)
s3_bucket = 'forenses-transcribe'
s3_uri = 's3://forenses-transcribe/New Recording 38.m4a'



def upload_to_s3(file_name, bucket, object_name=None):
    if object_name is None:
        object_name = file_name
    try:
        response = s3.upload_file(file_name, bucket, object_name)
    except Exception as e:
        print(e)
        return False
    return True 

def lambda_handler():
    pass


def transcribe_text(
    job_name,
    media_uri,
    media_format,
    language_code,
    transcribe_client,
    vocabulary_name=None,
    ):
    

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
        job = response["TranscriptionJob"]
        print("Started transcription job %s.", job_name)
    except Exception:
        print("Couldn't start transcription job %s.", job_name)
        raise
    else:
        return job
    
def get_job(job_name, transcribe_client):
    try:
        response = transcribe_client.get_transcription_job(
            TranscriptionJobName=job_name
        )
        job = response["TranscriptionJob"]
        print("Got job %s.", job["TranscriptionJobName"])
    except Exception:
        print("Couldn't get job %s.", job_name)
        raise
    else:
        return job
    

#job1 = transcribe_text("test2", s3_uri, "mp4", "en-US", transcribe_client)
#print(job1)

transcript_uri = get_job("test2", transcribe_client)["Transcript"]["TranscriptFileUri"]
transcript_json = requests.get(transcript_uri).json()
transcript_text = transcript_json["results"]["transcripts"][0]["transcript"]

print(transcript_text)