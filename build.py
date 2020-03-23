# Created by Chang Chia-huan
import argparse, pathlib, json, csv, io, urllib.request, math, statistics, datetime

parser = argparse.ArgumentParser(description = "This script generates an svg maps for the COVID-19 outbreak for select countries")
parser.add_argument("-c", "--country", help = "Name of country to generate; by default, a map for each country is generated")
args = vars(parser.parse_args())

countries = ["Australia", "France", "Germany", "Italy", "Japan", "Netherlands", "UK", "US", "Taiwan"]

if args["country"] != None:
    main = {args["country"]:{}}
else:
    main = {
        "US": {},
        "Australia": {},
        "France": {},
        "Italy": {},
        #"Canada": {},
        "Germany": {},
        "Netherlands": {},
        "UK": {},
        "Japan": {},
        "Taiwan": {}
    }

with open((pathlib.Path() / "population").with_suffix(".json"), newline = "", encoding = "utf-8-sig") as file:
    population = json.loads(file.read())
    for country in main:
        for place in population[country]:
            main[country][place] = {
                "population": population[country][place],
                "cases": 0
            }

#with open((pathlib.Path() / "meta").with_suffix(".json"), newline = "", encoding = "utf-8") as file:
    #meta = json.loads(file.read())

def arcgis(query):
    global attrs
    attrs = []
    with urllib.request.urlopen(query + "&outFields=*&returnGeometry=false&f=pjson") as response:
        for entry in json.loads(response.read())["features"]:
            attrs.append(entry["attributes"])

for country in countries:
    if country == "Taiwan":
        with urllib.request.urlopen("https://od.cdc.gov.tw/eic/Weekly_Age_County_Gender_19CoV.json") as response:
            data = json.loads(response.read())
            for row in data:
                main["Taiwan"][row["縣市"]]["cases"] += int(row["確定病例數"])
    else:
        url = "https://services{}.arcgis.com/{}/arcgis/rest/services/{}/FeatureServer/0/query?where={}%3E0".format(meta[country][0])
        with urllib.request.urlopen(url) as response:
            i = 0
            for entry in json.loads(response.read())["features"]:
                if meta[country][1][0] in main[country]:
                    if country == "Japan":
                        main[country][entry["attributes"][meta[country][1][0]]]["cases"] += 1
                    else:
                        main[country][entry["attributes"][meta[country][1][0]]]["cases"] = int(ntry["attributes"][meta[country][1][1]])
                        i += 1
                        if country == "US" and i == 54:
                            break

# countries using worldwide data
if "US" in main:
    arcgis("https://services1.arcgis.com/0MSEUqKaxRlEPj5g/arcgis/rest/services/Coronavirus_2019_nCoV_Cases/FeatureServer/1/query?where=ObjectID%3E0")
    i = 0
    for place in attrs:
        if place["Country_Region"] == "US" and place["Province_State"] in main["US"]:
            main["US"][place["Province_State"]]["cases"] = int(place["Confirmed"])
            i += 1
            if i >= 54:
                break

# general countries
if "Australia" in main:
    arcgis("https://services1.arcgis.com/vHnIGBHHqDR6y0CR/arcgis/rest/services/Current_Cases_by_State/FeatureServer/0/query?where=ObjectID%3E0")
    for place in attrs:
        if place["ISO_SUB"] in main["Australia"]:
            main["Australia"][place["ISO_SUB"]]["cases"] = int(place["Cases"])

if "France" in main:
    arcgis("https://services1.arcgis.com/5PzxEwuu4GtMhqQ6/arcgis/rest/services/Regions_DT_Project_Vue/FeatureServer/0/query?where=ObjectID%3E0")
    for place in attrs:
        if place["code_insee"] in main["France"]:
            main["France"][place["code_insee"]]["cases"] = int(place["nb_cas"])

if "Italy" in main:
    arcgis("https://services6.arcgis.com/L1SotImj1AAZY1eK/arcgis/rest/services/riepilogo_province/FeatureServer/0/query?where=ObjectID%3E0")
    for place in attrs:
        if place["sigla_provincia"] in main["Italy"]:
            main["Italy"][place["sigla_provincia"]]["cases"] = int(place["totale_casi"])

# countries with data for all places available
if "Canada" in main:
    arcgis("https://services9.arcgis.com/pJENMVYPQqZZe20v/arcgis/rest/services/HealthRegionTotals/FeatureServer/0/query?where=ObjectID%3E0")
    for place in attrs:
        main["Canada"][place["HR_UID"]]["cases"] = int(place["CaseCount"])

if "Germany" in main:
    arcgis("https://services7.arcgis.com/mOBPykOjAyBO2ZKk/arcgis/rest/services/Kreisgrenzen_2018_mit_Einwohnerzahl/FeatureServer/0/query?where=ObjectID%3E0")
    for place in attrs:
        main["Germany"][place["RS"]]["cases"] = int(place["Fallzahlen"])

if "Netherlands" in main:
    arcgis("https://services.arcgis.com/nSZVuSZjHpEZZbRo/arcgis/rest/services/Aantal_besmettingen_per_1000_inwoners/FeatureServer/0/query?where=ObjectID%3E0")
    for place in attrs:
        main["Netherlands"][place["Gemeentecode"]]["cases"] = int(place["Aantal_Besmettingen"])

# countries with case counts only
if "UK" in main:
    arcgis("https://services1.arcgis.com/0IrmI40n5ZYxTUrV/arcgis/rest/services/NHSR_Cases/FeatureServer/0/query?where=FID%3E0")
    for place in attrs:
        main["UK"][place["GSS_CD"]]["cases"] = int(place["TotalCases"])
    arcgis("https://services1.arcgis.com/0IrmI40n5ZYxTUrV/arcgis/rest/services/UK_Countries_cases/FeatureServer/0/query?where=FID%3E0")
    for place in attrs:
        if place["GSS_CD"] in main["UK"]:
            main["UK"][place["GSS_CD"]]["cases"] = int(place["TotalCases"])

# countries data for individual cases
if "Japan" in main:
    arcgis("https://services6.arcgis.com/5jNaHNYe2AnnqRnS/arcgis/rest/services/COVID19_Japan/FeatureServer/0/query?where=ObjectID%3E0")
    for place in attrs:
        if place["Hospital_Pref"] != "Unknown":
            main["Japan"][place["Hospital_Pref"]]["cases"] += 1

# countries with reliable official data outside Arcgis
if "Taiwan" in main:
    with urllib.request.urlopen("https://od.cdc.gov.tw/eic/Weekly_Age_County_Gender_19CoV.json") as response:
        data = json.loads(response.read())
        for row in data:
            main["Taiwan"][row["縣市"]]["cases"] += int(row["確定病例數"])

colour = ["#fee5d9","#fcbba1","#fc9272","#fb6a4a","#de2d26","#a50f15"]

for country in main:
    if country == "Germany" or country == "Netherlands":
        unit = 10000
    else:
        unit = 1000000

    values = []
    for place in main[country]:
        main[country][place]["pcapita"] = main[country][place]["cases"] / main[country][place]["population"] * unit
        values.append(main[country][place]["pcapita"])

    step = math.sqrt(statistics.mean(values)) / 2.5

    threshold = [0, 0, 0, 0, 0, 0]
    for i in range(6):
        threshold[i] = math.pow(i * step, 2)

    with open((pathlib.Path() / "data" / "template" / country).with_suffix(".svg"), "r", newline = "", encoding = "utf-8") as file_in:
        with open((pathlib.Path() / "results" / country).with_suffix(".svg"), "w", newline = "", encoding = "utf-8") as file_out:
            if threshold[1] > 10:
                num = "{:.0f}"
            else:
                num = "{:.2f}"

            for row in file_in:
                written = False
                for place in main[country]:
                    if row.find('id="{}"'.format(place)) > -1:
                        i = 0
                        while i < 5:
                            if main[country][place]["pcapita"] >= threshold[i + 1]:
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
                        for i in range(6):
                            if row.find('level{}'.format(i)) > -1:
                                if i == 0:
                                    file_out.write(row.replace('level{}'.format(i), "&lt; " + num.format(threshold[1])))
                                else:
                                    file_out.write(row.replace('level{}'.format(i), "≥ " + num.format(threshold[i])))
                    else:
                        file_out.write(row)

    cases = []
    for place in main[country]:
        cases.append(main[country][place]["cases"])
    print("{}: {} cases total in {} areas".format(country, sum(cases), len(cases)))
