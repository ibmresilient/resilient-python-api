import json
import csv

"""Prepare the CSV file used by the parks service, and the field definition with park options"""

with open("national_parks.geojson") as fh:
    parks = json.load(fh)

with open("bear_parks.geojson") as bh:
    bears = json.load(bh)

data = {}
for feature in parks["features"]:
    code = feature["properties"]["Code"]
    name = feature["properties"]["Name"]
    (lat, lon) = feature["geometry"]["coordinates"]
    data[code] = {"parkName": name.replace(",", "."),
                  "parkCode": code,
                  "geoLat": lat,
                  "geoLong": lon,
                  "url": None,
                  "hasBlackBear": None,
                  "hasGrizzlyBear": None,
                  "hasPolarBear": None}

for feature in bears["features"]:
    code = feature["properties"]["UnitCode"]
    url = feature["properties"]["UnitWebsite"]
    d = {"url": feature["properties"]["UnitWebsite"],
         "hasBlackBear": feature["properties"]["Black"],
         "hasGrizzlyBear": feature["properties"]["BrownGrizzly"],
         "hasPolarBear": feature["properties"]["Polar"]}
    data[code].update(d)

# print(json.dumps(data, indent=2))

with open("../service/parks.csv", 'wb') as temp:
    writer = None
    for park in data.values():
        if not writer:
            writer = csv.DictWriter(temp, fieldnames=sorted(park.keys()), dialect='excel')
            writer.writeheader()
        writer.writerow(park)

fielddef = {
    "name": "park",
    "text": "Park",
    "tooltip": "",
    "prefix": "properties",
    "blank_option": True,
    "input_type": "select",
    "placeholder": ""
    }
fieldvalues = []
for park in sorted(data.keys()):
    fieldvalues.append({
        "default": False,
        "enabled": True,
        "properties": None,
        "label": park
        })
fielddef["values"] = fieldvalues

with open("../action/fielddef_park.json", 'wb') as temp:
    temp.write(json.dumps(fielddef, indent=4))
