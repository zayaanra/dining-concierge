import boto3
import os
import uuid
import json

from datetime import datetime
from dotenv import load_dotenv
load_dotenv()

BOT_ALIAS_ID = os.getenv("BOT_ALIAS_ID")
BOT_ID = os.getenv("BOT_ID")

lexClient = boto3.client('lexv2-runtime')

def lambda_handler(event, context):
    try:
        sessionID = str(uuid.uuid4())

        msg = str(event['messages'][0]['unstructured']['text'])
        
        lexResponse = lexClient.recognize_text(
            botId=BOT_ID,
            botAliasId=BOT_ALIAS_ID,
            localeId="en_US",
            sessionId=sessionID,
            text=msg,
        )
        print("Lex Response: ", lexResponse)

        messages = [
            {
                "type": "unstructured",
                "unstructured": {
                    "id": sessionID,
                    "text": message['content'],
                    "timestamp": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                }
            }
            for message in lexResponse['messages']
        ]
        return {
            "statusCode": 200,
            "headers": {
                "Access-Control-Allow-Headers": "Content-Type",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "OPTIONS,POST,GET"
            },
            "messages": messages
        }
    except Exception as e:
        print("Error communicating with Lex chatbot:", e)
        return {
            "statusCode": 500,
            "body": json.dumps("Unexpected error")
        }
