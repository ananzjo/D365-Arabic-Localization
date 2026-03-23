# /* === START OF FILE === */
# File Name: msp_xlf_classic_pro_v1.8.5.py
# Version: v1.8.5
# Function: Classic Resume Logic with FA/PO Rules & Real-time Dashboard.
# /* ======================================================================== */

import os, json, time, re, sys, io, random
import pandas as pd
from lxml import etree
from tqdm import tqdm
from googletrans import Translator

def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] >>> {msg}", flush=True)

try:
    from arabic_reshaper import reshape
    from bidi.algorithm import get_display
    def fix_ar(t): return get_display(reshape(t))
except:
    def fix_ar(t): return t

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# --- إعدادات مشروع MSP الثابتة ---
EXCEL_DICTIONARY = "Dictionary.xlsx"
TARGET_FILES = ["Corrugated Samadhan.cs-CZ.xlf", "System Application.cs-CZ.xlf"]
CHECKPOINT_PATH = "msp_checkpoint02.json"

PROTECTED_BRANDS = ["VAT", "FA", "PO", "SQL", "ERP", "SAMADHAN", "Copilot", "Power BI", "Microsoft", "Azure","D365", "Dynamics 365"]

MSP_FIXED_LOGIC = {
    "Journal": "دفتر يومية", "Journals": "دفاتر يومية", "Prod.": "إنتاج", "Production": "إنتاج",
    "Entry": "قيد", "Entries": "قيود", "Item": "صنف", "Items": "أصناف",
    "Posting": "ترحيل", "Post": "ترحيل", "Line": "بند", "Lines": "بنود",
    "Fixed Assets": "الأصول الثابتة", "Fixed Asset": "أصل ثابت",
    "Purchase Order": "طلب شراء", "Purchase Orders": "طلبات شراء",
    "Bin": "رف", "Bins": "أرفف"
}

translator = Translator()

def format_time(seconds):
    mins, secs = divmod(int(seconds), 60)
    hrs, mins = divmod(mins, 60)
    return f"{hrs:02d}:{mins:02d}:{secs:02d}"

def smart_translate(text, msp_dict):
    if not text: return text
    
    # 1. القاموس والقواعد أولاً
    clean_text = text.strip(".,:;() ")
    if text in msp_dict:
        return msp_dict[text]
    elif clean_text in MSP_FIXED_LOGIC:
        return MSP_FIXED_LOGIC[clean_text]
    
    # 2. الترجمة التلقائية مع حماية البراندات
    try:
        time.sleep(random.uniform(0.6, 1.2)) # تأخير أمان IP
        res = translator.translate(text, src='en', dest='ar')
        translated = res.text
        for brand in PROTECTED_BRANDS:
            translated = re.sub(rf'\b{re.escape(brand)}\b', brand, translated, flags=re.IGNORECASE)
        
        # تصحيحات MSP الصارمة
        corrections = {"مجلة": "دفتر يومية", "نشر": "ترحيل", "أمر شراء": "طلب شراء"}
        for k, v in corrections.items(): translated = translated.replace(k, v)
        return translated
    except:
        return text

def run_engine():
    print("="*60)
    print(fix_ar("--- محرك MSP الاحترافي: v1.8.5 (Classic Dashboard) ---"))
    print("="*60)

    state = {"file": "", "last_index": 0}
    if os.path.exists(CHECKPOINT_PATH):
        with open(CHECKPOINT_PATH, 'r', encoding='utf-8') as f:
            state = json.load(f)

    if not os.path.exists(EXCEL_DICTIONARY):
        log("❌ Dictionary.xlsx missing!"); return

    df = pd.read_excel(EXCEL_DICTIONARY)
    msp_dict = dict(zip(df.iloc[:, 1].astype(str).str.strip(), df.iloc[:, 2].astype(str).str.strip()))

    for file_name in TARGET_FILES:
        if not os.path.exists(file_name): continue
        if state["file"] and file_name < state["file"]: continue

        output_name = file_name.replace(".cs-CZ.xlf", ".ar-JO.xlf")
        tree = etree.parse(file_name)
        root = tree.getroot()
        ns = {"ns": "urn:oasis:names:tc:xliff:document:1.2"}
        units = root.xpath("//ns:trans-unit", namespaces=ns)
        
        total_units = len(units)
        start_idx = state["last_index"] if state["file"] == file_name else 0
        start_time = time.time()

        print(f"\n📂 {fix_ar('عنصر المعالجة:')} {file_name}")

        with tqdm(total=total_units, initial=start_idx, unit="unit", desc=file_name) as pbar:
            for i in range(start_idx, total_units):
                unit = units[i]
                source = unit.find("ns:source", namespaces=ns)
                target = unit.find("ns:target", namespaces=ns)
                
                if target is None:
                    target = etree.SubElement(unit, "{urn:oasis:names:tc:xliff:document:1.2}target")

                if source is not None and source.text:
                    src_val = source.text
                    translated = smart_translate(src_val, msp_dict)
                    target.text = translated
                    target.set("state", "translated")

                    # تحديث لوحة المعلومات الحية بجانب الـ Progress Bar
                    elapsed = time.time() - start_time
                    speed = (i - start_idx + 1) / elapsed if elapsed > 0 else 0.1
                    eta = (total_units - i) / speed
                    
                    p_en = src_val[:15]
                    p_ar = translated[:15]
                    pbar.set_postfix_str(f"ETA: {format_time(eta)} | {p_en}->{fix_ar(p_ar)}")

                # حفظ دوري كل 15 جملة (نظام الأمان الخاص بك)
                if (i + 1) % 15 == 0 or i == total_units - 1:
                    tree.write(output_name, encoding="utf-8", xml_declaration=True)
                    with open(CHECKPOINT_PATH, 'w', encoding='utf-8') as f:
                        json.dump({"file": file_name, "last_index": i + 1}, f)
                
                pbar.update(1)

        state = {"file": "", "last_index": 0} 

    print("\n✅ " + fix_ar("اكتملت المهمة بنجاح وفق منطق MSP."))

if __name__ == "__main__":
    try:
        run_engine()
    except KeyboardInterrupt:
        print("\n⚠️ " + fix_ar("تم إيقاف المحرك يدوياً.. الحفظ آمن."))