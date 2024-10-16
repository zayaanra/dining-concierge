import boto3
import json
import requests
import os

from requests_aws4auth import AWS4Auth
from dotenv import load_dotenv

load_dotenv()

OASS_DOMAIN = os.getenv("OASS_DOMAIN")
SQS_QUEUE_URL = os.getenv("SQS_QUEUE_URL")
SES_SENDER_EMAIL = os.getenv("SES_SENDER_EMAIL")

region = 'us-east-1'
service = 'es'
credentials = boto3.Session().get_credentials()
awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, region, service, session_token=credentials.token)

host = OASS_DOMAIN
index = 'restaurants'
url = host + '/' + index + '/_search'

sqs_client = boto3.client('sqs')
dynamodb_client = boto3.client('dynamodb')
ses_client = boto3.client('ses')

# Polls the SQS Q1 for 1 message. It returns the receipt handle for message deletion and message body
def receive_from_sqs():
    try:
        response = sqs_client.receive_message(
            QueueUrl=SQS_QUEUE_URL,
            AttributeNames=["All"],
            MessageAttributeNames=["All"],
            MaxNumberOfMessages=1,
            WaitTimeSeconds=10
        )

        messages = response['Messages']
        body = json.loads(messages[0]['Body'])
        receiptHandle = messages[0]['ReceiptHandle']

        slots = {
            "cuisine": body["Cuisine"],
            "diningTime": body["DiningTime"],
            "location": body["Location"],
            "numOfPeople": body["NumOfPeople"],
            "email": body["Email"]
        }
        return slots, receiptHandle
    except Exception as e:
        print(f"Something went wrong: {e}")
        return None

# Searches the OpenSearch index for 3 random restaurant IDs given the cuisine
def search_index(cuisine):
    try:
        query = {
            "size": 3,
            "query": {
                "function_score": {
                    "query": {
                        "multi_match": {
                            "query": cuisine,
                            "fields": ["Cuisine"]
                        }
                    },
                    "random_score": {}
                }
            }
        }

        headers = { "Content-Type": "application/json" }
        r = requests.get(url, auth=awsauth, headers=headers, data=json.dumps(query))

        data = json.loads(r.text)
        restaurants = [
            {
                "RestaurantID": hit["_source"]["RestaurantID"],
            }
            for hit in data["hits"]["hits"]
        ]

        return restaurants
    except Exception as e:
        print(f"Something went wrong: {e}")
        return None

# Searches DynamoDB for the actual restaurant data through the restaurant IDs provided by the OpenSearch query earlier
def search_dynamodb(restaurants):
    try:
        keys = []
        for r in restaurants:
            restaurantID = r['RestaurantID']
            keys.append(
                {"restaurant_id": {"S": restaurantID}}
            )
        
        response = dynamodb_client.batch_get_item(
            RequestItems={
                "yelp-restaurants": {
                    'Keys': keys,
                    'AttributesToGet': ["name", "address"]
                }
            }
        )

        yelp_restaurants = response["Responses"]["yelp-restaurants"]
        return yelp_restaurants
    except Exception as e:
        print(f"Something went wrong: {e}")

# Sends the email with the given restaurant data to the given email
def send_email(cuisine, numOfPeople, diningTime, email, yelp_restaurants):
    try:
        msg = f"Hello! Here are my {cuisine} restaurant suggestions for {numOfPeople} people, for today at {diningTime}\n\n"
        n = 1
        for r in yelp_restaurants:
            name, address = r['name']['S'], r['address']['S']
            msg += f"{n}. {name}, located at {address}\n"
            n += 1
        
        msg += "\n\n"
        msg += "Enjoy your meal!"
        
        response = ses_client.send_email(
            Source=SES_SENDER_EMAIL,
            Destination={
                'ToAddresses': [email],
            },
            Message={
                'Subject': {
                    'Data': "Restaurant Suggestions",
                },
                'Body': {
                    'Text': {
                        'Data': msg,
                    }
                }
            }
        )

        print("Sent email response: ", response)
        return response
    except Exception as e:
        print(f"Something went wrong: {e}")
        return None

# Lambda execution starts here
def lambda_handler(event, context):
    invalidResponse = {
        "statusCode": 500,
        "body": json.dumps("Something went wrong")
    }
    
    # If we were not able to read from the queue, return 500
    slots, receiptHandle = receive_from_sqs()
    if not slots:
        return invalidResponse
    
    # If the OpenSearch index query failed, return 500
    restaurants = search_index(slots["cuisine"])
    if not restaurants:
        return invalidResponse
    
    # If the DynamoDB search failed, return 500
    yelp_restaurants = search_dynamodb(restaurants)
    if not yelp_restaurants:
        return invalidResponse
    
    # If the email could not be sent, return 500
    email_response = send_email(slots["cuisine"], slots["numOfPeople"], slots["diningTime"], slots['email'], yelp_restaurants)
    if not email_response:
        return invalidResponse
    
    # If everything was a success, then we can safely delete the message from the SQS Q
    response = sqs_client.delete_message(
        QueueUrl=SQS_QUEUE_URL,
        ReceiptHandle=receiptHandle
    )
    print(f"SQS Message Deleted:{response}\n")
    return response
