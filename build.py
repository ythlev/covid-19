# Created by Chang Chia-huan
import argparse, pathlib, json, csv, io, urllib.request, urllib.parse, math, statistics, datetime

parser = argparse.ArgumentParser(description = "This script generates svg maps for the COVID-19 outbreak for select places")
parser.add_argument("-p", "--place", help = "Name of place to generate; by default, maps for select places are generated")
args = vars(parser.parse_args())

with open((pathlib.Path() / "meta").with_suffix(".json"), newline = "", encoding = "utf-8") as file:
    meta = json.loads(file.read())

if args["place"] != None:
    places = [args["place"]]
else:
    places = meta["places"]

with open((pathlib.Path() / "population").with_suffix(".json"), newline = "", encoding = "utf-8-sig") as file:
    population = json.loads(file.read())

for place in places:
    main = {}
    for area in population[place]:
        main[area] = {
            "population": population[place][area],
            "cases": 0
        }
    unused = 0
    if place == "Taiwan":
        date = datetime.date.today()
        with urllib.request.urlopen("https://od.cdc.gov.tw/eic/Weekly_Age_County_Gender_19CoV.json") as response:
            cases = json.loads(response.read())
        for row in cases:
            main[row["縣市"]]["cases"] += int(row["確定病例數"])
        with urllib.request.urlopen("https://data.cdc.gov.tw/api/3/action/package_show?id=aagstable-weekly-19cov") as response:
            metadata = json.loads(response.read())["result"]
            date = datetime.datetime.fromisoformat(metadata["metadata_modified"])
    elif place == "Czechia":
        with urllib.request.urlopen("https://onemocneni-aktualne.mzcr.cz/api/v1/covid-19/osoby.min.json") as response:
            cases = json.loads(response.read())
        for row in cases:
            main[row["KHS"].lstrip("CZ0")]["cases"] += 1
        with urllib.request.urlopen(
            "https://opendata.mzcr.cz/api/3/action/package_show" +
            "?id=covid-19-prehled-osob-s-prokazanou-nakazou-dle-hlaseni-krajskych-hygienickych-stanic"
        ) as response:
            metadata = json.loads(response.read())["result"]
            date = datetime.datetime.fromisoformat(metadata["metadata_modified"])
    elif place == "Japan":
        with urllib.request.urlopen("https://www.stopcovid19.jp/data/covid19japan.json") as response:
            data = json.loads(response.read())
        for row in data["area"]:
            main[row["name"]]["cases"] = int(row["npatients"])
        date = datetime.datetime.fromisoformat(data["lastUpdate"])
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
                url2 = url + "query?where={}%3E0&outFields={},{}&returnGeometry=false&returnExceededLimitFeatures=true&f=pjson".format(
                    meta["query"][query][0][4],
                    urllib.parse.quote(meta["query"][query][1][0]),
                    urllib.parse.quote(meta["query"][query][1][1])
                )
                with urllib.request.urlopen(url2) as response:
                    if place == "US":
                        start = 236
                    else:
                        start = 0
                    for entry in json.loads(response.read())["features"][start:]:
                        key = str(entry["attributes"][meta["query"][query][1][0]]).lstrip("0")
                        if key in main:
                            if place == "Japan":
                                main[key]["cases"] += 1
                            else:
                                main[key]["cases"] = int(entry["attributes"][meta["query"][query][1][1]])
                        elif key not in [None, "None", "NA"]:
                            if meta["query"][query][1][1] not in entry["attributes"]:
                                if args["place"] != None or unused < 9:
                                    print(key)
                                unused += 1
                            elif entry["attributes"][meta["query"][query][1][1]] != None:
                                if args["place"] != None or unused < 9:
                                    print(key, entry["attributes"][meta["query"][query][1][1]])
                                unused += 1
        except:
            print("Error fetching data for", place)
            continue

    if place in meta["10000"]:
        unit = 10000
    else:
        unit = 1000000

    values = []
    for area in main:
        main[area]["pcapita"] = main[area]["cases"] / main[area]["population"] * unit
        values.append(main[area]["pcapita"])

    q = statistics.quantiles(values, n = 100, method = "inclusive")
    step = math.sqrt(statistics.mean(values) - q[0]) / 3

    threshold = [0, 0, 0, 0, 0, 0]
    for i in range(1, 6):
        threshold[i] = math.pow(i * step, 2) + q[0]

    with open((pathlib.Path() / "template" / place).with_suffix(".svg"), "r", newline = "", encoding = "utf-8") as file_in:
        with open((pathlib.Path() / "results" / place).with_suffix(".svg"), "w", newline = "", encoding = "utf-8") as file_out:
            if threshold[1] > 10:
                num = "{:.0f}"
            else:
                num = "{:.2f}"
            for row in file_in:
                written = False
                for area in main:
                    if row.find('id="{}"'.format(area)) > -1:
                        i = 0
                        while i < 5:
                            if main[area]["pcapita"] >= threshold[i + 1]:
                                i += 1
                            else:
                                break
                        file_out.write(row.replace('id="{}"'.format(area), 'style="fill:{}"'.format(meta["colour"][i])))
                        written = True
                        break
                if written == False:
                    if row.find('>Date') > -1:
                        file_out.write(row.replace('Date', date.strftime("%F")))
                    elif row.find('>level') > -1:
                        for i in range(6):
                            if row.find('level{}'.format(i)) > -1:
                                if i == 0:
                                    file_out.write(row.replace('level{}'.format(i), "&lt; " + num.format(threshold[1])))
                                else:
                                    file_out.write(row.replace('level{}'.format(i), "≥ " + num.format(threshold[i])))
                    else:
                        file_out.write(row)

    cases = []
    for area in main:
        cases.append(main[area]["cases"])
    print("{}: {} cases total in {} areas; {} figures unused".format(place, sum(cases), len(cases), unused))
