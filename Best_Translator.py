# /* === START OF FILE === */
# File Name: MspVelocityEngine.py
# Version: v31.0 (Real-time Velocity Meter)
# Function: Translate with speed tracking (Units per second)
# Language: Python 3.x

import xml.etree.ElementTree as ET
from googletrans import Translator
import time
import os
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import timedelta

# الإعدادات المعتمدة لمصنع MSP
DICT_FILE = "MSP-dictionary.txt"
INPUT_FILE = "Base Application.ar-JO.xlf"
OUTPUT_FILE = "Base Application.ar-JO02.xlf"
THREADS = 4
BATCH_SIZE = 30
TIMEOUT = 25

def is_arabic(text):
    if not text: return False
    return bool(re.search(r'[\u0600-\u06FF]', text))

def load_dict():
    msp_dict = {}
    if os.path.exists(DICT_FILE):
        with open(DICT_FILE, "r", encoding="utf-8") as f:
            for line in f:
                if "=" in line:
                    k, v = line.strip().split("=", 1)
                    msp_dict[k.strip()] = v.strip()
    return msp_dict

def translate_worker(batch_data):
    units, texts, _ = batch_data
    translator = Translator()
    try:
        results = translator.translate(texts, src='en', dest='ar')
        for unit, res in zip(units, results):
            tgt = unit.find('{urn:oasis:names:tc:xliff:document:1.2}target')
            tgt.text = res.text
            tgt.set('state', 'translated')
        return len(texts)
    except:
        return 0

def start_velocity_engine():
    msp_logic = load_dict()
    ns = {'ns': 'urn:oasis:names:tc:xliff:document:1.2'}
    ET.register_namespace('', ns['ns'])

    print(f"📡 Analyzing: {INPUT_FILE}...")
    tree = ET.parse(INPUT_FILE)
    root = tree.getroot()
    units = root.findall('.//ns:trans-unit', ns)
    
    google_tasks = []
    current_units, current_texts = [], []
    dict_hits = 0
    skipped_arabic = 0

    for unit in units:
        src_node = unit.find('ns:source', ns)
        tgt_node = unit.find('ns:target', ns)
        if tgt_node is None:
            tgt_node = ET.SubElement(unit, '{urn:oasis:names:tc:xliff:document:1.2}target')

        src_text = src_node.text.strip() if src_node.text else ""
        tgt_text = tgt_node.text.strip() if tgt_node.text else ""

        if is_arabic(tgt_text):
            skipped_arabic += 1
            continue

        if src_text in msp_logic:
            tgt_node.text = msp_logic[src_text]
            tgt_node.set('state', 'translated')
            dict_hits += 1
        else:
            current_units.append(unit)
            current_texts.append(src_text)
            if len(current_texts) >= BATCH_SIZE:
                google_tasks.append((list(current_units), list(current_texts), len(google_tasks)))
                current_units, current_texts = [], []

    if current_texts:
        google_tasks.append((current_units, current_texts, len(google_tasks)))

    if not google_tasks:
        print("🙌 All set! No units need translation.")
        return

    # المرحلة 2: محرك السرعة
    start_time = time.time()
    completed_batches = 0
    google_hits = 0
    total_batches = len(google_tasks)

    with ThreadPoolExecutor(max_workers=THREADS) as executor:
        futures = {executor.submit(translate_worker, task): task for task in google_tasks}
        
        for future in as_completed(futures):
            completed_batches += 1
            res_count = future.result()
            google_hits += res_count
            
            # حساب الإحصائيات اللحظية
            elapsed = time.time() - start_time
            # السرعة: عدد الوحدات المترجمة مقسوماً على الوقت
            velocity = google_hits / elapsed if elapsed > 0 else 0
            eta = (total_batches - completed_batches) * (elapsed / completed_batches) if completed_batches > 0 else 0
            
            # تحديث لوحة التحكم
            os.system('cls' if os.name == 'nt' else 'clear')
            print("="*65)
            print(f"🚀  MSP VELOCITY ENGINE v31.0")
            print("="*65)
            print(f"📈 Progress    : {(completed_batches/total_batches)*100:.1f}% ({completed_batches}/{total_batches})")
            print(f"⚡ Speed       : {velocity:.2f} units/sec") # العداد المطلوب
            print(f"🚫 Skipped (AR): {skipped_arabic}")
            print(f"🌐 Google Hits : {google_hits}")
            print(f"⏱️  Elapsed     : {str(timedelta(seconds=int(elapsed)))}")
            print(f"⏳ ETA         : {str(timedelta(seconds=int(eta)))}")
            print("="*65)

    tree.write(OUTPUT_FILE, encoding='utf-8', xml_declaration=True)
    print(f"\n🏆 Done! Output saved to: {OUTPUT_FILE}")

if __name__ == "__main__":
    start_velocity_engine()

# /* === END OF FILE === */