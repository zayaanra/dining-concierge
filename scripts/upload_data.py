# Uploads data in bulk to DynamoDB instance

import boto3
import json
import os
import datetime

from decimal import Decimal
from dotenv import load_dotenv

load_dotenv()

AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_KEY")


def main():
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1', aws_access_key_id=AWS_ACCESS_KEY, aws_secret_access_key=AWS_SECRET_KEY)
    table = dynamodb.Table('yelp-restaurants')

    cuisines = [
        "Mexican",
        "Indian",
        "American"
    ]

    for cuisine in cuisines:
        with open(f"data/{cuisine}_filtered.json", "r") as f:
            data = json.load(f, parse_float=Decimal)
            
            items = []
            for business in data["businesses"]:
                item = {
                    "restaurant_id": business["id"],
                    "insertedAtTimestamp": {
                        "time": datetime.datetime.now().isoformat(),
                        "date": datetime.date.today().isoformat()
                    },
                    "name": business["name"],
                    "address": business["address"],
                    "coordinates": business["coordinates"],
                    "review_count": business["review_count"],
                    "rating": business["rating"],
                    "zip_code": business["zip_code"],
                }
                items.append(item)
    
            # Insert each item in the JSON data into the DynamoDB table
            for item in items:
                try:
                    table.put_item(Item=item)
                    print(f"Inserted item: {item}")
                except Exception as e:
                    print(f"Error inserting item: {item}, error: {e}")

if __name__ == "__main__":
    main()
