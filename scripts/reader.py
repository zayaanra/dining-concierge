# Reads data collected from YELP API (debugging purposes)

import json

with open("data/American.json", "r") as f:
    data = json.load(f)
    print(data["businesses"][0])