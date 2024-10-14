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

def receive_from_queue():
    response = sqs_client.receive_message(
        QueueUrl=SQS_QUEUE_URL,
        AttributeNames=["All"],
        MessageAttributeNames=["All"],
        MaxNumberOfMessages=1,
        WaitTimeSeconds=10
    )

    messages = response['Messages']
    if not messages:
        print("No messages received from SQS\n")
        return
        
    messageAttributes = messages[0]['MessageAttributes']
    receiptHandle = messages[0]['ReceiptHandle']

    slots = {
        "cuisine": messageAttributes["Cuisine"]["StringValue"],
        "diningTime": messageAttributes["DiningTime"]["StringValue"],
        "location": messageAttributes["Location"]["StringValue"],
        "numOfPeople": messageAttributes["NumOfPeople"]["StringValue"],
        "email": messageAttributes["Email"]["StringValue"]
    }

    response = sqs_client.delete_message(
        QueueUrl=SQS_QUEUE_URL,
        ReceiptHandle=receiptHandle
    )
    print(f"SQS Message Deleted:{response}\n")

    return slots

def search_index(cuisine):
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

def search_dynamodb(restaurants):
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

def send_email(cuisine, numOfPeople, diningTime, email, yelp_restaurants):
    # TODO - need production access for SES which requires a domain which is $$$

    msg = f"Hello! Here are my {cuisine} restaurant suggestions for {numOfPeople} people, for today at {diningTime}"
    n = 1
    for r in yelp_restaurants:
        name, address = r['name']['S'], r['address']['S']
        msg += f"{n}. {name}, located at {address}"
    
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


# Lambda execution starts here
def lambda_handler(event, context):
    slots = receive_from_queue()
    if not slots:
        return {
            "statucCode": 200,
            "body": json.dumps("Something went wrong")
        }
    
    restaurants = search_index(slots["cuisine"])
    yelp_restaurants = search_dynamodb(restaurants)
    response = send_email(slots["cuisine"], slots["numOfPeople"], slots["diningTime"], slots['email'], yelp_restaurants)

    return response
