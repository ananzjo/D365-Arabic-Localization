#/* === START OF FILE === */
# File: XLF-to-CSV-Advanced.py
# Version: v1.0.0
# Function: تحويل ملفات XLF إلى CSV مع استخراج ملاحظات المطورين وحساب التكرار
# Components: XML Parser, Counter, CSV Writer

import csv
import xml.etree.ElementTree as ET
from collections import Counter

# أسماء الملفات التي رفعتها
files_to_process = [
    "Base Application.cs-CZ.xlf",
    "System Application.cs-CZ.xlf",
    "Corrugated Samadhan.cs-CZ.xlf"
]

OUTPUT_CSV = "ERP_Terms_Analysis.csv"
ns = {'xliff': "urn:oasis:names:tc:xliff:document:1.2"}

def extract_and_analyze():
    all_data = [] # لتخزين النصوص مع ملاحظاتها
    term_counts = Counter() # لحساب التكرار
    
    for file_name in files_to_process:
        print(f"جاري معالجة الملف: {file_name}...")
        try:
            tree = ET.parse(file_name)
            root = tree.getroot()
            units = root.findall('.//xliff:trans-unit', ns)
            
            for unit in units:
                source_text = unit.find('xliff:source', ns).text
                if source_text:
                    source_text = source_text.strip()
                    term_counts[source_text] += 1
                    
                    # استخراج ملاحظات المطور (Developer Notes)
                    notes = unit.findall('xliff:note', ns)
                    dev_note = ""
                    category = "General"
                    
                    for note in notes:
                        if note.get('from') == 'Developer':
                            dev_note = note.text if note.text else ""
                            # تصنيف تقريبي بناءً على محتوى الملاحظة (Namespace)
                            if "Namespace" in dev_note:
                                category = dev_note.split('=')[1].split(')')[0]
                            break
                    
                    all_data.append({
                        'Source Text': source_text,
                        'Note': dev_note,
                        'Category': category
                    })
                    
        except Exception as e:
            print(f"خطأ في قراءة {file_name}: {e}")

    # إزالة التكرار من القائمة النهائية مع الاحتفاظ ببيانات كل مصطلح
    unique_data = {}
    for entry in all_data:
        text = entry['Source Text']
        if text not in unique_data:
            unique_data[text] = entry

    # حفظ النتائج في ملف CSV
    with open(OUTPUT_CSV, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        # العناوين: النص الأصلي، الترجمة (فارغة)، عدد التكرار، التصنيف، ملاحظة المطور
        writer.writerow(["Source Text", "Arabic Translation", "Count", "Category", "Developer Note"])
        
        for text in sorted(unique_data.keys()):
            item = unique_data[text]
            writer.writerow([
                item['Source Text'], 
                "", # مكان الترجمة
                term_counts[text], 
                item['Category'], 
                item['Note']
            ])

    print(f"\nتم بنجاح! تم استخراج {len(unique_data)} مصطلح فريد.")
    print(f"الملف الناتج: {OUTPUT_CSV}")

if __name__ == "__main__":
    extract_and_analyze()
#/* === END OF FILE === */