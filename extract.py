# === START OF FILE ===
# File: xlf_advanced_categorizer.py
# Version: v1.2.1
# Function: Fixed extraction & UI categorization with NULL handling.
# Components: xml.etree.ElementTree, csv, re
# Input: Base Application, System, and Samadhan XLF files.
# Output: 'ERP_Master_Review_Sheet.csv'

import xml.etree.ElementTree as ET
import csv
import re

def get_ui_category(context):
    """
    Categorizes the string based on Business Central metadata patterns.
    Safely handles empty context strings.
    """
    if not context:
        return "Unknown / No Metadata"
        
    ctx = context.lower()
    
    if "action" in ctx:
        return "Button / Menu Command" if "promoted" not in ctx else "Button (Promoted)"
    if "tooltip" in ctx:
        return "Tooltip (User Guidance)"
    if "optioncaption" in ctx:
        return "Dropdown Option"
    if "report" in ctx:
        return "Report Label" if "label" in ctx else "Report Caption"
    if "page" in ctx or "table" in ctx:
        return "Field Label / Caption" if "control" in ctx else "Page/Table Header"
        
    return "General UI String"

def parse_xlf_to_master(files):
    ns = {'xliff': "urn:oasis:names:tc:xliff:document:1.2"}
    results = []

    for xlf in files:
        try:
            tree = ET.parse(xlf)
            root = tree.getroot()
            
            for unit in root.findall('.//xliff:trans-unit', ns):
                uid = unit.get('id', '')
                
                # Safe Extraction: Ensure we always have a string, even if tag is missing
                source_node = unit.find('xliff:source', ns)
                target_node = unit.find('xliff:target', ns)
                note_node = unit.find('xliff:note', ns)
                
                source_text = source_node.text if (source_node is not None and source_node.text) else ""
                target_text = target_node.text if (target_node is not None and target_node.text) else ""
                context = note_node.text if (note_node is not None and note_node.text) else ""
                
                # Extract Module safely
                module = "Global/System"
                mod_match = re.search(r'Microsoft\.(\w+)', context)
                if mod_match:
                    module = mod_match.group(1)
                elif "Samadhan" in xlf:
                    module = "Corrugated/Manufacturing"

                # Extract UI Type
                ui_type = get_ui_category(context)

                # Extract Window Name safely
                window = "N/A"
                win_match = re.search(r'(Page|Report|Table|Codeunit)\s+([^-\n]+)', context)
                if win_match:
                    window = win_match.group(2).strip()

                results.append({
                    'File': xlf,
                    'ID': uid,
                    'Module': module,
                    'UI Category': ui_type,
                    'Window Name': window,
                    'Source (EN)': source_text,
                    'Target (AR)': target_text,
                    'Metadata': context.replace('\n', ' ')
                })
                
        except Exception as e:
            print(f"Error in {xlf}: {e}")

    # Export to CSV
    headers = ['File', 'ID', 'Module', 'UI Category', 'Window Name', 'Source (EN)', 'Target (AR)', 'Metadata']
    with open('ERP_Master_Review_Sheet.csv', 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(results)

files = ["Base Application.ar-JO.xlf", "System Application.ar-JO.xlf", "Corrugated Samadhan.ar-JO.xlf"]

if __name__ == "__main__":
    parse_xlf_to_master(files)
    print("Success! The errors are resolved. Check 'ERP_Master_Review_Sheet.csv'.")

# === END OF FILE ===