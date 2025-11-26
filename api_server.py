"""
api_server.py - FastAPI Server للتحقق من الإعلانات (Monetag)

هذا الملف يدير:
1. توليد التوكنات للمستخدمين
2. عرض واجهة المشاهدة
3. التحقق من المشاهدة وإرسال Postback لـ Monetag
4. التواصل مع بوت التليجرام
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
import secrets
import aiohttp
import logging
from storage_utils import create_new_token, get_token_data, update_token_status # يجب تحديث هذا الملف للعمل في الذاكرة

# إعداد Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# الثوابت
BOT_SECRET = "3HydCoOi2byXBvkjAtG98KOT1u-r18t0G5aPPbHWvcY"
MONETAG_POSTBACK_URL = "https://api.monetag.com/postback?token={token}&status=completed"  # استبدل بالرابط الفعلي من Monetag
AD_LINK = "https://otieu.com/4/10231904"  # رابط الإعلان من Monetag

app = FastAPI(title="Manhaj AI - Ad Verification API")

# Models
class CreateTokenRequest(BaseModel):
    user_id: int
    secret: str

class CheckTokenRequest(BaseModel):
    token: str
    secret: str

class CompleteAdRequest(BaseModel):
    token: str

# ===================
# API Endpoints
# ===================

@app.post("/api/create-token")
async def create_token(request: CreateTokenRequest):
    """
    إنشاء توكن تحقق جديد
    يستدعى من البوت عند طلب مشاهدة إعلان
    """
    # التحقق من المفتاح السري
    if request.secret != BOT_SECRET:
        raise HTTPException(status_code=403, detail="Invalid secret key")
    
    # توليد توكن فريد
    token = secrets.token_urlsafe(32)
    
    # حفظ في التخزين
    create_new_token(request.user_id, token)
    
    # إنشاء رابط التحقق
    # تم تغيير الرابط الأساسي إلى http://localhost:8000 لضمان العمل على Vercel إذا كان الرابط القديم غير صحيح
    # يمكنك تغييره إلى رابط Vercel الفعلي بعد النشر: https://manhaj-ai-api.vercel.app
    verify_url = f"https://manhaj-ai-api.vercel.app/verify-ad/{token}" 
    
    logger.info(f"Created token for user {request.user_id}: {token}")
    
    return {
        "success": True,
        "token": token,
        "verify_url": verify_url,
        "user_id": request.user_id
    }

@app.post("/api/check-token")
async def check_token(request: CheckTokenRequest):
    """
    التحقق من حالة التوكن
    يستدعى من البوت للتحقق إذا تمت المشاهدة
    """
    # التحقق من المفتاح السري
    if request.secret != BOT_SECRET:
        raise HTTPException(status_code=403, detail="Invalid secret key")
    
    # البحث عن التوكن
    token_data = get_token_data(request.token)
    
    if not token_data:
        return {
            "success": False,
            "verified": False,
            "error": "Token not found"
        }
    
    return {
        "success": True,
        "verified": token_data["verified"],
        "user_id": token_data["user_id"],
        "created_at": token_data["created_at"],
        "verified_at": token_data.get("verified_at")
    }

# ------------------------------------------------
# الدالة المعدلة مع المؤقت
# ------------------------------------------------

@app.get("/verify-ad/{token}", response_class=HTMLResponse)
async def verify_ad_page(token: str):
    """
    صفحة HTML لمشاهدة الإعلان مع مؤقت إجباري (15 ثانية)
    """
    # التحقق من وجود التوكن
    token_data = get_token_data(token)
    
    if not token_data:
        return """
        <!DOCTYPE html>
        <html dir="rtl">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>خطأ</title>
        </head>
        <body style="font-family: Arial; text-align: center; padding: 50px;">
            <h1>❌ رابط غير صالح</h1>
            <p>الرابط الذي استخدمته غير صحيح أو منتهي الصلاحية.</p>
        </body>
        </html>
        """
    
    if token_data["verified"]:
        return """
        <!DOCTYPE html>
        <html dir="rtl">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>تم التحقق</title>
        </head>
        <body style="font-family: Arial; text-align: center; padding: 50px;">
            <h1>✅ تم التحقق مسبقاً</h1>
            <p>لقد تم التحقق من هذا الإعلان مسبقاً.</p>
            <p>يمكنك العودة للبوت.</p>
        </body>
        </html>
        """
    
    # صفحة المشاهدة المعدلة مع التايمر
    REQUIRED_VIEW_TIME = 15 # ثابت للعرض في الكود (محدد بـ 15 ثانية)
    
    html_content = f"""
    <!DOCTYPE html>
    <html lang="ar" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>مشاهدة الإعلان - بوت منهج AI</title>
        <style>
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                display: flex;
                justify-content: center;
                align-items: center;
                padding: 20px;
            }}
            .container {{
                background: white;
                border-radius: 20px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                max-width: 600px;
                width: 100%;
                padding: 40px;
                text-align: center;
            }}
            h1 {{
                color: #667eea;
                margin-bottom: 20px;
            }}
            /* نمط رسالة الحالة الرئيسية */
            #mainStatus {{
                font-size: 18px;
                font-weight: bold;
                color: #764ba2;
                margin-bottom: 15px;
                padding: 10px;
                border-radius: 8px;
                background-color: #f7f7ff;
            }}
            .status-done {{
                color: #27ae60 !important;
                background-color: #e6ffe6;
            }}
            .instructions {{
                background: #fff3cd;
                border: 2px solid #ffeaa7;
                border-radius: 10px;
                padding: 20px;
                margin: 20px 0;
                text-align: right;
            }}
            .instructions ol {{
                margin-right: 20px;
            }}
            .instructions li {{
                margin: 10px 0;
                font-size: 16px;
            }}
            .ad-link {{
                display: inline-block;
                background: #3498db;
                color: white;
                padding: 15px 30px;
                text-decoration: none;
                border-radius: 10px;
                font-size: 18px;
                font-weight: bold;
                margin: 20px 0;
                transition: all 0.3s;
            }}
            .ad-link:hover {{
                background: #2980b9;
                transform: translateY(-2px);
            }}
            #confirmBtn {{
                background: #27ae60;
                color: white;
                border: none;
                padding: 18px 40px;
                font-size: 20px;
                font-weight: bold;
                border-radius: 50px;
                cursor: pointer;
                transition: all 0.3s;
                margin-top: 20px;
            }}
            #confirmBtn:hover:not(:disabled) {{
                background: #229954;
                transform: translateY(-2px);
            }}
            #confirmBtn:disabled {{
                background: #95a5a6; /* لون رمادي لزر معطل */
                cursor: not-allowed;
                transform: none;
            }}
            #message {{
                margin-top: 20px;
                padding: 15px;
                border-radius: 10px;
                display: none;
            }}
            .success {{
                background: #d4edda;
                color: #155724;
                border: 2px solid #c3e6cb;
            }}
            .error {{
                background: #f8d7da;
                color: #721c24;
                border: 2px solid #f5c6cb;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🎯 شاهد الإعلان للحصول على النقاط</h1>
            
            <p id="mainStatus">
                1. اضغط على زر "🌐 فتح الإعلان" لبدء المشاهدة والمؤقت.
            </p>

            <div class="instructions">
                <strong>📋 التعليمات:</strong>
                <ol>
                    <li>اضغط على زر "فتح الإعلان" أدناه <b>(لبدء المؤقت)</b></li>
                    <li>ابقَ في صفحة الإعلان حتى انتهاء المؤقت <b>({REQUIRED_VIEW_TIME} ثانية)</b></li>
                    <li>ارجع لهذه الصفحة واضغط على زر "أكد المشاهدة" (سيتم تفعيله بعد انتهاء المؤقت)</li>
                </ol>
            </div>
            
            <a href="{AD_LINK}" target="_blank" class="ad-link" onclick="startVerification()">
                🌐 فتح الإعلان
            </a>
            
            <br><br>
            
            <button id="confirmBtn" onclick="confirmView()" disabled>
                ⏳ انتظر {REQUIRED_VIEW_TIME} ثانية...
            </button>
            
            <div id="message"></div>
        </div>

        <script>
            const token = '{token}';
            const REQUIRED_VIEW_TIME = 15; // 15 ثانية للمشاهدة
            
            let timeLeft = REQUIRED_VIEW_TIME;
            let timerInterval = null;
            let timerStarted = false;
            
            const confirmBtn = document.getElementById('confirmBtn');
            const mainStatus = document.getElementById('mainStatus');
            const msgDiv = document.getElementById('message');

            function updateTimerDisplay() {{
                if (timeLeft > 0) {{
                    confirmBtn.textContent = `⏳ انتظر ${timeLeft} ثانية...`;
                    mainStatus.innerHTML = `2. الرجاء البقاء في الإعلان! المتبقي: <b>${timeLeft} ثانية</b> ⏳`;
                }} else {{
                    clearInterval(timerInterval);
                    confirmBtn.textContent = '✅ أكد المشاهدة الآن';
                    confirmBtn.disabled = false;
                    mainStatus.innerHTML = '✅ <b>انتهى وقت المشاهدة!</b> اضغط "أكد المشاهدة"';
                    mainStatus.classList.add('status-done');
                }}
            }}
            
            function startTimer() {{
                if (timerStarted) return;
                
                timerStarted = true;
                confirmBtn.disabled = true;
                
                updateTimerDisplay();
                
                timerInterval = setInterval(() => {{
                    timeLeft--;
                    updateTimerDisplay();
                    
                    if (timeLeft <= 0) {{
                        clearInterval(timerInterval);
                    }}
                }}, 1000);
            }}

            function startVerification() {{
                // إذا حاول الفتح مرة أخرى والمؤقت يعمل
                if (timerStarted && timeLeft > 0) {{
                     mainStatus.innerHTML = `2. المؤقت قيد التشغيل: <b>${timeLeft} ثانية</b> متبقية.`;
                     return;
                }}

                // إذا حاول الفتح بعد الانتهاء
                if (timeLeft <= 0) {{
                     mainStatus.innerHTML = '✅ <b>انتهى وقت المشاهدة!</b> اضغط "أكد المشاهدة"';
                     return;
                }}

                // عند الضغط لأول مرة
                startTimer();
                msgDiv.style.display = 'none'; // إخفاء أي رسالة سابقة
            }}
            
            async function confirmView() {{
                // الشرط الحاسم: التحقق من انتهاء المؤقت وبدئه
                if (timeLeft > 0 || !timerStarted) {{
                    msgDiv.className = 'error';
                    msgDiv.style.display = 'block';
                    msgDiv.innerHTML = '⚠️ يجب عليك الانتظار حتى انتهاء العداد بعد الضغط على "فتح الإعلان"!';
                    return;
                }}
                
                // بدء عملية التحقق (API Call)
                confirmBtn.disabled = true;
                confirmBtn.textContent = '⏳ جاري التحقق...';
                msgDiv.style.display = 'none';
                
                try {{
                    // هنا يتم استدعاء API /api/complete-ad
                    const response = await fetch('/api/complete-ad', {{
                        method: 'POST',
                        headers: {{
                            'Content-Type': 'application/json'
                        }},
                        body: JSON.stringify({{ token: token }})
                    }});
                    
                    // يتم التحقق هنا من حالة استجابة الشبكة (HTTP status)
                    if (!response.ok) {{
                        // إذا كانت الحالة 500 أو 404 أو غيرها
                        const errorData = await response.json().catch(() => ({{}})); 
                        throw new Error(errorData.detail || 'فشل التحقق بسبب خطأ في الخادم (يرجى مراجعة سجلات Vercel)');
                    }}

                    const data = await response.json();
                    
                    if (data.success) {{
                        msgDiv.className = 'success';
                        msgDiv.innerHTML = 
                            '✅ <strong>تم التحقق بنجاح!</strong><br><br>' +
                            '🎁 سيتم إضافة النقاط لحسابك خلال ثوانٍ<br>' +
                            '🔙 يمكنك العودة للبوت الآن';
                        mainStatus.style.display = 'none'; // إخفاء حالة المشاهدة بعد النجاح
                        confirmBtn.style.display = 'none'; // إخفاء الزر بعد النجاح
                    }} else {{
                        msgDiv.className = 'error';
                        msgDiv.innerHTML = '❌ <strong>حدث خطأ:</strong><br>' + (data.error || 'خطأ غير معروف');
                        confirmBtn.disabled = false;
                        confirmBtn.textContent = '✅ أكد المشاهدة الآن'; // إعادة الزر لحالته
                    }}
                    msgDiv.style.display = 'block';
                }} catch (error) {{
                    // معالجة خطأ الشبكة (No Internet) أو الخطأ الذي تم إثارته أعلاه
                    msgDiv.className = 'error';
                    msgDiv.innerHTML = `❌ <strong>خطأ في الاتصال</strong><br>يرجى المحاولة مرة أخرى والتأكد من اتصالك بالإنترنت. تفاصيل الخطأ: ${error.message}`;
                    msgDiv.style.display = 'block';
                    confirmBtn.disabled = false;
                    confirmBtn.textContent = '✅ أكد المشاهدة الآن'; // إعادة الزر لحالته
                }}
            }}

            // عند تحميل الصفحة
            updateTimerDisplay();

        </script>
    </body>
    </html>
    """
    
    return HTMLResponse(content=html_content)


@app.post("/api/complete-ad")
async def complete_ad(request: CompleteAdRequest):
    """
    تأكيد مشاهدة الإعلان وإرسال Postback لـ Monetag
    """
    token = request.token
    
    # البحث عن التوكن
    token_data = get_token_data(token)
    
    if not token_data:
        raise HTTPException(status_code=404, detail="Token not found")
    
    if token_data["verified"]:
        raise HTTPException(status_code=400, detail="Already verified")
    
    # تحديث حالة التوكن
    update_token_status(token, verified=True)
    
    # إرسال Postback لـ Monetag
    postback_url = MONETAG_POSTBACK_URL.format(token=token)
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(postback_url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    logger.info(f"✅ Postback sent successfully for token {token}")
                else:
                    logger.error(f"⚠️ Postback failed with status {response.status} for token {token}. Response: {await response.text()}")
    except Exception as e:
        logger.error(f"❌ Error sending postback for token {token}: {e}")
        # نكمل حتى لو فشل الـ Postback
    
    logger.info(f"Token {token} marked as verified for user {token_data['user_id']}")
    
    return {
        "success": True,
        "message": "Ad verification completed successfully",
        "user_id": token_data["user_id"]
    }

@app.get("/")
async def root():
    """الصفحة الرئيسية"""
    return {
        "service": "Manhaj AI - Ad Verification API",
        "status": "running",
        "endpoints": {
            "create_token": "POST /api/create-token",
            "check_token": "POST /api/check-token",
            "verify_page": "GET /verify-ad/{token}",
            "complete_ad": "POST /api/complete-ad"
        }
    }

# للتشغيل المحلي
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
