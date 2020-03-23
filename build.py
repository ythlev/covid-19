# Created by Chang Chia-huan
import argparse, pathlib, json, csv, io, urllib.request, math, statistics, datetime

parser = argparse.ArgumentParser(description = "This script generates an svg maps for the COVID-19 outbreak for select countries")
parser.add_argument("-c", "--country", help = "Name of country to generate; by default, a map for each country is generated")
args = vars(parser.parse_args())

if args["country"] != None:
    countries = [args["country"]]
else:
    countries = ["Australia", "Canada", "France", "Germany", "Italy", "Japan", "Netherlands", "UK", "US", "Taiwan"]

with open((pathlib.Path() / "population").with_suffix(".json"), newline = "", encoding = "utf-8-sig") as file:
    population = json.loads(file.read())

with open((pathlib.Path() / "meta").with_suffix(".json"), newline = "", encoding = "utf-8") as file:
    meta = json.loads(file.read())

colour = ['#fee5d9','#fcae91','#fb6a4a','#de2d26','#a50f15']

for country in countries:
    main = {}
    for place in population[country]:
        main[place] = {
            "population": population[country][place],
            "cases": 0
        }

    if country == "Taiwan":
        with urllib.request.urlopen("https://od.cdc.gov.tw/eic/Weekly_Age_County_Gender_19CoV.json") as response:
            data = json.loads(response.read())
            for row in data:
                main[row["縣市"]]["cases"] += int(row["確定病例數"])
    else:
        if country == "UK":
            queries = ["UK-1", "UK-2"]
        else:
            queries = [country]
        for query in queries:
            url = "https://services{}.arcgis.com/{}/arcgis/rest/services/{}/FeatureServer/{}/query?where={}%3E0".format(
                meta[query][0][0],
                meta[query][0][1],
                meta[query][0][2],
                meta[query][0][3],
                meta[query][0][4]
            )
            url = url + "&outFields=*&returnGeometry=false&f=pjson"
            with urllib.request.urlopen(url) as response:
                if country == "US":
                    start = 236
                else:
                    start = 0
                for entry in json.loads(response.read())["features"][start:]:
                    if entry["attributes"][meta[query][1][0]] in main:
                        if country == "Japan" and entry["attributes"][meta[query][1][0]] != "Unknown":
                            main[entry["attributes"][meta[query][1][0]]]["cases"] += 1
                        else:
                            main[entry["attributes"][meta[query][1][0]]]["cases"] = int(entry["attributes"][meta[query][1][1]])

    if country == "Germany" or country == "Netherlands":
        unit = 10000
    else:
        unit = 1000000

    values = []
    for place in main:
        main[place]["pcapita"] = main[place]["cases"] / main[place]["population"] * unit
        values.append(main[place]["pcapita"])

    step = math.sqrt(statistics.mean(values)) / 2

    threshold = [0, 0, 0, 0, 0]
    for i in range(5):
        threshold[i] = math.pow(i * step, 2)

    with open((pathlib.Path() / "template" / country).with_suffix(".svg"), "r", newline = "", encoding = "utf-8") as file_in:
        with open((pathlib.Path() / "results" / country).with_suffix(".svg"), "w", newline = "", encoding = "utf-8") as file_out:
            if threshold[1] > 10:
                num = "{:.0f}"
            else:
                num = "{:.2f}"

            for row in file_in:
                written = False
                for place in main:
                    if row.find('id="{}"'.format(place)) > -1:
                        i = 0
                        while i < 4:
                            if main[place]["pcapita"] >= threshold[i + 1]:
                                i += 1
                            else:
                                break
                        file_out.write(row.replace('id="{}"'.format(place), 'style="fill:{}"'.format(colour[i])))
                        written = True
                        break

                if written == False:
                    if row.find('>Date<') > -1:
                        file_out.write(row.replace('Date', datetime.date.today().isoformat()))
                    elif row.find('>level') > -1:
                        for i in range(5):
                            if row.find('level{}'.format(i)) > -1:
                                if i == 0:
                                    file_out.write(row.replace('level{}'.format(i), "&lt; " + num.format(threshold[1])))
                                else:
                                    file_out.write(row.replace('level{}'.format(i), "≥ " + num.format(threshold[i])))
                    else:
                        file_out.write(row)

    cases = []
    for place in main:
        cases.append(main[place]["cases"])
    print("{}: {} cases total in {} areas".format(country, sum(cases), len(cases)))
