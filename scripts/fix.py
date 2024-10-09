# Fixes how some fields are formatted in the data

import json


def main():
    cuisines = [
        "Mexican",
        "Indian",
        "American"
    ]

    for cuisine in cuisines:
        with open(f"data/{cuisine}_filtered.json", "r") as f:
            data = json.load(f)

        with open(f"data/{cuisine}_filtered.json", "w") as f:
            for business in data["businesses"]:
                business["address"] = business["address"][0] + ", " + business["address"][1]


            json.dump(data, f, indent=4)

if __name__ == "__main__":
    main()