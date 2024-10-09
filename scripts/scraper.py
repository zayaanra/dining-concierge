import requests
import os

from dotenv import load_dotenv

load_dotenv()

YELP_API_KEY = os.getenv("YELP_API_KEY")

def main():
    cuisines = [
        "Mexican",
        "Indian",
        "American"
    ]

    for cuisine in cuisines:
        url = "https://api.yelp.com/v3/businesses/search"

        headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {YELP_API_KEY}"
        }

        params = {
            'limit': 50,
            'location': 'Manhattan',
            'term': f'{cuisine}_restaurants',
            'sort_by': 'best_match',
        }
        response = requests.get(url, headers=headers, params=params)
        with open(f"data/{cuisine}.json", "w") as f:
            f.write(response.text)

if __name__ == "__main__":
    main()