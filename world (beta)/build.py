# Created by Chang Chia-huan
import pathlib, json, csv, io, urllib.request, math, statistics

with open("places.json", newline = "", encoding = "utf-8") as file:
    main = json.loads(file.read())

with urllib.request.urlopen("https://services1.arcgis.com/0MSEUqKaxRlEPj5g/arcgis/rest/services/Coronavirus_2019_nCoV_Cases/FeatureServer/1/query?where=OBJECTID%3E0&outFields=*&f=pjson") as response:
    data = json.loads(response.read())
    for row in data["features"]:
        row["attributes"]["Country_Region"] = row["attributes"]["Country_Region"].replace("*", "")
        if row["attributes"]["Province_State"] in main:
            main[row["attributes"]["Province_State"]]["cases"] = int(row["attributes"]["Confirmed"])
        elif row["attributes"]["Country_Region"] in main:
            main[row["attributes"]["Country_Region"]]["cases"] += int(row["attributes"]["Confirmed"])
            if row["attributes"]["Province_State"] != None:
                print(row["attributes"]["Province_State"], "in", row["attributes"]["Country_Region"])

values = []
for place in main:
    if main[place]["cases"] > 0 and main[place]["population"] != None:
        main[place]["pcapita"] = round(main[place]["cases"] / main[place]["population"], 2)
        values.append(main[place]["pcapita"])

step = math.sqrt(statistics.mean(values)) / 3

thresholds = [0, 0, 0, 0, 0, 0, 0]
for i in range(7):
    thresholds[i] = round(math.pow(step * i, 2), 2)

colours = ['#fee5d9','#fcbba1','#fc9272','#fb6a4a','#ef3b2c','#cb181d','#99000d']

with open("template.svg", "r", newline = "", encoding = "utf-8") as file_in:
    with open("per-capita.svg", "w", newline = "", encoding = "utf-8") as file_out:
        r = 0
        for row in file_in:
            r += 1
            if r == 158:
                levels = [[], [], [], [], [], [], []]
                for place in main:
                    if "pcapita" in main[place]:
                        i = 0
                        while i < 6:
                            if main[place]["pcapita"] >= thresholds[i + 1]:
                                i += 1
                            else:
                                break
                        main[place]["threshold met"] = thresholds[i]
                        main[place]["fill"] = colours[i]
                        levels[i].append(main[place]["code"])
                    else:
                        main[place]["fill"] = "#e0e0e0"
                for i in range(7):
                    file_out.write(", ".join(levels[i]) + "\n")
                    file_out.write("{" + "\n")
                    file_out.write("   fill:" + colours[i] + ";\n")
                    file_out.write("}" + "\n")
            else:
                file_out.write(row)

print("Number of data figures:", len(values))
print("Colours:", colours)
print("Thresholds:", thresholds, "Max:", max(values))

with open("details.json", "w", newline = "", encoding = "utf-8") as file:
    file.write(json.dumps(main, indent = 2, ensure_ascii = False))
