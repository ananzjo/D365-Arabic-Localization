import xml.etree.ElementTree as ET
import sys

def count_units(xlf):
    ns = {'xliff': "urn:oasis:names:tc:xliff:document:1.2"}
    try:
        tree = ET.parse(xlf)
        root = tree.getroot()
        total = 0
        translated = 0
        new = 0
        untranslated = 0
        for unit in root.findall('.//xliff:trans-unit', ns):
            total += 1
            target = unit.find('xliff:target', ns)
            if target is None:
                untranslated += 1
            else:
                state = target.get('state', 'new')
                if state == 'translated':
                    translated += 1
                elif state == 'new':
                    new += 1
                else:
                    untranslated += 1
        return total, translated, new, untranslated
    except Exception as e:
        return str(e)

files = ["Base Application.ar-JO.xlf", "System Application.ar-JO.xlf", "Corrugated Samadhan.ar-JO.xlf"]
with open("stats.txt", "w") as f_out:
    for f in files:
        res = count_units(f)
        line = f"{f}: {res}"
        print(line)
        f_out.write(line + "\n")
