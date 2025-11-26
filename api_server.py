# mini_app/api_server.py

"""
api_server.py - FastAPI Server للتحقق من الإعلانات (Monetag) - نسخة Vercel المصححة

هذا الملف يدير:
1. توليد التوكنات للمستخدمين
2. عرض واجهة المشاهدة
3. التحقق من المشاهدة وإرسال Postback لـ Monetag
4. التواصل مع بوت التليجرام
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
import uuid
import aiohttp
import logging
import os 
# تم تحديث الاستيراد: إزالة initialize_db
from .storage_utils import create_new_token, get_token_data, update_token_status 


# إعداد Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# الثوابت
BOT_SECRET = "3HydCoOi2byXBvkjAtG98KOT1u-r18t0G5aPPbHWvcY"
MONETAG_POSTBACK_URL = "https://api.monetag.com/postback?token={token}&status=completed" 
AD_LINK = "https://otieu.com/4/10231904" 
VERCEL_BASE_URL = os.environ.get('VERCEL_URL', 'http://localhost:8000')

# تم حذف استدعاء initialize_db() الذي كان يسبب التعطل
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
    secret: str 

# ===================
# دوال مساعدة لـ Monetag
# ===================
async def send_monetag_postback(token: str):
    """إرسال طلب Postback إلى Monetag لتأكيد التحويل."""
    postback_url = MONETAG_POSTBACK_URL.format(token=token)
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(postback_url, timeout=10) as response:
                if response.status == 200:
                    logger.info(f"✅ Postback sent successfully for token {token}")
                    return True
                else:
                    logger.error(f"⚠️ Postback failed with status {response.status} for token {token}")
                    return False
    except Exception as e:
        logger.error(f"❌ Error sending postback for token {token}: {e}")
        return False

# ===================
# API Endpoints
# ===================

@app.post("/api/create-token")
async def create_token_endpoint(req: CreateTokenRequest):
    if req.secret != BOT_SECRET:
        raise HTTPException(status_code=403, detail="Invalid secret key")
    
    token = str(uuid.uuid4())
    token_data = create_new_token(req.user_id, token)
    
    # بناء رابط التحقق (الصفحة التي يفتحها المستخدم)
    # استخدام VERCEL_BASE_URL لضمان الرابط الصحيح
    verify_url = f"https://{VERCEL_BASE_URL}/verify-ad/{token}" 
    
    return JSONResponse({
        "success": True,
        "token": token,
        "verify_url": verify_url,
        "user_id": req.user_id
    })

@app.post("/api/check-token")
async def check_token_endpoint(req: CheckTokenRequest):
    if req.secret != BOT_SECRET:
        raise HTTPException(status_code=403, detail="Invalid secret key")
        
    token_data = get_token_data(req.token)
    
    if not token_data:
        # هذا هو الرد المتوقع عندما تفقد البيانات على Vercel
        return JSONResponse({"success": False, "verified": False, "error": "Token not found (or data lost on Vercel)"})
        
    return JSONResponse({
        "success": True,
        "verified": token_data.get("verified", False),
        "user_id": token_data["user_id"]
    })

@app.get("/verify-ad/{token}", response_class=HTMLResponse)
async def verify_ad_page(token: str):
    token_data = get_token_data(token)
    
    if not token_data:
        return HTMLResponse("<h1>❌ Token غير صالح - قد تكون انتهت صلاحيته أو فُقدت بياناته.</h1>")
        
    if token_data.get("verified"):
        return HTMLResponse("<h1>✅ تم التحقق من هذا الإعلان مسبقاً!</h1>")
    
    html_content = f"""
    <!DOCTYPE html>
    <html lang="ar" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>صفحة التحقق من الإعلان</title>
        <style>
            body {{ font-family: Tahoma, Arial, sans-serif; text-align: center; margin-top: 50px; background: #f4f4f9; }}
            .container {{ background: white; padding: 30px; border-radius: 10px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); max-width: 400px; margin: auto; }}
            .ad-link {{ background-color: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; font-size: 1.1em; display: inline-block; margin-bottom: 20px; }}
            .verify-btn {{ background-color: #28a745; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; font-size: 1em; }}
            .success {{ color: #28a745; font-weight: bold; }}
            .error {{ color: #dc3545; font-weight: bold; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h3>خطوات التحقق من الإعلان</h3>
            <p>1. اضغط على الزر أدناه لفتح الإعلان.</p>
            <p>2. أكمل متطلبات الإعلان (الانتظار أو النقر).</p>
            <p>3. بعد الإكمال، اضغط على زر "أكد المشاهدة".</p>
            
            <a href="{AD_LINK}" target="_blank" class="ad-link" id="adLink">🌐 فتح الإعلان (Monetag)</a>
            
            <button class="verify-btn" onclick="confirmAdWatched('{token}')" id="confirmBtn">أكد المشاهدة</button>
            
            <div id="message" style="margin-top: 20px;"></div>
        </div>

        <script>
            const API_BASE = window.location.origin;
            const BOT_SECRET_JS = '{BOT_SECRET}'; 

            async function confirmAdWatched(token) {{
                const btn = document.getElementById('confirmBtn');
                const msgDiv = document.getElementById('message');
                
                btn.disabled = true;
                msgDiv.innerHTML = "جاري التحقق من الإكمال...";

                try {{
                    const response = await fetch(`${{API_BASE}}/api/complete-ad`, {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json' }},
                        body: JSON.stringify({{ token: token, secret: BOT_SECRET_JS }})
                    }});
                    const data = await response.json();

                    if (data.success) {{
                        msgDiv.innerHTML = "<span class='success'>✅ تم التحقق بنجاح! يمكنك العودة للبوت.</span>";
                    }} else {{
                        msgDiv.innerHTML = `<span class='error'>❌ خطأ في التحقق: ${{data.error || 'غير معروف'}}</span>`;
                        btn.disabled = false;
                    }}
                }} catch (error) {{
                    msgDiv.innerHTML = "<span class='error'>❌ خطأ في الاتصال بالخادم. حاول مرة أخرى.</span>";
                    btn.disabled = false;
                }}
            }}
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content, status_code=200)

@app.post("/api/complete-ad")
async def complete_ad_endpoint(req: CompleteAdRequest):
    if req.secret != BOT_SECRET:
        raise HTTPException(status_code=403, detail="Invalid secret key")
        
    token_data = get_token_data(req.token)
    
    if not token_data:
        raise HTTPException(status_code=404, detail="Token not found (or data lost on Vercel)")
        
    if token_data.get("verified"):
        return JSONResponse({"success": True, "message": "Already verified"})

    # 1. تحديث حالة الرمز في التخزين المحلي
    update_token_status(req.token, verified=True) 
    
    # 2. إرسال Postback إلى Monetag
    postback_success = await send_monetag_postback(req.token)
    
    # 3. الرد على المستخدم
    if postback_success:
        return JSONResponse({"success": True, "message": "Verification complete and Postback sent."})
    else:
        # نعتبره نجاحًا طالما تم التحقق محلياً
        return JSONResponse({"success": True, "message": "Verification successful, but Monetag Postback failed."})
