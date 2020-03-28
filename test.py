import statistics

incl, excl = [], []

for i in range(5):
    incl.append(i)

for i in range(1, 4):
    excl.append(i)

print(statistics.quantiles(incl, n = 4, method = "inclusive"))
print(statistics.quantiles(excl, n = 4))
