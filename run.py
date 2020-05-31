# Created by Chang Chia-huan
import argparse, pathlib, json, csv, io, urllib.request, urllib.parse, math, statistics, datetime

parser = argparse.ArgumentParser(description = "This script generates svg maps for the COVID-19 outbreak for select places")
parser.add_argument("-p", "--place", help = "Name of place to generate; by default, maps for select places are generated")
parser.add_argument("-u", "--url", help = "Print url")
args = vars(parser.parse_args())

with open((pathlib.Path() / "meta").with_suffix(".json"), newline = "", encoding = "utf-8") as file:
    meta = json.loads(file.read())

if args["place"]:
    if args["place"] == "UK":
        places = ["UK-1", "UK-2"]
    else:
        places = [args["place"]]
else:
    places = meta["places"]

with open((pathlib.Path() / "population").with_suffix(".json"), newline = "", encoding = "utf-8-sig") as file:
    population = json.loads(file.read())

main_uk = {}
for place in places:
    print(place)
    main = {}
    if place == "UK-1":
        place = "UK"
    if place == "UK-2":
        main = main_uk
        place = "UK"
    else:
        for area in population[place]:
            main[area] = {
                "population": population[place][area],
                "cases": 0
            }
        if place == "UK":
            place = "UK-1"
    unused = 0
    if place == "Taiwan":
        with urllib.request.urlopen("https://od.cdc.gov.tw/eic/Age_County_Gender_19Cov.json") as response:
            cases = json.loads(response.read())
        for row in cases:
            main[row["縣市"]]["cases"] += int(row["確定病例數"])
        date = datetime.date.today()

    elif place in ["UK-1", "England", "London"]:
        if "uk_data" not in globals():
            with urllib.request.urlopen("https://c19downloads.azureedge.net/downloads/data/data_latest.json") as response:
                global uk_data
                uk_data = json.loads(response.read())
        for area in uk_data["ltlas"]:
            if area in main:
                main[area]["cases"] = uk_data["ltlas"][area]["totalCases"]["value"]
            else:
                unused += 1
                if args["place"] or unused < 9:
                    print("  Area '{}' in query not found in list; cases:".format(area), uk_data["ltlas"][area]["totalCases"]["value"])
        date = datetime.datetime.fromisoformat(uk_data["lastUpdatedAt"].rstrip("Z"))
        if place == "UK-1":
            main_uk = main
            continue

    elif place == "Czechia":
        with urllib.request.urlopen("https://api.apify.com/v2/key-value-stores/K373S4uCFR9W1K8ei/records/LATEST?disableRedirect=true") as response:
            data = json.loads(response.read())
        for row in data["infectedByRegion"]:
            if row["name"] in main:
                main[row["name"]]["cases"] = row["value"]
            else:
                unused += 1
                if args["place"] or unused < 9:
                    print("  Area '{}' in query not found in list".format(row["name"]))
        date = datetime.datetime.fromisoformat(data["lastUpdatedAtSource"].rstrip("Z"))

    elif place == "Japan":
        with urllib.request.urlopen("https://www.stopcovid19.jp/data/covid19japan.json") as response:
            data = json.loads(response.read())
        for row in data["area"]:
            main[row["name"]]["cases"] = int(row["npatients"])
        if data["lastUpdate"] != "--":
            date = datetime.datetime.fromisoformat(data["lastUpdate"])
        else:
            date = datetime.date.today()
            print("  No date available for Japan; current date used")

    else:
        if place in meta["query_list"]:
            queries = meta["query_list"][place]
        else:
            queries = [place]
        try:
            for query in queries:
                url = "https://services{}.arcgis.com/{}/arcgis/rest/services/{}/FeatureServer/{}/".format(
                    meta["query"][query][0][0],
                    meta["query"][query][0][1],
                    urllib.parse.quote(meta["query"][query][0][2]),
                    meta["query"][query][0][3],
                )
                url1 = url + "?f=pjson"
                with urllib.request.urlopen(url1) as response:
                    date = json.loads(response.read())["editingInfo"]["lastEditDate"] / 1000
                    date = datetime.datetime.fromtimestamp(date, tz = datetime.timezone.utc)
                if place == "France":
                    where = "Jour%3D%27{}%2F{}%2F20{}%27".format(date.strftime("%d"), date.strftime("%m"), date.strftime("%y"))
                else:
                    where = urllib.parse.quote(meta["query"][query][1][1]) + "%3E-1"
                url2 = url + "query?where={}&outFields={},{},{}&returnGeometry=false&returnExceededLimitFeatures=true&f=pjson".format(
                    where,
                    meta["query"][query][1][0],
                    urllib.parse.quote(meta["query"][query][1][1]),
                    meta["query"][query][1][2]
                )
                if args["url"]:
                    print("  " + url2)
                with urllib.request.urlopen(url2) as response:
                    if place == "US":
                        start = 255
                    else:
                        start = 0
                    for item in json.loads(response.read())["features"][start:]:
                        id = str(item["attributes"][meta["query"][query][1][0]]).lstrip("0")
                        if id in main:
                            main[id]["cases"] = float(item["attributes"][meta["query"][query][1][1]])
                            if meta["query"][query][1][2] != "":
                                main[id]["population"] = int(item["attributes"][meta["query"][query][1][2]])
                        elif id not in [None, "None", "NA"] and item["attributes"][meta["query"][query][1][1]]:
                            unused += 1
                            if args["place"] or unused < 9:
                                print("  Area '{}' in query not found in list; cases:".format(id), item["attributes"][meta["query"][query][1][1]])
        except:
            print("  Error fetching data for", place)
            continue

    if place in meta["10000"]:
        unit = 10000
    else:
        unit = 1000000

    cases, pop = 0, 0
    values = []
    for area in main:
        no_cases = 0
        if main[area]["population"] > 0:
            if not main[area]["cases"] > 0:
                no_cases += 1
                if args["place"] or no_cases < 9:
                    print("  Area '{}' in list has 0 cases".format(area))
            main[area]["pcapita"] = main[area]["cases"] / main[area]["population"] * unit
            cases += main[area]["cases"]
            pop += main[area]["population"]
            values.append(main[area]["pcapita"])
        else:
            print("  Population for '{}' in list is 0".format(area))

    q = statistics.quantiles(values, n = 100, method = "inclusive")
    step = math.sqrt(cases / pop * unit - q[0]) / 3

    threshold = [0, 0, 0, 0, 0]
    for i in range(1, 5):
        threshold[i] = math.pow(i * step, 2) + q[0]

    with open((pathlib.Path() / "template" / place).with_suffix(".svg"), "r", newline = "", encoding = "utf-8") as file_in:
        with open((pathlib.Path() / "results" / place).with_suffix(".svg"), "w", newline = "", encoding = "utf-8") as file_out:
            if threshold[4] >= 10000:
                num = "{:_.0f}"
            elif threshold[1] >= 10:
                num = "{:.0f}"
            else:
                num = "{:.2f}"

            for row in file_in:
                written = False
                for area in main:
                    if row.find('id="{}"'.format(area)) > -1:
                        i = 0
                        while i < 4:
                            if main[area]["pcapita"] >= threshold[i + 1]:
                                i += 1
                            else:
                                break
                        if place == "France":
                            file_out.write(row.replace('id="{}"'.format(area), 'fill="{}"'.format(meta["colour"]["deaths"][i])))
                        else:
                            file_out.write(row.replace('id="{}"'.format(area), 'fill="{}"'.format(meta["colour"]["cases"][i])))
                        written = True
                        break
                if written == False:
                    if row.find('>Date') > -1:
                        file_out.write(row.replace('Date', date.strftime("%F")))
                    elif row.find('>level') > -1:
                        for i in range(5):
                            if row.find('level{}'.format(i)) > -1:
                                if i == 0:
                                    file_out.write(row.replace('level{}'.format(i), "&lt; " + num.format(threshold[1]).replace("_", "&#8201;")))
                                else:
                                    file_out.write(row.replace('level{}'.format(i), "≥ " + num.format(threshold[i]).replace("_", "&#8201;")))
                    else:
                        file_out.write(row)

    print("  {:.0f} cases total in {} areas; {} figures unused".format(cases, len(values), unused))
