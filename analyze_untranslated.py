import xml.etree.ElementTree as ET

def analyze_untranslated(xlf):
    ns = {'xliff': "urn:oasis:names:tc:xliff:document:1.2"}
    try:
        tree = ET.parse(xlf)
        root = tree.getroot()
        results = []
        for unit in root.findall('.//xliff:trans-unit', ns):
            target = unit.find('xliff:target', ns)
            state = target.get('state', 'none') if target is not None else 'none'
            source = unit.find('xliff:source', ns)
            stext = source.text if source is not None else "N/A"
            translate_attr = unit.get('translate', 'yes')
            
            # Logic from TranslatorScript for "translated"
            # ET register_namespace('', 'urn:oasis:names:tc:xliff:document:1.2')
            
            is_trans = False
            if target is not None:
                import re
                target_text = target.text
                if state == 'translated':
                   # Check logic from TranslatorScript
                   if target_text == stext and not re.search(r'[a-zA-Z]', stext):
                       is_trans = True
                   elif target_text and re.search(r'[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF]', target_text):
                       is_trans = True
            
            if not is_trans:
                results.append({
                    'id': unit.get('id'),
                    'source': stext,
                    'target': target.text if target is not None else "MISSING",
                    'state': state,
                    'translate': translate_attr
                })
        return results
    except Exception as e:
        return str(e)

files = ["Base Application.ar-JO.xlf", "System Application.ar-JO.xlf", "Corrugated Samadhan.ar-JO.xlf"]
for f in files:
    res = analyze_untranslated(f)
    if isinstance(res, str):
        print(f"{f} Error: {res}")
        continue
    print(f"{f}: {len(res)} untranslated units found.")
    for r in res[:20]:
        print(f"ID: {r['id']} | Src: {r['source']} | State: {r['state']} | Translate: {r['translate']}")
