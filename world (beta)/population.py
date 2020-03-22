import json, csv

with open("data.json", newline = "", encoding = "utf-8") as file:
    main = json.loads(file.read())

with open("https://raw.githubusercontent.com/mledoze/countries/master/countries.json", newline = "", encoding = "utf-8") as file:
    country = json.loads(file.read())
    for row in country:
        if row["Year"] == "2019" and row["Series"] == "Population mid-year estimates (millions)":
            if row["Region/Country/Area"] in main and main[row["Region/Country/Area"]]["population"] != None:
                try:
                    main[row["Region/Country/Area"]]["population"] = float(row["Value"])
                except:
                    print(row["Region/Country/Area"], "cannot be added")
                    continue
            else:
                print(row["Region/Country/Area"], "not found")

with open("data-generated.json", "w", newline = "", encoding = "utf-8") as file:
    file.write(json.dumps(main, indent = 2, ensure_ascii = False))
