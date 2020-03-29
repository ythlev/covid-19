# Created by Chang Chia-huan
import argparse, pathlib, json, csv, io, urllib.request, math, statistics, datetime

parser = argparse.ArgumentParser(description = "This script generates svg maps for the COVID-19 outbreak for select places")
parser.add_argument("-p", "--place", help = "Name of place to generate; by default, maps for select places are generated")
args = vars(parser.parse_args())

if args["place"] != None:
    places = [args["place"]]
else:
    places = ["Australia", "Canada", "Berlin", "Italy", "Japan", "Netherlands", "UK", "London", "US", "New York CSA", "Spain", "Taiwan"]

with open((pathlib.Path() / "population").with_suffix(".json"), newline = "", encoding = "utf-8-sig") as file:
    population = json.loads(file.read())

with open((pathlib.Path() / "meta").with_suffix(".json"), newline = "", encoding = "utf-8") as file:
    meta = json.loads(file.read())

colour = ["#fee5d9","#fcbba1","#fc9272","#fb6a4a","#de2d26","#a50f15"]

for place in places:
    main = {}
    for area in population[place]:
        main[area] = {
            "population": population[place][area],
            "cases": 0
        }
    date = datetime.date.today()
    if place == "Taiwan":
        with urllib.request.urlopen("https://od.cdc.gov.tw/eic/Weekly_Age_County_Gender_19CoV.json") as response:
            cases = json.loads(response.read())
        for row in cases:
            main[row["縣市"]]["cases"] += int(row["確定病例數"])
    elif place == "Malaysia":
        with open((pathlib.Path() / "cases").with_suffix(".json"), newline = "", encoding = "utf-8") as file:
            cases = json.loads(file.read())
        for area in cases[place]:
            main[area]["cases"] = cases[place][area]
    else:
        if place == "UK":
            queries = ["UK-1", "UK-2"]
        elif place == "New York CSA":
            queries = ["New York CSA-1", "New York"]
        else:
            queries = [place]
        try:
            for query in queries:
                url = "https://services{}.arcgis.com/{}/arcgis/rest/services/{}/FeatureServer/{}/".format(
                    meta[query][0][0],
                    meta[query][0][1],
                    meta[query][0][2],
                    meta[query][0][3],
                )
                url1 = url + "?f=pjson"
                with urllib.request.urlopen(url1) as response:
                    date = json.loads(response.read())["editingInfo"]["lastEditDate"] / 1000
                    date = datetime.datetime.fromtimestamp(date, tz = datetime.timezone.utc)
                url2 = url + "query?where={}%3E0&outFields=*&returnGeometry=false&f=pjson".format(
                    meta[query][0][4],
                    meta[query][1][0],
                    meta[query][1][1],
                )
                with urllib.request.urlopen(url2) as response:
                    if place == "US":
                        start = 236
                    else:
                        start = 0
                    for entry in json.loads(response.read())["features"][start:]:
                        key = str(entry["attributes"][meta[query][1][0]]).lstrip("0")
                        if key in main:
                            main[key]["cases"] = int(entry["attributes"][meta[query][1][1]])
        except:
            print("Error fetching data for", place)
            continue

    if place in ["Germany", "Berlin", "Netherlands", "London", "New York CSA", "New York"]:
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
                        file_out.write(row.replace('id="{}"'.format(area), 'style="fill:{}"'.format(colour[i])))
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
    print("{}: {} cases total in {} areas".format(place, sum(cases), len(cases)))
