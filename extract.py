import xml.etree.ElementTree as ET
import pandas as pd
import os

def extract_full_xliff_details(file_list, output_excel):
    all_rows = []
    ns = {'ns': 'urn:oasis:names:tc:xliff:document:1.2'}

    for file_path in file_list:
        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            continue
            
        print(f"Processing: {file_path}...")
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
        except Exception as e:
            print(f"Error parsing {file_path}: {e}")
            continue
        
        for unit in root.findall('.//ns:trans-unit', ns):
            # 1. الخصائص الأساسية
            unit_id = unit.get('id', '')
            max_width = unit.get('maxwidth', 'N/A')
            obj_target = unit.get('al-object-target', 'N/A')
            translate_attr = unit.get('translate', 'yes')
            
            # 2. النصوص (مع معالجة القيم الفارغة لتجنب الـ TypeError)
            source_node = unit.find('ns:source', ns)
            target_node = unit.find('ns:target', ns)
            
            source_text = source_node.text if (source_node is not None and source_node.text) else ""
            target_text = target_node.text if (target_node is not None and target_node.text) else ""
            target_state = target_node.get('state', 'new') if target_node is not None else "new"
            
            # 3. الملاحظات (Notes)
            notes = unit.findall('ns:note', ns)
            dev_note = ""
            gen_note = ""
            for note in notes:
                annotates = note.get('from', '')
                content = note.text if note.text else ""
                if annotates == 'Developer':
                    dev_note = content
                elif annotates == 'Xliff Generator':
                    gen_note = content

            # 4. فحص المصطلحات (بند / تفاصيل) - الآن آمن ضد الـ NoneType
            needs_review = "No"
            if "Line" in source_text:
                if not any(word in target_text for word in ["بند", "تفاصيل", "أسطر"]):
                    needs_review = "Yes"

            all_rows.append({
                "File": file_path,
                "Object Target": obj_target,
                "ID": unit_id,
                "Source (EN)": source_text,
                "Target (AR)": target_text,
                "State": target_state,
                "Translate": translate_attr,
                "Max Width": max_width,
                "Developer Note": dev_note,
                "Generator Note": gen_note,
                "Needs Review": needs_review
            })

    if all_rows:
        df = pd.DataFrame(all_rows)
        df.to_excel(output_excel, index=False)
        print(f"\nSuccess! Extracted {len(df)} units into '{output_excel}'")
    else:
        print("No data was extracted.")

# تشغيل الكود
my_files = ["Base Application.ar-JO.xlf", "Corrugated Samadhan.ar-JO.xlf"]
extract_full_xliff_details(my_files, "D365_Localization_Full_Report.xlsx")