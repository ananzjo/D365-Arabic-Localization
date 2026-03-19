#/* === START OF FILE === */
# File: BC-Translator-Pro.py
# Version: v1.2.0
# Function: Advanced XLF Translator with Resume Logic and Rate Limiting
# Purpose: Handling large D365 BC files (Base/System App) using Gemini 2.0 Flash

import os
import time
import xml.etree.ElementTree as ET
from google import genai
from google.genai import types

# === CONFIGURATION ===
API_KEY = "AIzaSyBzz4D726YDE6NqITDjs8ATo9-p-kKAgzo"
API_KEY = os.getenv("GOOGLE_API_KEY")
if not API_KEY:
    raise ValueError("Please set the GOOGLE_API_KEY environment variable.")
client = genai.Client(api_key=API_KEY)

# Change these for each file you process
SOURCE_FILE = "Base Application.cs-CZ.xlf"
OUTPUT_FILE = "Base Application.ar-JO.xlf"
SOURCE_FILE = "System Application.cs-CZ.xlf"
OUTPUT_FILE = "System Application.ar-JO.xlf"

# XLIFF Namespace setup
ET.register_namespace('', "urn:oasis:names:tc:xliff:document:1.2")
ns = {'xliff': "urn:oasis:names:tc:xliff:document:1.2"}

def translate_batch(texts):
    """Sends strings to Gemini with instructions to ignore placeholders."""
    system_msg = (
        "You are an expert ERP translator for Dynamics 365 Business Central. "
        "Translate the following list into professional Arabic (Jordan/ar-JO). "
        "Context: Corrugated packaging factory and industrial accounting. "
        "CRITICAL: Keep placeholders like %1, %2, %3 exactly as they are. "
        "Return ONLY the translations, one per line."
    )
    
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=texts,
            config=types.GenerateContentConfig(system_instruction=system_msg)
        )
        return [line.strip() for line in response.text.strip().split('\n')]
    except Exception as e:
        print(f"\n[!] API Error: {e}")
        return None

def is_arabic(text):
    """Checks if the text already contains Arabic characters."""
    if not text: return False
    return any('\u0600' <= c <= '\u06FF' for c in text)

def run_translation():
    # If we already have a partial output file, use it to resume. 
    # Otherwise, start from the source file.
    file_to_load = OUTPUT_FILE if os.path.exists(OUTPUT_FILE) else SOURCE_FILE
    
    print(f"Loading {file_to_load}...")
    tree = ET.parse(file_to_load)
    root = tree.getroot()
    
    # Set target language
    for file_tag in root.findall('xliff:file', ns):
        file_tag.set('target-language', 'ar-JO')

    all_units = root.findall('.//xliff:trans-unit', ns)
    
    # Filter: Only process units that don't have Arabic in the target yet
    todo_units = []
    for unit in all_units:
        target = unit.find('xliff:target', ns)
        if target is None or not is_arabic(target.text):
            todo_units.append(unit)

    total_todo = len(todo_units)
    print(f"Total units in file: {len(all_units)}")
    print(f"Units remaining to translate: {total_todo}")

    if total_todo == 0:
        print("Everything is already translated!")
        return

    batch_size = 30
    for i in range(0, total_todo, batch_size):
        batch = todo_units[i : i + batch_size]
        sources = [u.find('xliff:source', ns).text for u in batch]
        
        print(f"Translating batch {i//batch_size + 1}... ", end="", flush=True)
        
        results = translate_batch(sources)
        
        if results:
            for j, unit in enumerate(batch):
                target = unit.find('xliff:target', ns)
                if target is None:
                    target = ET.SubElement(unit, '{urn:oasis:names:tc:xliff:document:1.2}target')
                
                # Update target text and state
                target.text = results[j] if j < len(results) else sources[j]
                target.set('state', 'translated')
            
            # Save progress after every successful batch
            tree.write(OUTPUT_FILE, encoding="utf-8", xml_declaration=True)
            print(f"Done. ({i + len(batch)}/{total_todo})")
            
            # Wait to avoid Rate Limit (429)
            time.sleep(12) 
        else:
            print("Skipping batch due to error. Retrying in 30 seconds...")
            time.sleep(30)

    print(f"\nProcessing Complete! Final file saved as: {OUTPUT_FILE}")

if __name__ == "__main__":
    run_translation()
#/* === END OF FILE === */