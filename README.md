# Manhaj AI - Ad Verification API 🎯

نظام التحقق من الإعلانات لبوت منهج AI مع تكامل Monetag

## 📁 الهيكل

```
mini_app/
├── api_server.py        # الـ API الرئيسي (FastAPI)
├── storage_utils.py     # إدارة البيانات (JSON مؤقت)
├── requirements.txt     # المكتبات المطلوبة
├── vercel.json         # إعدادات النشر على Vercel
├── runtime.txt         # إصدار Python
└── README.md          # هذا الملف
```

## 🚀 النشر على Vercel

### 1. إنشاء حساب Vercel
- اذهب إلى [vercel.com](https://vercel.com)
- سجّل دخول بحساب GitHub

### 2. ربط المشروع
```bash
# تثبيت Vercel CLI
npm install -g vercel

# تسجيل الدخول
vercel login

# نشر المشروع
cd mini_app
vercel --prod
```

### 3. الحصول على رابط الـ API
بعد النشر، ستحصل على رابط مثل:
```
https://manhaj-ai-api.vercel.app
```

### 4. تحديث البوت
غيّر `VERIFY_API_BASE_URL` في `app.py` لاستخدام رابط Vercel الخاص بك.

## 🔗 Endpoints

### 1. إنشاء توكن
```http
POST /api/create-token
Content-Type: application/json

{
  "user_id": 123456789,
  "secret": "3HydCoOi2byXBvkjAtG98KOT1u-r18t0G5aPPbHWvcY"
}
```

**Response:**
```json
{
  "success": true,
  "token": "abc123...",
  "verify_url": "https://manhaj-ai-api.vercel.app/verify-ad/abc123...",
  "user_id": 123456789
}
```

### 2. فحص التوكن
```http
POST /api/check-token
Content-Type: application/json

{
  "token": "abc123...",
  "secret": "3HydCoOi2byXBvkjAtG98KOT1u-r18t0G5aPPbHWvcY"
}
```

**Response:**
```json
{
  "success": true,
  "verified": true,
  "user_id": 123456789,
  "created_at": "2024-01-01T12:00:00",
  "verified_at": "2024-01-01T12:05:00"
}
```

### 3. صفحة التحقق
```http
GET /verify-ad/{token}
```
صفحة HTML للمستخدم لمشاهدة الإعلان

### 4. تأكيد المشاهدة
```http
POST /api/complete-ad
Content-Type: application/json

{
  "token": "abc123..."
}
```

## 💰 تكامل Monetag

### 1. الحصول على Postback URL
- سجّل في [Monetag](https://monetag.com)
- احصل على رابط Postback من لوحة التحكم
- الرابط عادة بهذا الشكل:
  ```
  https://api.monetag.com/postback?campaign_id=XXX&click_id={token}&status=completed
  ```

### 2. تحديث API Server
في ملف `api_server.py`، غيّر:
```python
MONETAG_POSTBACK_URL = "رابط_postback_الحقيقي_هنا"
```

### 3. تحديث رابط الإعلان
```python
AD_LINK = "رابط_اعلان_monetag_الحقيقي"
```

## ⚠️ ملاحظات مهمة

### التخزين
حالياً النظام يستخدم JSON للتخزين (ملف `tokens_data.json`).

**للإنتاج:**
- يجب استخدام قاعدة بيانات خارجية (MongoDB Atlas, PostgreSQL)
- Vercel Serverless لا تحتفظ بالملفات بين الاستدعاءات
- استخدم:
  - [MongoDB Atlas](https://www.mongodb.com/cloud/atlas) (مجاني حتى 512 MB)
  - [Supabase](https://supabase.com) (PostgreSQL مجاني)
  - [PlanetScale](https://planetscale.com) (MySQL serverless)

### الأمان
- `BOT_SECRET` يجب أن يكون فريداً وسرياً
- لا تشاركه في الكود المنشور
- استخدم Environment Variables في Vercel:
  ```bash
  vercel env add BOT_SECRET
  ```

## 🧪 الاختبار المحلي

```bash
cd mini_app

# تثبيت المكتبات
pip install -r requirements.txt

# تشغيل السيرفر
python api_server.py

# السيرفر سيعمل على
# http://localhost:8000
```

اختبار الـ API:
```bash
# إنشاء توكن
curl -X POST http://localhost:8000/api/create-token \
  -H "Content-Type: application/json" \
  -d '{"user_id": 123, "secret": "3HydCoOi2byXBvkjAtG98KOT1u-r18t0G5aPPbHWvcY"}'

# فتح صفحة التحقق
# افتح المتصفح على الرابط الذي ترجع من create-token
```

## 📊 سير العمل

```
1. المستخدم يطلب إجابة من البوت
   ↓
2. البوت يتحقق: Premium؟
   ↓ لا
3. البوت يرسل POST /api/create-token
   ↓
4. API يولّد توكن ويرجع verify_url
   ↓
5. البوت يرسل الرابط للمستخدم
   ↓
6. المستخدم يفتح الرابط
   ↓
7. صفحة HTML تعرض زر فتح الإعلان
   ↓
8. المستخدم يضغط "فتح الإعلان" → يفتح Monetag
   ↓
9. المستخدم يشاهد الإعلان ويرجع
   ↓
10. المستخدم يضغط "أكد المشاهدة"
    ↓
11. JavaScript يرسل POST /api/complete-ad
    ↓
12. API يحدّث التوكن + يرسل Postback لـ Monetag
    ↓
13. البوت يفحص POST /api/check-token (polling)
    ↓
14. البوت يستقبل verified=true
    ↓
15. البوت يُرسل الإجابة للمستخدم ✅
```

## 🐛 حل المشاكل

### المشكلة: "Token not found"
- تحقق أن الـ storage_utils.py يعمل بشكل صحيح
- للإنتاج: انتقل لقاعدة بيانات خارجية

### المشكلة: "Invalid secret key"
- تأكد أن `BOT_SECRET` متطابق في البوت والـ API

### المشكلة: Monetag Postback لا يعمل
- تحقق من رابط Postback في حساب Monetag
- تأكد من استخدام `{token}` كـ click_id
- راجع logs في Vercel

### المشكلة: البوت لا يستقبل التحديث
- تحقق من الـ polling في `check_ad_verification_status()`
- راجع response من `/api/check-token`

## 📱 التواصل

للمزيد من المساعدة، راجع:
- [Vercel Docs](https://vercel.com/docs)
- [FastAPI Docs](https://fastapi.tiangolo.com)
- [Monetag Support](https://monetag.com/support)

---

**بُني بواسطة GitHub Copilot** 🤖
