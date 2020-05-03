from pathlib import Path
import os

old = ['#fee5d9','#fcbba1','#fc9272','#fb6a4a','#de2d26','#a50f15']
new = ['#fef0d9','#fdd49e','#fdbb84','#fc8d59','#e34a33','#b30000']

p = Path('.')
for file in list(p.glob('*.svg')):
    os.rename(file.name, file.name.replace("-new", ""))
