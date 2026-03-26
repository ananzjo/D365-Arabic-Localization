# /* === START OF FILE === */
# File Name: MspVelocityEngine.py
# Version: v37.6 (The Diagnostic Architect)
# Function: Auto-Structure XLF + RTL Support + Failure Diagnostics
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
INPUT_FILE = "Base Application.cs-CZ.xlf"
OUTPUT_FILE = "Base Application.ar-JO.xlf"
QA_LOG_FILE = "MSP_QA_Audit_Log02.csv"

THREADS = 2 
BATCH_SIZE = 15 
SLEEP_BETWEEN_BATCHES = 1.2

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

def log_qa_event(unit_id, source, target, status, reason):
    file_exists = os.path.isfile(QA_LOG_FILE)
    with open(QA_LOG_FILE, "a", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["Timestamp", "Unit_ID", "Source", "Target", "Status", "Reason"])
        writer.writerow([time.strftime("%Y-%m-%d %H:%M:%S"), unit_id, source, target, status, reason])

def translate_worker(batch_data):
    units, texts, ids, ns_uri = batch_data
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
                if tgt is None:
                    tgt = ET.SubElement(unit, f'{{{ns_uri}}}target')
                tgt.text = target_text
                tgt.set('state', 'translated')
            
            log_qa_event(u_id, src_text, target_text, status, reason)
            results_data.append((src_text, target_text, status, reason))
            
        return results_data
    except Exception as e:
        return [ (t, "N/A", "ERROR", str(e)) for t in texts ]

def start_velocity_engine():
    msp_logic = load_dict()
    XLIFF_NS = "urn:oasis:names:tc:xliff:document:1.2"
    ns = {'ns': XLIFF_NS}
    ET.register_namespace('', XLIFF_NS)

    if not os.path.exists(INPUT_FILE):
        print(f"❌ Error: File '{INPUT_FILE}' not found!")
        return

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
            if tgt_node is None: tgt_node = ET.SubElement(unit, f'{{{XLIFF_NS}}}target')
            tgt_node.text = msp_logic[src_text.strip()]
            tgt_node.set('state', 'translated')
            log_qa_event(u_id, src_text, tgt_node.text, "PASSED_DICT", "Dictionary Match")
            skipped_count += 1
        else:
            current_units.append(unit)
            current_texts.append(src_text)
            current_ids.append(u_id)
            if len(current_texts) >= BATCH_SIZE:
                google_tasks.append((list(current_units), list(current_texts), list(current_ids), XLIFF_NS))
                current_units, current_texts, current_ids = [], [], []

    if current_texts: google_tasks.append((current_units, current_texts, current_ids, XLIFF_NS))

    start_time = time.time()
    total_batches = len(google_tasks)
    batches_done, total_passed, total_failed = 0, 0, 0

    with ThreadPoolExecutor(max_workers=THREADS) as executor:
        futures = {executor.submit(translate_worker, task): task for task in google_tasks}
        for future in as_completed(futures):
            batches_done += 1
            batch_results = future.result()
            os.system('cls' if os.name == 'nt' else 'clear')
            print("="*115)
            print(f"🚀 MSP VELOCITY ENGINE v37.6 | DIAGNOSTIC MODE | RTL SUPPORT")
            print("="*115)
            print(f"{'STAT':<4} | {'SOURCE (EN)':<25} | {'TARGET (AR)':<25} | {'REASON / STATUS':<20}")
            print("-" * 115)
            
            for src, tgt, status, reason in batch_results[-10:]:
                icon = "✅" if status == "PASSED" else "❌"
                display_tgt = fix_terminal_output(tgt[:22])
                # طباعة البيانات مع سبب الفشل
                print(f"{icon:<4} | {src[:23]:<25} | {display_tgt:<25} | {reason:<20}")
            
            for _, _, status, _ in batch_results:
                if status == "PASSED": total_passed += 1
                else: total_failed += 1

            elapsed = time.time() - start_time
            velocity = (total_passed + total_failed) / elapsed if elapsed > 0 else 0
            remaining = (total_batches - batches_done) * BATCH_SIZE
            eta = remaining / velocity if velocity > 0 else 0
            
            print("-" * 115)
            print(f"📊 PROGRESS: {(batches_done/total_batches)*100:.1f}% | BATCH: {batches_done}/{total_batches} | VELOCITY: {velocity:.1f} u/s")
            print(f"⏱️  ELAPSED: {str(timedelta(seconds=int(elapsed)))} | ⏳ ETA: {str(timedelta(seconds=int(eta)))} | 🛡️ QA: {total_passed} OK / {total_failed} FAIL")
            print("="*115)

    tree.write(OUTPUT_FILE, encoding='utf-8', xml_declaration=True)
    print(f"\n🏆 MISSION COMPLETE! Diagnostics logged in: {QA_LOG_FILE}")

if __name__ == "__main__":
    start_velocity_engine()

# /* === END OF FILE === */