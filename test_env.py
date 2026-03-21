import sys
import os

def run_diagnostic():
    print("--- تشغيل الفحص التشخيصي لـ MSP Project ---", flush=True)
    
    # 1. فحص المسار (هل نحن في فخ الـ Windows Store؟)
    py_path = sys.executable
    print(f"Path: {py_path}", flush=True)
    
    if "WindowsApps" in py_path:
        print("!!! تحذير: أنت تعمل داخل Windows Store Stub. استخدم 'py' بدلاً من 'python' !!!", flush=True)
    else:
        print("✓ مسار البايثون سليم.", flush=True)

    # 2. فحص الترميز العربي (Arabic Encoding Test)
    test_file = "test_arabic.txt"
    test_text = "تجربة تعريب نظام MSP - كرتون مضلع"
    
    try:
        # استخدام utf-8-sig لضمان ظهور العربي في ويندوز
        with open(test_file, "w", encoding="utf-8-sig") as f:
            f.write(test_text)
        print(f"✓ تم إنشاء ملف تجريبي ({test_file}) باللغة العربية بنجاح.", flush=True)
        
        # التأكد من القراءة الصحيحة
        with open(test_file, "r", encoding="utf-8-sig") as f:
            content = f.read()
            if content == test_text:
                print("✓ فحص ترميز اللغة العربية: ناجح 100%.", flush=True)
    except Exception as e:
        print(f"X خطأ في الترميز: {e}", flush=True)

    print("\n--- جاهز للبدء بترجمة الـ XLF الآن ---", flush=True)

if __name__ == "__main__":
    run_diagnostic()
