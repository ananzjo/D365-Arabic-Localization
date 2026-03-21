#!/usr/bin/env python3
import glob
import os
import re
import time
import xml.etree.ElementTree as ET

try:
    from deep_translator import GoogleTranslator
except ImportError:
    print("Please install deep-translator to run this script: pip install deep-translator")
    exit(1)

# Mapping dictionary for key terms
TERMS_MAPPING = {
    'post': 'ترحيل',
    'apply': 'تسوية',
    'order': 'أمر',
    'corrugated': 'معرج',
    'journal': 'دفتر يومية',     # Also يومية
    'lc': 'اعتماد بنكي',
    'invoice lines': 'تفاصيل الفاتورة',
    'purchase lines': 'تفاصيل المشتريات',
    'sales lines': 'تفاصيل المبيعات',
    'purchase indent': 'احتياجات الشراء',
    'indent': 'طلب توريد داخلي',
    'scrap': 'تالف',
    'pallet': 'طبلية',
    'pallets': 'طبالي',
    'item issue journal': 'يومية صرف المواد',
    'issue': 'صرف',
    'de-palletization': 'تفكيك',
    'issue log': 'سجل الصرف',
    'die': 'قالب قص',
    'die-cutting': 'عملية قص وتشكيل',
    'die-cut box': 'صندوق داي-كت',
    'rotary die': 'قالب دوار',
    'flatbed die': 'قالب مسطح',
    'copilot': 'كوبايلوت',
    'corrugated board': 'ورق كرتون معرج',
    'corrugator': 'ماكينة التعريج',
    'corrugating medium': 'ورق التعريج',
    'single facer': 'رأس التعريج المفرد',
    'flute': 'تعريجة',
    'fluting': 'تعريجة',
    'liner': 'ورق تبطين',
    'rsc': 'صندوق عادي (RSC)',
    'regular slotted container': 'صندوق عادي (RSC)',
    'creasing': 'تحزيز',
    'scoring': 'تحزيز',
    'slitter scorer': 'جهاز القص والتحزيز',
    'score line': 'خط التحزيز',
    'slotting': 'فتحات الربط (سلوت)',
    'waste': 'هالك',
    'trim': 'قصاصات',
    'starch': 'نشأ',
    'glue': 'غراء',
    'bursting strength': 'قوة الانفجار (Mullen)',
    'ect': 'اختبار ضغط الحواف',
    'edge crush test': 'اختبار ضغط الحواف',
    'flexo printing': 'طباعة فليكسو',
    'dispatch': 'شحن',
    'machine wise daily prod. status': 'حالة الإنتاج اليومي حسب الماكينة',
    'items': 'مواد',
    'item': 'مادة',
    'double stacker': 'دبل ستاكر',
    'capacity': 'الطاقة الانتاجية'
}

from functools import lru_cache

@lru_cache(maxsize=200000)
def _do_translate(text):
    try:
        from deep_translator import GoogleTranslator
        translator = GoogleTranslator(source='en', target='ar')
        res = translator.translate(text)
        if res is None:
            return text
        return res
    except Exception:
        return text

def translate_and_map(text, dev_note, translator):
    if not text or not text.strip():
        return text

    # Handle placeholders like %1, %2, \n, \t
    # Pattern to match %number or escape sequences
    pattern = r'(%[0-9]+|\\[nt])'
    parts = re.split(pattern, text)
    
    translated_parts = []
    original_lower = text.lower()
    
    for p in parts:
        if re.match(pattern, p):
            translated_parts.append(p)
        else:
            if not p.strip():
                translated_parts.append(p)
                continue
            
            p_lower_strip = p.strip().lower()
            if p_lower_strip in TERMS_MAPPING:
                translated = TERMS_MAPPING[p_lower_strip]
            elif p_lower_strip == 'journals': translated = 'يوميات'
            elif p_lower_strip == 'indents': translated = TERMS_MAPPING['indent']
            elif p_lower_strip == 'depalletization': translated = TERMS_MAPPING['de-palletization']
            elif p_lower_strip == 'die cut box': translated = TERMS_MAPPING['die-cut box']
            elif p_lower_strip == 'die cutting': translated = TERMS_MAPPING['die-cutting']
            elif p_lower_strip == 'dies': translated = TERMS_MAPPING['die']
            else:
                # Use LRU cached translation engine
                translated = _do_translate(p)
            
            # Context-Aware Key Term Mapping
            if 'process' in original_lower:
                dev_note_lower = dev_note.lower() if dev_note else ''
                # Default translation usually yields 'عملية', we refine based on Dev Note Context
                if 'manufacturing' in dev_note_lower or 'production' in dev_note_lower:
                    translated = translated.replace('عملية', 'عملية تشغيل/إنتاج')
                else:
                    translated = translated.replace('عملية', 'معالجة')
                    
            if 'post' in original_lower:
                translated = translated.replace('نشر', TERMS_MAPPING['post'])
            if 'apply' in original_lower:
                translated = translated.replace('تطبيق', TERMS_MAPPING['apply'])
            if 'corrugated' in original_lower:
                translated = translated.replace('مموج', TERMS_MAPPING['corrugated']).replace('مضلع', TERMS_MAPPING['corrugated'])
            if 'corrugator' in original_lower:
                translated = translated.replace('تضليع', 'تعريج')
            if 'order' in original_lower:
                translated = translated.replace('طلب', TERMS_MAPPING['order'])
            
            # Post-processing embedded items (replacing Google's default translation guesses)
            if 'journal' in original_lower:
                translated = translated.replace('مجلة', 'يومية').replace('صحيفة', 'يومية')
            if ' lc ' in original_lower:
                translated = translated.replace(' ال سي ', ' اعتماد بنكي ').replace('الاعتماد المستندي', 'اعتماد بنكي')
            if 'invoice lines' in original_lower:
                translated = translated.replace('خطوط الفاتورة', TERMS_MAPPING['invoice lines']).replace('أسطر الفاتورة', TERMS_MAPPING['invoice lines']).replace('سطور الفاتورة', TERMS_MAPPING['invoice lines'])
            if 'purchase lines' in original_lower:
                translated = translated.replace('خطوط الشراء', TERMS_MAPPING['purchase lines']).replace('أسطر الشراء', TERMS_MAPPING['purchase lines']).replace('سطور الشراء', TERMS_MAPPING['purchase lines'])
            if 'sales lines' in original_lower:
                translated = translated.replace('خطوط المبيعات', TERMS_MAPPING['sales lines']).replace('أسطر المبيعات', TERMS_MAPPING['sales lines']).replace('سطور المبيعات', TERMS_MAPPING['sales lines'])
            if 'purchase indent' in original_lower:
                translated = translated.replace('طلب شراء', TERMS_MAPPING['purchase indent']).replace('مسافة بادئة للشراء', TERMS_MAPPING['purchase indent'])
            elif 'indent' in original_lower:
                translated = translated.replace('مسافة بادئة', TERMS_MAPPING['indent']).replace('يضع مسافة بادئة', TERMS_MAPPING['indent']).replace('المسافة البادئة', TERMS_MAPPING['indent'])
            if 'scrap' in original_lower:
                translated = translated.replace('خردة', TERMS_MAPPING['scrap']).replace('سكراب', TERMS_MAPPING['scrap'])
            if 'item issue journal' in original_lower:
                translated = translated.replace('يومية إصدار الصنف', TERMS_MAPPING['item issue journal']).replace('دفتر يومية إصدار الصنف', TERMS_MAPPING['item issue journal'])
            if 'issue log' in original_lower:
                translated = translated.replace('سجل الإصدار', TERMS_MAPPING['issue log']).replace('سجل المشكلات', TERMS_MAPPING['issue log'])
            elif 'issue' in original_lower:
                translated = translated.replace('إصدار', TERMS_MAPPING['issue'])
            if 'pallets' in original_lower:
                translated = translated.replace('منصات نقالة', TERMS_MAPPING['pallets']).replace('المنصات', TERMS_MAPPING['pallets'])
            elif 'pallet' in original_lower:
                translated = translated.replace('منصة نقالة', TERMS_MAPPING['pallet']).replace('البليت', TERMS_MAPPING['pallet'])
            if 'de-palletization' in original_lower or 'depalletization' in original_lower:
                translated = translated.replace('إزالة البليت', TERMS_MAPPING['de-palletization']).replace('إزالة المنصات', TERMS_MAPPING['de-palletization'])
            
            # Die terminology logic
            if 'die-cut box' in original_lower or 'die cut box' in original_lower:
                translated = translated.replace('صندوق مقطوع', TERMS_MAPPING['die-cut box']).replace('صندوق يموت', TERMS_MAPPING['die-cut box']).replace('صندوق قوالب', TERMS_MAPPING['die-cut box'])
            if 'die-cutting' in original_lower or 'die cutting' in original_lower:
                translated = translated.replace('قطع القوالب', TERMS_MAPPING['die-cutting']).replace('يموت قطع', TERMS_MAPPING['die-cutting']).replace('قطع يموت', TERMS_MAPPING['die-cutting'])
            if 'rotary die' in original_lower:
                translated = translated.replace('يموت الدوارة', TERMS_MAPPING['rotary die']).replace('يموت الدوار', TERMS_MAPPING['rotary die']).replace('قوالب دوارة', TERMS_MAPPING['rotary die'])
            if 'flatbed die' in original_lower:
                translated = translated.replace('يموت المسطحة', TERMS_MAPPING['flatbed die']).replace('الموت المسطح', TERMS_MAPPING['flatbed die']).replace('قوالب مسطحة', TERMS_MAPPING['flatbed die'])
            
            if 'die-cut' not in original_lower and 'die cut' not in original_lower and 'rotary die' not in original_lower and 'flatbed die' not in original_lower:
                if 'die' in original_lower or 'dies' in original_lower:
                    translated = translated.replace('يموت', TERMS_MAPPING['die']).replace('الموت', TERMS_MAPPING['die'])
                    
            if 'copilot' in original_lower: translated = translated.replace('مساعد طيار', TERMS_MAPPING['copilot'])
            if 'corrugated board' in original_lower: translated = translated.replace('لوح مموج', TERMS_MAPPING['corrugated board']).replace('الورق المموج', TERMS_MAPPING['corrugated board'])
            if 'corrugator' in original_lower: translated = translated.replace('المموج', TERMS_MAPPING['corrugator']).replace('مصنع الكرتون', TERMS_MAPPING['corrugator'])
            if 'corrugating medium' in original_lower: translated = translated.replace('متوسط التعريج', TERMS_MAPPING['corrugating medium']).replace('وسيلة التمويج', TERMS_MAPPING['corrugating medium'])
            if 'single facer' in original_lower: translated = translated.replace('واجهة واحدة', TERMS_MAPPING['single facer']).replace('وجه واحد', TERMS_MAPPING['single facer'])
            if 'fluting' in original_lower or 'flute' in original_lower: translated = translated.replace('مزمار', 'تعريجة').replace('عزف بالناي', 'تعريجة').replace('تمويج', 'تعريجة').replace('الفلوت', 'تعريجة')
            if 'liner' in original_lower: translated = translated.replace('بطانة', TERMS_MAPPING['liner'])
            if 'rsc' in original_lower or 'regular slotted container' in original_lower: translated = translated.replace('رسك', TERMS_MAPPING['rsc']).replace('آر إس سي', TERMS_MAPPING['rsc'])
            if 'creasing' in original_lower: translated = translated.replace('التجعيد', TERMS_MAPPING['creasing']).replace('تجعيد', TERMS_MAPPING['creasing'])
            
            if 'slitter scorer' in original_lower:
                translated = translated.replace('محزز مشقق', TERMS_MAPPING['slitter scorer']).replace('هداف تقطيع', TERMS_MAPPING['slitter scorer']).replace('حرز ومقطع', TERMS_MAPPING['slitter scorer'])
            if 'score line' in original_lower:
                translated = translated.replace('خط النقاط', TERMS_MAPPING['score line']).replace('خط التهديف', TERMS_MAPPING['score line'])
            if 'scoring' in original_lower: 
                translated = translated.replace('تسجيل الأهداف', TERMS_MAPPING['scoring']).replace('تهديف', TERMS_MAPPING['scoring']).replace('التهديف', TERMS_MAPPING['scoring']).replace('تسجيل', TERMS_MAPPING['scoring']).replace('إحراز', TERMS_MAPPING['scoring'])
                
            if 'slotting' in original_lower: translated = translated.replace('الشق', TERMS_MAPPING['slotting']).replace('إحداث فجوة', TERMS_MAPPING['slotting'])
            if 'waste' in original_lower: translated = translated.replace('نفايات', TERMS_MAPPING['waste'])
            if 'trim' in original_lower: translated = translated.replace('تقليم', TERMS_MAPPING['trim']).replace('تشذيب', TERMS_MAPPING['trim'])
            if 'starch' in original_lower: translated = translated.replace('نشاء', TERMS_MAPPING['starch']).replace('النشا', TERMS_MAPPING['starch'])
            if 'glue' in original_lower: translated = translated.replace('صمغ', TERMS_MAPPING['glue'])
            if 'bursting strength' in original_lower: translated = translated.replace('قوة الانفجار', TERMS_MAPPING['bursting strength'])
            if 'edge crush test' in original_lower or 'ect' in original_lower: translated = translated.replace('اختبار سحق الحافة', TERMS_MAPPING['edge crush test']).replace('العلاج بالصدمات الكهربائية', TERMS_MAPPING['edge crush test'])
            if 'dispatch' in original_lower: translated = translated.replace('إرسال', TERMS_MAPPING['dispatch']).replace('إيفاد', TERMS_MAPPING['dispatch']).replace('توزيع', TERMS_MAPPING['dispatch'])
            if 'machine wise daily prod. status' in original_lower: translated = translated.replace('حالة الإنتاج اليومي الحكيم للآلة', TERMS_MAPPING['machine wise daily prod. status']).replace('حالة الإنتاج اليومية الحكيمة للماكينة', TERMS_MAPPING['machine wise daily prod. status']).replace('الماكينة الحكيمة حالة الإنتاج اليومية', TERMS_MAPPING['machine wise daily prod. status'])
            if 'items' in original_lower: 
                translated = translated.replace('أغراض', TERMS_MAPPING['items']).replace('الأغراض', TERMS_MAPPING['items']).replace('عناصر', TERMS_MAPPING['items']).replace('أصناف', TERMS_MAPPING['items'])
            elif 'item' in original_lower: 
                translated = translated.replace('غرض', TERMS_MAPPING['item']).replace('الغرض', TERMS_MAPPING['item']).replace('عنصر', TERMS_MAPPING['item']).replace('صنف', TERMS_MAPPING['item']).replace('صنفا', TERMS_MAPPING['item'])
            
            if 'double stacker' in original_lower: 
                translated = translated.replace('مكدس مزدوج', TERMS_MAPPING['double stacker']).replace('مكدس مضاعف', TERMS_MAPPING['double stacker'])
            if 'capacity' in original_lower:
                translated = translated.replace('سعة', TERMS_MAPPING['capacity']).replace('السعة', TERMS_MAPPING['capacity']).replace('قدرة', TERMS_MAPPING['capacity']).replace('القدرة', TERMS_MAPPING['capacity'])

            translated_parts.append(translated)
            
    return "".join(translated_parts)


def is_arabic_translated(target_text, source_text):
    if not target_text:
        return False
    # If it's already exactly the same as source and contains no letters (like %1, or 0.00), assume completed
    if target_text == source_text and not re.search(r'[a-zA-Z]', source_text):
        return True
    # Check for Arabic characters
    if re.search(r'[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF]', target_text):
        return True
    return False

def process_xlf_file(input_file, output_file):
    print(f"\nProcessing {input_file} -> {output_file}")
    
    # Register XLIFF namespaces
    ET.register_namespace('', 'urn:oasis:names:tc:xliff:document:1.2')
    
    file_to_parse = output_file if os.path.exists(output_file) else input_file
    print(f"Loading {file_to_parse} into memory...")
    tree = ET.parse(file_to_parse)
    root = tree.getroot()
    ns = {'xliff': 'urn:oasis:names:tc:xliff:document:1.2'}
    
    # Update target-language to ar-JO
    files = root.findall('xliff:file', ns)
    for f in files:
        f.set('target-language', 'ar-JO')
    
    # Extract total units for batch progress tracking
    total_units = 0
    for f in files:
        for body in f.findall('xliff:body', ns):
            for group in body.findall('xliff:group', ns):
                total_units += len(group.findall('xliff:trans-unit', ns))
                
    print(f"Total units: {total_units}")
    
    translator = None # Placeholder, uses instance in cached loop
    processed = 0
    newly_translated = 0
    
    for f in files:
        for body in f.findall('xliff:body', ns):
            for group in body.findall('xliff:group', ns):
                for unit in group.findall('xliff:trans-unit', ns):
                    source = unit.find('xliff:source', ns)
                    target = unit.find('xliff:target', ns)
                    
                    dev_note = ""
                    for note in unit.findall('xliff:note', ns):
                        if note.attrib.get('from') == 'Developer':
                            dev_note = note.text or ""
                            break
                            
                    if source is not None and source.text:
                        # Append <target> if it doesn't exist
                        if target is None:
                            target = ET.SubElement(unit, '{urn:oasis:names:tc:xliff:document:1.2}target')
                            
                        # Skip if already translated properly to Arabic
                        if target.attrib.get('state') == 'translated' and is_arabic_translated(target.text, source.text):
                            processed += 1
                            continue
                        
                        target.set('state', 'translated')
                        
                        # Process translation while maintaining placeholders intact
                        target.text = translate_and_map(source.text, dev_note, translator)
                        newly_translated += 1
                        
                    processed += 1
                    if newly_translated > 0 and newly_translated % 50 == 0:
                        print(f"[{processed}/{total_units}] translated... Saving progress.")
                        # Incremental save
                        xml_str = ET.tostring(root, encoding='utf-8', xml_declaration=True)
                        with open(output_file, 'wb') as out_f:
                            out_f.write(b'\xef\xbb\xbf')
                            out_f.write(xml_str)
                        time.sleep(2) # Throttle to prevent IP block
                        
    # Final Save
    print(f"Saving final output to {output_file}...")
    xml_str = ET.tostring(root, encoding='utf-8', xml_declaration=True)
    
    # Explicit BOM for UTF-8
    with open(output_file, 'wb') as out_f:
        out_f.write(b'\xef\xbb\xbf')
        out_f.write(xml_str)
        
    print(f"Completed {output_file}")


def main():
    print("Business Central XLF Professional Translator Initialized.")
    xlf_files = glob.glob("*.xlf")
    
    for xlf in xlf_files:
        # Skip files already processed or Arabic localization files
        if 'ar-JO' in xlf:
            continue
            
        # Ensure Output Name follows specification: [OriginalName].ar-JO.xlf
        base_name = xlf
        if '.cs-CZ' in xlf:
            out_name = xlf.replace('.cs-CZ', '.ar-JO')
        elif '.en-US' in xlf:
            out_name = xlf.replace('.en-US', '.ar-JO')
        else:
            out_name = xlf.replace('.xlf', '.ar-JO.xlf')
            
        # Prevent overwriting original file
        if os.path.abspath(xlf) == os.path.abspath(out_name):
            print(f"Skipping {xlf}: Target filename matches source filename.")
            continue
            
        try:
            process_xlf_file(xlf, out_name)
        except Exception as e:
            print(f"Failed to process {xlf}. Error: {e}")

if __name__ == '__main__':
    main()
