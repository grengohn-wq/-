import os
from pdf2image import convert_from_path
import pytesseract
from tqdm import tqdm # لعرض شريط تقدم أنيق

# --- إعدادات التكوين ---
# 1. مسار مجلد الإدخال (ضع فيه ملفات PDF)
INPUT_DIR = "Input_PDFs"
# 2. مسار مجلد الإخراج (ستظهر فيه ملفات TXT)
OUTPUT_DIR = "Output_TXTs"
# 3. إعدادات محرك Tesseract
# إذا كنت تستخدم Tesseract، قم بتحديد مسار ملفه التنفيذي (exe).
# مثلاً لنظام ويندوز: pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
# إذا كان مثبتًا لديك في المسار الافتراضي، فقد لا تحتاج لهذا السطر.
# pytesseract.pytesseract.tesseract_cmd = r'مسار ملف Tesseract التنفيذي هنا' # قم بإلغاء التعليق وتعديله إذا لزم الأمر

# استخدم لغة OCR العربية (ara)
OCR_LANG = 'ara' 

# --- تأكد من وجود مجلدات الإدخال والإخراج ---
os.makedirs(INPUT_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# --- قائمة جميع ملفات PDF في مجلد الإدخال ---
pdf_files = [f for f in os.listdir(INPUT_DIR) if f.lower().endswith('.pdf')]

if not pdf_files:
    print(f"❌ لم يتم العثور على ملفات PDF في المجلد: {INPUT_DIR}")
else:
    print(f"✅ تم العثور على {len(pdf_files)} كتاباً. بدء المعالجة...")
    
    # حلقة لمعالجة كل كتاب على حدة
    for pdf_file in tqdm(pdf_files, desc="التقدم الإجمالي"):
        pdf_path = os.path.join(INPUT_DIR, pdf_file)
        txt_filename = os.path.splitext(pdf_file)[0] + ".txt"
        txt_path = os.path.join(OUTPUT_DIR, txt_filename)
        
        # تخطي الملف إذا كان موجودًا بالفعل في مجلد الإخراج
        if os.path.exists(txt_path):
            print(f"\n⬅️ تخطي: {pdf_file} (موجود مسبقاً)")
            continue

        try:
            # 1. تحويل صفحات الـ PDF إلى صور (مطلوب لـ Tesseract)
            pages = convert_from_path(pdf_path, 300) # 300 DPI للحصول على جودة OCR عالية

            full_text = []
            
            # حلقة لمعالجة كل صفحة كصورة
            for i, page_image in enumerate(pages):
                # 2. تطبيق OCR على الصورة واستخراج النص العربي
                text = pytesseract.image_to_string(page_image, lang=OCR_LANG)
                full_text.append(text)
                
            # 3. حفظ النص المستخرج في ملف TXT واحد
            with open(txt_path, 'w', encoding='utf-8') as f:
                f.write("\n\n" + "-"*50 + "\n\n".join(full_text))

            print(f"\n🎉 تم بنجاح: {pdf_file} -> {txt_filename}")
            
        except Exception as e:
            print(f"\n❌ حدث خطأ أثناء معالجة {pdf_file}: {e}")

    print("\n\n--- اكتملت معالجة الدُفعات ---")
