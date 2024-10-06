import requests
import os

from dotenv import load_dotenv

load_dotenv()

YELP_API_KEY = os.getenv("YELP_API_KEY")

cuisines = [
    "Italian",
    "Chinese",
    "Mexican",
    "Indian",
    "Japanese",
    "Greek",
    "Thai",
    "French",
    "Korean",
    "Mediterranean",
    "Vietnamese",
    "Turkish",
    "Brazilian",
    "Ethiopian",
    "Moroccan",
    "Lebanese",
    "Caribbean",
    "German",
    "Russian",
    "American"
]

# for cuisine in cuisines:
#     url = f"https://api.yelp.com/v3/businesses/search"

#     headers = {
#         "accept": "application/json",
#         "Authorization": f"Bearer {YELP_API_KEY}"
#     }

#     for offset in range(0, 1000, 50):
#         params = {
#             'limit': 50,
#             'offset': offset,
#             'location': 'Manhattan',
#             'term': f'{cuisine}_restaurants',
#             'sort_by': 'best_match',
#         }
#         response = requests.get(url, headers=headers, params=params)
#         with open(f"data/{cuisine}.json", "w") as f:
#             f.write(response.text)

def fetch_unique_restaurants(cuisine, target_count=1000):
    unique_restaurants = {}
    offset = 0

    while len(unique_restaurants) < target_count:
        headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {YELP_API_KEY}"
        }
        params = {
            'term': f'{cuisine} restaurants',
            'location': 'Manhattan',
            'limit': 50,
            'offset': offset
        }

        response = requests.get("https://api.yelp.com/v3/businesses/search", headers=headers, params=params)
        
        if response.status_code != 200:
            print(f"Error: {response.status_code} - {response.text}")
            break
            
        data = response.json()
        
        # Collect unique restaurants
        for business in data.get("businesses", []):
            if business["id"] not in unique_restaurants:
                unique_restaurants[business["id"]] = business  # Store business entry

        offset += 50

        if len(data.get("businesses", [])) < 50:
            break  # No more results available
        
        # time.sleep(1)  # Respect rate limits

    return list(unique_restaurants.values())

# Main execution
all_restaurants = {}
for cuisine in cuisines:
    restaurants = fetch_unique_restaurants(cuisine)
    all_restaurants[cuisine] = restaurants
    print(f"Fetched {len(restaurants)} unique {cuisine} restaurants.")