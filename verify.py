# /* === START OF FILE === */
# File Name: MspVelocityEngine.py
# Version: v36.1 (The Bug-Free Architect)
# Function: Fixed Unpacking Error & Auto-Structure XLF
# Language: Python 3.x (Compatible with 3.10)

import xml.etree.ElementTree as ET
from googletrans import Translator
import time
import os
import re
import csv
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import timedelta

# --- MSP Project Configuration ---
DICT_FILE = "MSP-dictionary.txt"
INPUT_FILE = "Plant and Maintenance Samadhan.g.xlf"
OUTPUT_FILE = "Plant and Maintenance Samadhan.g02.xlf"
QA_LOG_FILE = "MSP_QA_Audit_Log.csv"

THREADS = 2 
BATCH_SIZE = 15 
SLEEP_BETWEEN_BATCHES = 1.2

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

def log_qa_event(unit_id, source, target, status):
    file_exists = os.path.isfile(QA_LOG_FILE)
    with open(QA_LOG_FILE, "a", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["Timestamp", "Unit_ID", "Source", "Target", "Status"])
        writer.writerow([time.strftime("%Y-%m-%d %H:%M:%S"), unit_id, source, target, status])

def translate_worker(batch_data):
    # استقبال 4 قيم بوضوح
    units, texts, ids, ns_uri = batch_data
    translator = Translator()
    results_data = []
    try:
        time.sleep(SLEEP_BETWEEN_BATCHES)
        results = translator.translate(texts, src='en', dest='ar')
        
        for unit, res, src_text, u_id in zip(units, results, texts, ids):
            target_text = res.text if res else ""
            
            if not src_text or not src_text.strip():
                status = "FAIL_EMPTY_SRC"
            elif not target_text or target_text.strip() == src_text.strip():
                status = "FAIL_NO_TRANS"
            elif not is_arabic(target_text):
                status = "FAIL_NOT_ARABIC"
            else:
                status = "PASSED"

            if status == "PASSED":
                tgt = unit.find(f'{{{ns_uri}}}target')
                if tgt is None:
                    tgt = ET.SubElement(unit, f'{{{ns_uri}}}target')
                tgt.text = target_text
                tgt.set('state', 'translated')
            
            log_qa_event(u_id, src_text, target_text, status)
            results_data.append((src_text, target_text, status))
            
        return results_data
    except Exception as e:
        return [ (t, str(e), "CRITICAL_ERROR") for t in texts ]

def start_velocity_engine():
    msp_logic = load_dict()
    XLIFF_NS = "urn:oasis:names:tc:xliff:document:1.2"
    ns = {'ns': XLIFF_NS}
    ET.register_namespace('', XLIFF_NS)

    if not os.path.exists(INPUT_FILE):
        print(f"❌ Error: File '{INPUT_FILE}' not found!")
        return

    print(f"🏗️  Architect Mode: Building structure for {INPUT_FILE}...")
    tree = ET.parse(INPUT_FILE)
    root = tree.getroot()
    units = root.findall('.//ns:trans-unit', ns)
    
    google_tasks = []
    current_units, current_texts, current_ids = [], [], []
    skipped_count = 0

    for unit in units:
        src_node = unit.find('ns:source', ns)
        tgt_node = unit.find('ns:target', ns)
        u_id = unit.get('id', 'N/A')
        
        src_text = src_node.text if (src_node is not None and src_node.text) else ""
        tgt_text = tgt_node.text if (tgt_node is not None and tgt_node.text) else ""

        if is_arabic(tgt_text):
            skipped_count += 1
            continue

        if src_text.strip() in msp_logic:
            if tgt_node is None:
                tgt_node = ET.SubElement(unit, f'{{{XLIFF_NS}}}target')
            tgt_node.text = msp_logic[src_text.strip()]
            tgt_node.set('state', 'translated')
            log_qa_event(u_id, src_text, tgt_node.text, "PASSED_DICT")
            skipped_count += 1
        else:
            current_units.append(unit)
            current_texts.append(src_text)
            current_ids.append(u_id)
            if len(current_texts) >= BATCH_SIZE:
                # إرسال 4 قيم للـ worker
                google_tasks.append((list(current_units), list(current_texts), list(current_ids), XLIFF_NS))
                # تصحيح الخطأ: تصفير 3 متغيرات فقط لمطابقة الطرف الأيسر
                current_units, current_texts, current_ids = [], [], []

    if current_texts:
        google_tasks.append((current_units, current_texts, current_ids, XLIFF_NS))

    # --- Dashboard Execution ---
    start_time = time.time()
    total_batches = len(google_tasks)
    batches_done, total_passed, total_failed = 0, 0, 0

    if total_batches == 0:
        print("🙌 All units are structurally sound and translated!")
        return

    with ThreadPoolExecutor(max_workers=THREADS) as executor:
        futures = {executor.submit(translate_worker, task): task for task in google_tasks}
        
        for future in as_completed(futures):
            batches_done += 1
            batch_results = future.result()
            
            os.system('cls' if os.name == 'nt' else 'clear')
            print("="*85)
            print(f"🚀 MSP VELOCITY ENGINE v36.1 | STRUCTURAL ARCHITECT MODE")
            print("="*85)
            
            for src, tgt, status in batch_results[-8:]:
                icon = "✅" if status == "PASSED" else "❌"
                print(f"{icon} [SRC]: {src[:30]:<32} | [TGT]: {tgt[:30]:<32} | {status}")
            
            for _, _, status in batch_results:
                if "PASSED" in status: total_passed += 1
                else: total_failed += 1

            elapsed = time.time() - start_time
            velocity = (total_passed + total_failed) / elapsed if elapsed > 0 else 0
            remaining = (total_batches - batches_done) * BATCH_SIZE
            eta = remaining / velocity if velocity > 0 else 0
            
            print("-" * 85)
            print(f"📊 PROGRESS: {(batches_done/total_batches)*100:.1f}% | BATCH: {batches_done}/{total_batches}")
            print(f"⚡ VELOCITY: {velocity:.2f} units/sec | ⏱️ ELAPSED: {str(timedelta(seconds=int(elapsed)))}")
            print(f"⏳ ETA:      {str(timedelta(seconds=int(eta)))} | 🚫 SKIPPED/DICT: {skipped_count}")
            print(f"🛡️ QA STATS: PASSED: {total_passed} | FAILED: {total_failed}")
            print("="*85)

    tree.write(OUTPUT_FILE, encoding='utf-8', xml_declaration=True)
    print(f"\n🏆 MISSION COMPLETE! Version 36.1 Resolved the Unpacking Issue.")
    print(f"📁 Output: {OUTPUT_FILE}")

if __name__ == "__main__":
    start_velocity_engine()

# /* === END OF FILE === */