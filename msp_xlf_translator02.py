# /* === START OF FILE === */
# File Name: msp_xlf_translator_v1.8.9.py
# Version: v1.8.9
# Function: Advanced Localization with Technical Corrugation Dictionary.
# /* ======================================================================== */

import os, json, time, re, sys, io, random
import pandas as pd
from lxml import etree
from tqdm import tqdm
from googletrans import Translator

# إعدادات العرض العربي الاحترافي
try:
    from arabic_reshaper import reshape
    from bidi.algorithm import get_display
    def fix_ar(t): return get_display(reshape(t))
except:
    def fix_ar(t): return t

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# --- إعدادات MSP الثابتة والمحمية ---
EXCEL_DICTIONARY = "Dictionary.xlsx"
TARGET_FILES = ["Corrugated Samadhan.cs-CZ.xlf"]
CHECKPOINT_PATH = "msp_turbo_checkpoint02.json"
PROTECTED_BRANDS = ["VAT", "FA", "PO", "SQL", "ERP", "SAMADHAN", "Copilot", "Power BI", "Microsoft", "Azure","D365", "Dynamics 365"]

# القاموس الفني الموحد لـ MSP (تم دمج قائمتك الجديدة هنا)
MSP_FIXED_LOGIC = {
    # القواعد الأساسية
    "Journal": "دفتر يومية", "Journals": "دفاتر يومية", "Prod.": "إنتاج", "Production": "إنتاج",
    "Entry": "قيد", "Entries": "قيود", "Item": "صنف", "Items": "أصناف", "Scrap": "تالف",
    "Posting": "ترحيل", "Post": "ترحيل", "Line": "بند", "Lines": "بنود", "Default": "افتراضي",
    "BOM": "قائمة مواد", "Fixed Assets": "الأصول الثابتة", "Fixed Asset": "أصل ثابت",
    "Purchase Order": "طلب شراء", "Purchase Orders": "طلبات شراء", "Bin": "رف", "Bins": "أرفف",
    "A/C": "حساب", "A/R": "ذ.م", "A/P": "ذ.د",

    # القائمة الفنية الجديدة (Technical Corrugation Terms)
    "Length Wise Mfg. Joint": "وصلة التصنيع حسب الطول",
    "Length X Height Wise Partition Size": "مقاس الفاصل حسب الطول × الارتفاع",
    "Length x Height wise no. of \"Partition\" required": "عدد الفواصل المطلوبة حسب الطول × الارتفاع",
    "Width Wise Mfg. Joint": "وصلة التصنيع حسب العرض",
    "Width x Height Wise Partition Size": "مقاس الفاصل حسب العرض × الارتفاع",
    "Width x Height wise no. of \"Partition\" required": "عدد الفواصل المطلوبة حسب العرض × الارتفاع",
    "Work Center Wise": "حسب مركز العمل",
    "Corr Schedule Wise": "حسب جدول التعريج",
    "Converting Schedule Wise": "حسب جدول التحويل",
    "DB Facer Wise Roll Details": "تفاصيل الرولات حسب ماكينة الوجه الثنائي",
    "Facer Wise Roll Details": "تفاصيل الرولات حسب ماكينة الوجه (Facer)",
    "Total Ink Qty. Prod. Ord. Wise": "إجمالي كمية الحبر حسب أمر الإنتاج",
    "Job wise Deviation Buffer": "هامش الانحراف حسب الطلبية",
    "Mach Wise Qty CheckforQC": "فحص الكمية حسب الماكينة لمراقبة الجودة",
    "Item Wise": "حسب الصنف",
    "Paper Type Wise": "حسب نوع الورق",
    "Paper Type and Paper GSM Wise": "حسب نوع الورق ووزن الورق (GSM)",
    "Reel Wise": "حسب البكرة",
    "Req - Vendor Wise Qty.": "الكمية المطلوبة حسب المورد",
    "Seq. Wise Paper Req": "احتياجات الورق حسب التسلسل",
    "Converting Machine Wise": "حسب ماكينة التحويل",
    "QA Wise": "حسب تأكيد الجودة",
    "History Wise": "حسب السجل التاريخي",
    "Report Wise": "حسب التقارير",
    "Load Wise": "حسب التحميل",
    "Create Material Requisition RPO Wise": "إنشاء طلب مواد حسب أمر الإنتاج (RPO)",
    "Schedule Wise Job card Report": "تقرير بطاقة العمل حسب الجدول",
    "Schedule Wise Job Wise Report": "تقرير الطلبيات حسب الجدول",
    "Schedule Wise Material Requirement": "احتياجات المواد حسب الجدول",
    "Job Card Corrugation Schedule wise": "بطاقة العمل حسب جدول التعريج",
    "Print Job Card Printing & Finishing Schedule Wise": "بطاقة عمل الطباعة حسب جدول الطباعة والتشطيب",
    "Print Job Card Corrugation Schedule Wise": "بطاقة عمل الطباعة حسب جدول التعريج",
    "Print Schedule Wise Print Planning": "تخطيط الطباعة حسب جدول الطباعة",
    "Customer Wise Flute": "نوع التعريج (Flute) حسب العميل",
    "Customer Wise Paper Price": "سعر الورق حسب العميل",
    "Customer Wise Process": "العملية التصنيعية حسب العميل",
    "Customer Wise Scrap": "الهالك (الخردة) حسب العميل",
    "Day Wise Trip Details": "تفاصيل الرحلات حسب اليوم",
    "Deckle Wise Item": "الصنف حسب عرض الورق (Deckle)",
    "Deckle Wise Item Details": "تفاصيل الأصناف حسب عرض الورق (Deckle)",
    "Deckle Wise Suggestion": "المقترحات حسب عرض الورق (Deckle)",
    "Deckle Wise Items": "الأصناف حسب عرض الورق (Deckle)",
    "Production Order Wise Status": "حالة أمر الإنتاج حسب الطلب",
    "Production Wise Status": "حالة الإنتاج حسب الإنتاج",
    "Stock Report Reel Wise": "تقرير المخزون حسب البكرة",
    "Stock Report Width Wise": "تقرير المخزون حسب العرض",
    "Customer Wise Item Wise Sale": "المبيعات حسب العميل وحسب الصنف",
    "Customer Wise Weekly Sale": "المبيعات الأسبوعية حسب العميل",
    "Month Wise Sales": "المبيعات حسب الشهر",
    "Schedule Wise Paper Consumption List": "قائمة استهلاك الورق حسب الجدول",
    "Cust. Location Wise Truck": "الشاحنة حسب موقع العميل",
    "Customer Wise Truck Load": "حمولة الشاحنة حسب العميل",
    "Daily Avg. Cost Trip Wise": "متوسط التكلفة اليومية حسب الرحلة",
    "Location Wise Inventory": "المخزون حسب الموقع/المستودع",
    "Customer Segment Wise Cons.": "الاستهلاك حسب فئة العملاء",
    "Job Wise Deviation": "الانحراف حسب الطلبية",
    "Job Wise Deviation New": "الانحراف الجديد حسب الطلبية",
    "Jobwise Ink Cons. Exp. Vs Actual": "استهلاك الحبر (المتوقع ضد الفعلي) حسب الطلبية",
    "Jobwise Paper Cons. Expected Vs Actual": "استهلاك الورق (المتوقع ضد الفعلي) حسب الطلبية",
    "Machine Wise Daily Prod. Status": "حالة الإنتاج اليومية حسب الماكينة",
    "Machine Wise Production": "الإنتاج حسب الماكينة",
    "Machine Wise Shift Wise": "حسب الماكينة وحسب الوردية",
    "Monthly Converting Operator Wise": "إنتاج مشغل التحويل الشهري حسب المشغل",
    "Rate/Kg For Paper Job Wise": "سعر الكيلو للورق حسب الطلبية",
    "RPO Wise Consumption": "الاستهلاك حسب أمر الإنتاج (RPO)",
    "Machine Wise Prod. Status": "حالة الإنتاج حسب الماكينة",
    "Total Ink Qty. Prod. Ord. Wise Field": "حقل إجمالي كمية الحبر حسب أمر الإنتاج",
    "Item Work Center wise Spec": "مواصفات الصنف حسب مركز العمل",
    "Mach Wise Qty CheckMaster": "رئيسي فحص الكمية حسب الماكينة",
    "Machine Wise Prod. Lines": "خطوط الإنتاج حسب الماكينة",
    "Deckle Wise Inventory": "المخزون حسب عرض الورق (Deckle)",
    "Item Wise Purch. Cost History": "سجل تكلفة الشراء حسب الصنف",
    "Paper Wise Pending Order": "الطلبيات المعلقة حسب نوع الورق",
    "Vendor Wise Analysis": "تحليل الموردين حسب المورد",
    "Cust. Wise Sample": "عينة حسب العميل",
    "Sales Month Wise": "مبيعات حسب الشهر",
    "Sales Person Wise Annual Prospecting Plan": "خطة البحث السنوية حسب موظف المبيعات",
    "Cost Sheet Item Categ. Wise": "كشف التكلفة حسب فئة الصنف",
    "FSC Customer Wise Detail": "تفاصيل شهادة (FSC) حسب العميل",
    "Job Wise Deviation Report": "تقرير الانحراف حسب الطلبية",
    "Monthly GRN and Consump. BF Wise": "الاستلام المخزني والاستهلاك الشهري حسب قوة الورق (BF)",
    "Paper Contribution BF Wise": "مساهمة الورق حسب قوة الورق (BF)",
    "Machine Wise Shift Wise Report": "تقرير الورديات حسب الماكينة",
    "Rate/Kg for Paper Jobwise": "سعر الكيلو للورق حسب الطلبية",
    "Paper wise Pendng Order": "الطلبيات المعلقة حسب نوع الورق",
    "Container wise load details": "تفاصيل التحميل حسب الحاوية",
    "Cust Location Wise Truck": "الشاحنة حسب موقع العميل",
    "Cust Segment wise consumption": "الاستهلاك حسب فئة العملاء",
    "Cust Wise Sample": "عينة حسب العميل",
    "Customer wise Sales Summary": "ملخص المبيعات حسب العميل",
    "Customer wise Truck load": "حمولة الشاحنة حسب العميل",
    "Total Export containerwise": "إجمالي الصادرات حسب الحاوية",
    "Vendor wise Analysis Report": "تقرير تحليل الموردين حسب المورد",
    "PlyFlute Wise Setup": "إعدادات الطبقات والتعريج حسب النوع",
    "Position Wise stock": "المخزون حسب الموضع",
    "Item Reel Wise Reservation": "حجز الأصناف حسب البكرة",
    "Item Wise Reservation": "حجز الأصناف حسب الصنف",
    "Item Wise Summary": "ملخص الأصناف حسب الصنف",
    "Prod Order wise status": "حالة أمر الإنتاج حسب الطلب",
    "Job Seq. Wise Paper Req.": "احتياجات الورق حسب تسلسل الطلبية",
    "Schedule Seq. Wise Paper Wise Req New": "احتياجات الورق حسب تسلسل الجدول (جديد)",
    "Schedule Wise Paper Wise Req": "احتياجات الورق حسب الجدول",
    "Machine Wise Qty Check Master": "رئيسي فحص الكمية حسب الماكينة",
    "Repeat Job Creat Lot Wise": "تكرار إنشاء الطلبية حسب التشغيلة (Lot)",
    "RPO Wise Stock Fact Box": "صندوق معلومات المخزون حسب أمر الإنتاج (RPO)",
    "Customer Wise Annual Visit Plan": "خطة الزيارات السنوية حسب العميل",
    "Print JobWise Deviation": "طباعة الانحراف حسب الطلبية",
    "Check Inventory Batch Wise": "فحص المخزون حسب الدفعة (Batch)",
    "Cont wise load details": "تفاصيل التحميل حسب الحاوية",
    "Cust Segment wise consump": "الاستهلاك حسب فئة العملاء",
    "Cust wise Sales Summary": "ملخص المبيعات حسب العميل",
    "Deckle Wise Invent Report": "تقرير المخزون حسب عرض الورق (Deckle)",
    "Item Wise Avg. Cost": "متوسط التكلفة حسب الصنف",
    "Item Wise Inc Decrease": "الزيادة والنقصان حسب الصنف",
    "Item Wise Purch. Cost His": "سجل تكلفة الشراء حسب الصنف",
    "Job Wise Deviation N": "الانحراف حسب الطلبية (N)",
    "Job Wise Paper Requirement": "احتياجات الورق حسب الطلبية",
    "Jobwise Ink Exp vs Actual": "استهلاك الحبر المتوقع ضد الفعلي حسب الطلبية",
    "Jobwise Paper Cons. Det": "تفاصيل استهلاك الورق حسب الطلبية",
    "Machine Wise Daily Prod.": "الإنتاج اليومي حسب الماكينة",
    "Machine Wise Prod Report": "تقرير الإنتاج حسب الماكينة",
    "Machine Wise ShiftWise Rep": "تقرير الورديات حسب الماكينة",
    "Monthly Converting Operator Wise With Cost": "إنتاج مشغل التحويل الشهري مع التكلفة حسب المشغل",
    "Show Item Wise": "عرض حسب الصنف",
    "Overall Profit Cust Wise": "الأرباح الإجمالية حسب العميل",
    "Prod. Wise Monthly Sales": "المبيعات الشهرية حسب الإنتاج",
    "RPO WISE CONSUMPTION DETAILS": "تفاصيل الاستهلاك حسب أمر الإنتاج (RPO)",
    "RPO Wise Consumption1": "استهلاك أمر الإنتاج 1 (RPO)",
    "Sales Person WiseInter": "موظف المبيعات حسب التفاعل الداخلي",
    "Sched Wise CorrScd Qty Tem": "كمية جدول التعريج المؤقتة حسب الجدول",
    "Seq. Wise Paper Req.": "احتياجات الورق حسب التسلسل",
    "Item Wise Increase Decrease": "الزيادة والنقصان حسب الصنف",
    "Prod. Wise Monthly Analysis": "التحليل الشهري حسب الإنتاج",
    "Open Related Prod. Wise Cost": "تكلفة الإنتاج المرتبطة المفتوحة حسب الإنتاج",
    "Ply Flute Wise Setup": "إعدادات الطبقات والتعريج حسب النوع",
    "JobWise Deviation": "الانحراف حسب الطلبية",
    "JobWise Deviation New": "الانحراف الجديد حسب الطلبية",
    "RPO Wise Consumption Details": "تفاصيل الاستهلاك حسب أمر الإنتاج (RPO)",
    "Order Wise, Open": "حسب الطلب، مفتوح",
    "Actual Consumed (LayerWise)": "الاستهلاك الفعلي حسب الطبقة",
    "Total PO value Itemwise": "إجمالي قيمة أمر الشراء حسب الصنف",
    "Job Wise Inventory": "المخزون حسب الطلبية",
    "Machine Wise Qty Check": "فحص الكميات حسب الماكينة","PDI": "واجهة تصميم المنتج","Pallet": "طبلية","Palletization": "توزيع الأحمال على الطبلية","Pallets":"طبالي"
    }

translator = Translator()

def smart_translate(text, msp_dict):
    if not text: return text, "[EMPTY]"
    clean_text = text.strip(".,:;() ")
    
    # 1. فحص القواعد الفنية (Corrugation Dictionary) - الأولوية القصوى
    if text in MSP_FIXED_LOGIC:
        return MSP_FIXED_LOGIC[text], "[RULE]"
    elif clean_text in MSP_FIXED_LOGIC:
        return MSP_FIXED_LOGIC[clean_text], "[RULE]"

    # 2. فحص القاموس الخارجي (Excel)
    if text in msp_dict:
        return msp_dict[text], "[DICT]"
    
    # 3. الترجمة الآلية
    try:
        time.sleep(random.uniform(0.4, 0.8))
        res = translator.translate(text, src='en', dest='ar')
        translated = res.text
        # تصحيحات فورية لضمان جودة MSP
        replacements = {"مجلة": "دفتر يومية", "نشر": "ترحيل", "أمر شراء": "طلب شراء"}
        for old, new in replacements.items():
            translated = translated.replace(old, new)
        return translated, "[AUTO]"
    except:
        return text, "[WAITING/FAIL]"

def run_engine():
    print("\n" + "="*85)
    print(fix_ar(f"--- MSP MANAGEMENT DASHBOARD v1.8.9 | {time.strftime('%Y-%m-%d')} ---"))
    print("="*85)

    state = {"file": "", "last_index": 0}
    if os.path.exists(CHECKPOINT_PATH):
        with open(CHECKPOINT_PATH, 'r', encoding='utf-8') as f:
            state = json.load(f)

    if not os.path.exists(EXCEL_DICTIONARY):
        print("❌ CRITICAL: Dictionary.xlsx not found!"); return

    log_data = pd.read_excel(EXCEL_DICTIONARY)
    msp_dict = dict(zip(log_data.iloc[:, 1].astype(str).str.strip(), log_data.iloc[:, 2].astype(str).str.strip()))

    for file_name in TARGET_FILES:
        if not os.path.exists(file_name): continue
        if state["file"] and file_name < state["file"]: continue

        output_name = file_name.replace(".cs-CZ.xlf", ".ar-JO.xlf")
        tree = etree.parse(file_name)
        root = tree.getroot()
        ns = {"ns": "urn:oasis:names:tc:xliff:document:1.2"}
        units = root.xpath("//ns:trans-unit", namespaces=ns)
        
        total = len(units)
        start_idx = state["last_index"] if state["file"] == file_name else 0
        
        print(f"\n📂 {fix_ar('بدء معالجة ملف:')} {file_name} ({total} {fix_ar('وحدة')})")
        
        with tqdm(total=total, initial=start_idx, desc="PROGRESS", unit="msg", colour='green') as pbar:
            for i in range(start_idx, total):
                unit = units[i]
                source = unit.find("ns:source", namespaces=ns)
                target = unit.find("ns:target", namespaces=ns)
                
                if target is None:
                    target = etree.SubElement(unit, "{urn:oasis:names:tc:xliff:document:1.2}target")

                if source is not None and source.text:
                    src_val = source.text
                    translated, mode = smart_translate(src_val, msp_dict)
                    target.text = translated
                    target.set("state", "translated")

                    # الفيدباك التفصيلي
                    short_en = (src_val[:25] + '..') if len(src_val) > 25 else src_val.ljust(27)
                    short_ar = (translated[:25] + '..') if len(translated) > 25 else translated
                    tqdm.write(f"PROCESSED: {mode:<7} | {short_en} -> {fix_ar(short_ar)}")

                if (i + 1) % 15 == 0 or i == total - 1:
                    tree.write(output_name, encoding="utf-8", xml_declaration=True)
                    with open(CHECKPOINT_PATH, 'w', encoding='utf-8') as f:
                        json.dump({"file": file_name, "last_index": i + 1}, f)
                
                pbar.update(1)

        state = {"file": "", "last_index": 0} 

    print("\n" + "="*85)
    print("✅ " + fix_ar("تم الانتهاء بنجاح. كافة المصطلحات الفنية لـ MSP مطابقة الآن."))
    print("="*85)

if __name__ == "__main__":
    try:
        run_engine()
    except KeyboardInterrupt:
        print("\n🛑 " + fix_ar("تم إيقاف المحرك.. التقدم محفوظ."))
# /* === END OF FILE === */