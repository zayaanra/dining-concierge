# Filter out unnecessary fields from cuisine data

import json

def check_duplicates():
    restaurants = set()

    cuisines = [
        "Mexican",
        "Indian",
        "American"
    ]

    #print("test")

    for cuisine in cuisines:
        with open(f"data/{cuisine}_filtered.json", "r") as f:
            for business in json.load(f)["businesses"]:
                if business["name"] in restaurants:
                    print(business["name"])
                else:
                    restaurants.add(business["name"])

def main():
    cuisines = [
        "Mexican",
        "Indian",
        "American"
    ]

    for cuisine in cuisines:
        with open(f"data/{cuisine}.json", "r") as f1, open(f"data/{cuisine}_filtered.json", "w") as f2:
            data = json.load(f1)

            filtered_data = {"businesses": []}
            for business in data["businesses"]:
                filtered_data["businesses"].append({
                    "id": business["id"],
                    "name": business["name"],
                    "address": business["location"]["display_address"],
                    "coordinates": business["coordinates"],
                    "review_count": business["review_count"],
                    "rating": business["rating"],
                    "zip_code": business["location"]["zip_code"],
                })

            json.dump(filtered_data, f2, indent=4)

if __name__ == "__main__":
    check_duplicates()