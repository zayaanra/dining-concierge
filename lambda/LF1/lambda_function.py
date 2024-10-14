import boto3
import os

from dotenv import load_dotenv
load_dotenv()

SQS_QUEUE_URL = os.getenv("SQS_QUEUE_URL")

sqs_client = boto3.client('sqs')


def prepareResponse(event, msgText):
    return {
        "sessionState": {
            "dialogAction": {
                "type": "Close"
            },
            "intent": {
                "name": event["sessionState"]["intent"]["name"],
                "state": "Fulfilled"
            }
        },
        "messages": [
            {
                "contentType": "PlainText",
                "content": msgText,
            }
        ]
    }

def greetUser(event):
    return prepareResponse(event, "Hi, how can I help you?")

def yourWelcome(event):
    return prepareResponse(event, "You\'re welcome")

def handleDiningSuggestions(event):
    slots = event["sessionState"]["intent"]["slots"]

    sqs_client.send_message(
        QueueUrl=SQS_QUEUE_URL,
        DelaySeconds=5,
        MessageAttributes={
            "Cuisine": {"DataType": "String", "StringValue": slots["Cuisine"]["value"]["interpretedValue"]},
            "Email": {"DataType": "String", "StringValue": slots["Email"]["value"]["interpretedValue"]},
            "DiningTime": {"DataType": "String", "StringValue": slots["DiningTime"]["value"]["interpretedValue"]},
            "NumOfPeople": {"DataType": "String", "StringValue": slots["NumOfPeople"]["value"]["interpretedValue"]},
            "Location": {"DataType": "String", "StringValue": slots["Location"]["value"]["interpretedValue"]}
        },
        MessageBody="Sent received slots to SQS Q1"
    )
    
    return prepareResponse(event, "You're all set. Expect my suggestions shortly! Have a good day.")

def lambda_handler(event, context):
    intentName = event["sessionState"]["intent"]["name"]

    if intentName == "GreetingIntent":
        return greetUser(event)
    elif intentName == "ThankYouIntent":
        return yourWelcome(event)
    elif intentName == "DiningSuggestionsIntent":
        return handleDiningSuggestions(event)
    else:
        return prepareResponse(event, "I'm sorry. Something went wrong. Please try again.")
