import boto3
import json
import requests
import os

from requests_aws4auth import AWS4Auth
from dotenv import load_dotenv

load_dotenv()

OASS_DOMAIN = os.getenv("OASS_DOMAIN")

region = 'us-east-1'
service = 'oass'
credentials = boto3.Session().get_credentials()
awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, region, service, session_token=credentials.token)

host = OASS_DOMAIN
index = 'restaurants'
url = host + '/' + index + '/_search'

# Lambda execution starts here
def lambda_handler(event, context):
    query = {
        "size": 3,
        "query": {
            "multi_match": {
                "query": 'Mexican',
                "fields": ["cuisine"]
            }
        }
    }

    headers = { "Content-Type": "application/json" }
    r = requests.get(url, auth=awsauth, headers=headers, data=json.dumps(query))
    response = {
        "statusCode": 200,
        "headers": {
            "Access-Control-Allow-Origin": '*'
        },
        "isBase64Encoded": False
    }

    response['body'] = r.text
    print("Response: ", response)
    return response