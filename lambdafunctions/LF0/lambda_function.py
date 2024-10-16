import boto3
import os
import json

from datetime import datetime
from dotenv import load_dotenv
load_dotenv()

BOT_ALIAS_ID = os.getenv("BOT_ALIAS_ID")
BOT_ID = os.getenv("BOT_ID")

lexClient = boto3.client('lexv2-runtime')

def lambda_handler(event, context):
    try:
        msg = str(event['messages'][0]['unstructured']['text'])
        
        # Send a message to the Lex chatbot
        # It should receive a valid response which is sent to the frontend to display
        lexResponse = lexClient.recognize_text(
            botId=BOT_ID,
            botAliasId=BOT_ALIAS_ID,
            localeId="en_US",
            sessionId="session",
            text=msg,
        )
        lexResponseMessages = lexResponse.get('messages', [])
        
        # Prepare the list of messages to return to the frontend
        # The number of messages should always be <= 1
        messages = [
            {
                "type": "unstructured",
                "unstructured": {
                    "id": "id",
                    "text": message['content'],
                    "timestamp": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                }
            }
            for message in lexResponseMessages
        ]
        return {
            "statusCode": 200,
            "messages": messages
        }
    except Exception as e:
        print("Error communicating with Lex chatbot:", e)
        return {
            "statusCode": 500,
            "body": json.dumps("Unexpected error")
        }
