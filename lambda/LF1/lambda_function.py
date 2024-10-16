import boto3
import os
import re
import json

from dotenv import load_dotenv
load_dotenv()

SQS_QUEUE_URL = os.getenv("SQS_QUEUE_URL")

sqs_client = boto3.client('sqs')

# Sends message containing dining suggestions slots to SQS Q1
def send_to_sqs(event):
    slots = event["sessionState"]["intent"]["slots"]

    body = json.dumps({
        "Cuisine": slots["Cuisine"]["value"]["interpretedValue"],
        "Email": slots["Email"]["value"]["interpretedValue"],
        "DiningTime": slots["DiningTime"]["value"]["interpretedValue"],
        "NumOfPeople": slots["NumOfPeople"]["value"]["interpretedValue"],
        "Location": slots["Location"]["value"]["interpretedValue"]
    })

    sqs_client.send_message(
        QueueUrl=SQS_QUEUE_URL,
        DelaySeconds=5,
        MessageBody=body
    )

# Validates each slot provided by the user
# If a slot is invalid, the chatbot will re-elicit the slot value
def validate_slots(slots):
    if slots["Cuisine"]:
        cuisines = ["Indian", "Mexican", "American"]
        if "interpretedValue" not in slots["Cuisine"]["value"] or slots["Cuisine"]["value"]["interpretedValue"] not in cuisines:
            return False, "Cuisine is invalid. Only Indian/Mexican/American cuisine is supported. Please try again.", "Cuisine"
    
    if slots["Email"]:
        if "interpretedValue" not in slots["Email"]["value"] or not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+.[a-zA-Z]{2,}$', slots["Email"]["value"]["interpretedValue"]):
            return False, "Email is invalid. Please try again. (e.g: test@gmail.com)", "Email"
    
    if slots["DiningTime"]:        
        try:
            _ = slots["DiningTime"]["value"]["interpretedValue"]
        except KeyError:
            return False, "Dining time is invalid. Please try again. (e.g: 2PM)", "DiningTime"
    
    if slots["NumOfPeople"]:
        if "interpretedValue" not in slots["NumOfPeople"]["value"] or int(slots["NumOfPeople"]["value"]["interpretedValue"]) < 1:
            return False, "Num. of people is invalid. Please try again.", "NumOfPeople"
    
    if slots["Location"]:
        if "interpretedValue" not in slots["Location"]["value"] or slots["Location"]["value"]["interpretedValue"] != "Manhattan":
            return False, "City is invalid. Only Manhattan is supported. Please try again.", "Location"

    return True, "", ""

# Prepares a generic response for when an intent has been fulfilled
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

# Checks to see if any slots are invalid and if it is, it will prepare a response to re-elicit the invalid slot
def handleDiningSuggestions(event):
    if event['invocationSource'] == 'DialogCodeHook':
        slots = event['sessionState']['intent']['slots']
        
        valid, msg, slot = validate_slots(slots)
        if not valid:
            return {

                'sessionState': {
                    'dialogAction': {
                        'type': 'ElicitSlot',
                        'slotToElicit': slot
                    },
                    'intent': {
                        'name': event["sessionState"]["intent"]["name"],
                        'slots': slots,
                        'state': 'Failed'
                    }
                },
                'messages': [
                    {
                        "contentType": "PlainText",
                        "content": msg,
                    }
                ],
            }
    
    return ""

def lambda_handler(event, context):
    # Handle the intent accordingly
    intentName = event["sessionState"]["intent"]["name"]
    if intentName == "GreetingIntent":
        return prepareResponse(event, "Hi, how can I help you?")
    elif intentName == "ThankYouIntent":
        return prepareResponse(event, "You're welcome.")
    elif intentName == "DiningSuggestionsIntent":
        # If there is no proposedNextState, then it means the intent has been fulfilled
        if "proposedNextState" not in event:
            send_to_sqs(event)
            return prepareResponse(event, "You're all set. Expect my suggestions shortly! Have a good day.")
        else:
            # The intent has not yet been fulfilled, so we will check if the current slot is valid and re-elicit if necessary
            response = {
                "statusCode": 200,
                "sessionState": event['sessionState'],
            }
            response["sessionState"]["dialogAction"] = event["proposedNextState"]["dialogAction"]

            slotResponse = handleDiningSuggestions(event)
            if slotResponse:
                return slotResponse
            
            return response
    else:
        # Fallback intent
        return prepareResponse(event, "I'm sorry. I didn't recognize that. Please try again.")
