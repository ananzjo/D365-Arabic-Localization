# /* === START OF FILE === */
# File Name: MspVelocityEngine.py
# Version: v38.1 (The Master Timeline Edition)
# Function: Multi-File Processing + Dual-Level ETA (File & Project)
# Language: Python 3.x (Compatible with 3.10)

import xml.etree.ElementTree as ET
from googletrans import Translator
import time
import os
import re
import csv
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import timedelta

# --- Arabic Support Libraries ---
try:
    import arabic_reshaper
    from bidi.algorithm import get_display
    HAS_AR_SUPPORT = True
except ImportError:
    HAS_AR_SUPPORT = False

# --- MSP Project Configuration ---
DICT_FILE = "MSP-dictionary.txt"
QA_LOG_FILE = "MSP_QA_Audit_Log.csv"

INPUT_FILES = [
    "Enable Samadhan Sub-Con.g.xlf",
    "System Application.cs-CZ.xlf",
    "Corrugated Samadhan.cs-CZ.xlf"
]

THREADS = 2 
BATCH_SIZE = 15 
SLEEP_BETWEEN_BATCHES = 1.2

# متغيرات الوقت الكلية للمشروع
project_start_time = 0
total_units_in_project = 0
units_completed_so_far = 0

def fix_terminal_output(text):
    if not text or not HAS_AR_SUPPORT: return text
    if not bool(re.search(r'[\u0600-\u06FF]', text)): return text
    reshaped = arabic_reshaper.reshape(text)
    return get_display(reshaped)

def is_arabic(text):
    if not text: return False
    return bool(re.search(r'[\u0600-\u06FF]', text))

def load_dict():
    msp_dict = {}
    if os.path.exists(DICT_FILE):
        with open(DICT_FILE, "r", encoding="utf-8") as f:
            for line in f:
                if "=" in line:
                    parts = line.strip().split("=", 1)
                    if len(parts) == 2:
                        msp_dict[parts[0].strip()] = parts[1].strip()
    return msp_dict

def log_qa_event(unit_id, source, target, status, reason, file_name):
    file_exists = os.path.isfile(QA_LOG_FILE)
    with open(QA_LOG_FILE, "a", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["Timestamp", "File_Name", "Unit_ID", "Source", "Target", "Status", "Reason"])
        writer.writerow([time.strftime("%Y-%m-%d %H:%M:%S"), file_name, unit_id, source, target, status, reason])

def translate_worker(batch_data):
    units, texts, ids, ns_uri, file_name = batch_data
    translator = Translator()
    results_data = []
    try:
        time.sleep(SLEEP_BETWEEN_BATCHES)
        results = translator.translate(texts, src='en', dest='ar')
        for unit, res, src_text, u_id in zip(units, results, texts, ids):
            target_text = res.text if res else ""
            reason = "Success"
            if not src_text or not src_text.strip():
                status, reason = "FAILED", "Empty Source Field"
            elif not target_text or target_text.strip() == src_text.strip():
                status, reason = "FAILED", "Identical to Source"
            elif not is_arabic(target_text):
                status, reason = "FAILED", "No Arabic in Output"
            else:
                status = "PASSED"
            if status == "PASSED":
                tgt = unit.find(f'{{{ns_uri}}}target')
                if tgt is None: tgt = ET.SubElement(unit, f'{{{ns_uri}}}target')
                tgt.text = target_text
                tgt.set('state', 'translated')
            log_qa_event(u_id, src_text, target_text, status, reason, file_name)
            results_data.append((src_text, target_text, status, reason))
        return results_data
    except Exception as e:
        return [ (t, "N/A", "ERROR", str(e)) for t in texts ]

def process_single_file(file_path, msp_logic, file_index, total_files):
    global units_completed_so_far
    if not os.path.exists(file_path): return

    base, ext = os.path.splitext(file_path)
    output_file = f"{base}02{ext}"
    XLIFF_NS = "urn:oasis:names:tc:xliff:document:1.2"
    ns = {'ns': XLIFF_NS}
    ET.register_namespace('', XLIFF_NS)

    tree = ET.parse(file_path)
    root = tree.getroot()
    units = root.findall('.//ns:trans-unit', ns)
    
    google_tasks = []
    current_units, current_texts, current_ids = [], [], []
    
    for unit in units:
        src_node = unit.find('ns:source', ns)
        tgt_node = unit.find('ns:target', ns)
        src_text = src_node.text if (src_node is not None and src_node.text) else ""
        tgt_text = tgt_node.text if (tgt_node is not None and tgt_node.text) else ""
        if is_arabic(tgt_text): continue
        if src_text.strip() in msp_logic: continue
        
        current_units.append(unit)
        current_texts.append(src_text)
        current_ids.append(unit.get('id', 'N/A'))
        if len(current_texts) >= BATCH_SIZE:
            google_tasks.append((list(current_units), list(current_texts), list(current_ids), XLIFF_NS, file_path))
            current_units, current_texts, current_ids = [], [], []

    if current_texts: google_tasks.append((current_units, current_texts, current_ids, XLIFF_NS, file_path))

    file_start_time = time.time()
    total_batches = len(google_tasks)
    batches_done = 0

    with ThreadPoolExecutor(max_workers=THREADS) as executor:
        futures = {executor.submit(translate_worker, task): task for task in google_tasks}
        for future in as_completed(futures):
            batches_done += 1
            batch_results = future.result()
            units_completed_so_far += len(batch_results)
            
            os.system('cls' if os.name == 'nt' else 'clear')
            # حسابات وقت الملف الحالي
            file_elapsed = time.time() - file_start_time
            file_velocity = (batches_done * BATCH_SIZE) / file_elapsed if file_elapsed > 0 else 0
            file_eta = ((total_batches - batches_done) * BATCH_SIZE) / file_velocity if file_velocity > 0 else 0
            
            # حسابات وقت المشروع الكلي
            total_elapsed = time.time() - project_start_time
            total_velocity = units_completed_so_far / total_elapsed if total_elapsed > 0 else 0
            total_remaining_units = total_units_in_project - units_completed_so_far
            total_eta = total_remaining_units / total_velocity if total_velocity > 0 else 0

            print("="*115)
            print(f"🚀 MSP VELOCITY ENGINE v38.1 | FILE {file_index}/{total_files}: {file_path}")
            print("="*115)
            for src, tgt, status, reason in batch_results[-5:]:
                icon = "✅" if status == "PASSED" else "❌"
                print(f"{icon:<4} | {src[:23]:<25} | {fix_terminal_output(tgt[:22]):<25} | {reason:<20}")
            
            print("-" * 115)
            print(f"📁 CURRENT FILE: {file_path}")
            print(f"⏱️  ELAPSED: {str(timedelta(seconds=int(file_elapsed)))} | ⏳ ETA: {str(timedelta(seconds=int(file_eta)))} | PROGRESS: {(batches_done/total_batches)*100:.1f}%")
            print("-" * 115)
            print(f"🌐 TOTAL PROJECT STATUS:")
            print(f"⏱️  TOTAL ELAPSED: {str(timedelta(seconds=int(total_elapsed)))} | ⏳ TOTAL ETA: {str(timedelta(seconds=int(total_eta)))}")
            print(f"📊 OVERALL VELOCITY: {total_velocity:.1f} units/sec")
            print("="*115)

    tree.write(output_file, encoding='utf-8', xml_declaration=True)

def start_velocity_engine():
    global project_start_time, total_units_in_project
    msp_logic = load_dict()
    project_start_time = time.time()
    
    # حساب إجمالي عدد الوحدات في كل الملفات لمعايرة الـ ETA الكلي
    print("🔍 Pre-calculating total project volume...")
    for f in INPUT_FILES:
        if os.path.exists(f):
            tree = ET.parse(f)
            total_units_in_project += len(tree.findall('.//{urn:oasis:names:tc:xliff:document:1.2}trans-unit'))

    for i, file_path in enumerate(INPUT_FILES, 1):
        process_single_file(file_path, msp_logic, i, len(INPUT_FILES))
    
    total_time = time.time() - project_start_time
    print(f"\n🏆 ALL MISSIONS COMPLETE! TOTAL TIME: {str(timedelta(seconds=int(total_time)))}")

if __name__ == "__main__":
    start_velocity_engine()

# /* === END OF FILE === */