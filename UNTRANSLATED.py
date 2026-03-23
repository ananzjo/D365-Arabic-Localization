# === START OF FILE ===
# File: extract_untranslated.py
# Version: v1.0.1
# Function: Extracts untranslated units from XLIFF files into a CSV for manual review.
# Components: xml.etree.ElementTree, csv
# Input: .xlf files defined in 'files' list.
# Output: 'untranslated_report.csv' containing ID, Source, and Context.
# Note: Adheres to the # comment style for Python.

import xml.etree.ElementTree as ET
import csv

def extract_untranslated(files):
    ns = {'xliff': "urn:oasis:names:tc:xliff:document:1.2"}
    report_data = []

    for xlf in files:
        try:
            tree = ET.parse(xlf)
            root = tree.getroot()
            
            # Iterate through every translation unit in the XML tree
            for unit in root.findall('.//xliff:trans-unit', ns):
                target = unit.find('xliff:target', ns)
                source = unit.find('xliff:source', ns)
                note = unit.find('xliff:note', ns)
                
                # Evaluation: Check if target is missing or not marked 'translated'
                is_untranslated = (target is None) or (target.get('state') != 'translated')
                
                if is_untranslated:
                    report_data.append({
                        'File': xlf,
                        'ID': unit.get('id'),
                        'Source (EN)': source.text if source is not None else "",
                        'Context/Note': note.text if note is not None else "No context provided"
                    })
        except Exception as e:
            print(f"Error processing {xlf}: {e}")

    # Exporting results to CSV for Excel review
    keys = ['File', 'ID', 'Source (EN)', 'Context/Note']
    with open('untranslated_report.csv', 'w', newline='', encoding='utf-8-sig') as f:
        dict_writer = csv.DictWriter(f, fieldnames=keys)
        dict_writer.writeheader()
        dict_writer.writerows(report_data)

# File list specific to the MSP / Samadhan ERP project
files = ["Base Application.ar-JO.xlf", "System Application.ar-JO.xlf", "Corrugated Samadhan.ar-JO.xlf"]

if __name__ == "__main__":
    extract_untranslated(files)
    print("Extraction complete. 'untranslated_report.csv' has been generated.")

# === END OF FILE ===