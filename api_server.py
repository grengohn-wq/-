# api_server.py - FastAPI Server للتحقق من الإعلانات (بدون مؤقت)

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
import secrets
import aiohttp
import logging
from storage_utils import create_new_token, get_token_data, update_token_status 

# إعداد Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# الثوابت (يرجى التأكد من صحة هذه الروابط والأسرار)
BOT_SECRET = "3HydCoOi2byXBvkjAtG98KOT1u-r18t0G5aPPbHWvcY"
MONETAG_POSTBACK_URL = "https://api.monetag.com/postback?token={token}&status=completed"
AD_LINK = "https://otieu.com/4/10231904" 
# تأكد من استبدال هذا الرابط برابط Vercel الخاص بك
VERCEL_BASE_URL = "https://manhaj-ai-api.vercel.app" 

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

@app.post("/api/create-token")
async def create_token(request: CreateTokenRequest):
    if request.secret != BOT_SECRET:
        raise HTTPException(status_code=403, detail="Invalid secret key")
    
    token = secrets.token_urlsafe(32)
    create_new_token(request.user_id, token)
    
    verify_url = f"{VERCEL_BASE_URL}/verify-ad/{token}" 
    
    return {
        "success": True,
        "token": token,
        "verify_url": verify_url,
        "user_id": request.user_id
    }

@app.post("/api/check-token")
async def check_token(request: CheckTokenRequest):
    if request.secret != BOT_SECRET:
        raise HTTPException(status_code=403, detail="Invalid secret key")
    
    token_data = get_token_data(request.token)
    
    if not token_data:
        return {"success": False, "verified": False, "error": "Token not found"}
    
    return {"success": True, "verified": token_data["verified"], "user_id": token_data["user_id"]}


# ------------------------------------------------
# صفحة التحقق (بدون مؤقت)
# ------------------------------------------------

@app.get("/verify-ad/{token}", response_class=HTMLResponse)
async def verify_ad_page(token: str):
    token_data = get_token_data(token)
    
    if not token_data:
        return HTMLResponse("<h1>❌ رابط غير صالح</h1><p>الرابط الذي استخدمته غير صحيح أو منتهي الصلاحية.</p>", status_code=404)
    
    if token_data["verified"]:
        return HTMLResponse("<h1>✅ تم التحقق مسبقاً</h1><p>لقد تم التحقق من هذا الإعلان مسبقاً.</p>")
    
    # صفحة المشاهدة الأساسية (بدون تايمر)
    html_content = f"""
    <!DOCTYPE html>
    <html lang="ar" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>مشاهدة الإعلان - بوت منهج AI</title>
        <style>
            body {{ font-family: Arial; text-align: center; padding: 20px; background: #f4f4f4; }}
            .container {{ background: white; padding: 30px; border-radius: 10px; box-shadow: 0 0 10px rgba(0,0,0,0.1); max-width: 400px; margin: auto; }}
            .ad-link {{ display: inline-block; background: #3498db; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; font-weight: bold; margin: 15px 0; }}
            #confirmBtn {{ background: #27ae60; color: white; border: none; padding: 15px 30px; border-radius: 5px; cursor: pointer; font-size: 18px; margin-top: 20px; }}
            #message {{ margin-top: 15px; padding: 10px; border-radius: 5px; display: none; }}
            .success {{ background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }}
            .error {{ background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🎯 شاهد الإعلان</h1>
            
            <p>1. اضغط على الزر لفتح صفحة الإعلان:</p>
            <a href="{AD_LINK}" target="_blank" class="ad-link">
                🌐 فتح الإعلان
            </a>
            
            <p>2. بعد مشاهدة الإعلان، عد واضغط على زر التأكيد:</p>
            
            <button id="confirmBtn" onclick="confirmView()">
                ✅ أكد المشاهدة
            </button>
            
            <div id="message"></div>
        </div>

        <script>
            const token = '{token}';
            const confirmBtn = document.getElementById('confirmBtn');
            const msgDiv = document.getElementById('message');

            async function confirmView() {{
                confirmBtn.disabled = true;
                confirmBtn.textContent = '⏳ جاري التحقق...';
                msgDiv.style.display = 'none';
                
                try {{
                    const response = await fetch('/api/complete-ad', {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json' }},
                        body: JSON.stringify({{ token: token }})
                    }});
                    
                    const data = await response.json();
                    
                    if (data.success) {{
                        msgDiv.className = 'success';
                        msgDiv.innerHTML = '✅ <strong>تم التحقق بنجاح!</strong><br>يمكنك العودة للبوت الآن.';
                        confirmBtn.style.display = 'none'; 
                    }} else {{
                        msgDiv.className = 'error';
                        msgDiv.innerHTML = '❌ <strong>حدث خطأ:</strong><br>' + (data.detail || data.error || 'خطأ غير معروف');
                        confirmBtn.disabled = false;
                        confirmBtn.textContent = '✅ أكد المشاهدة';
                    }}
                    msgDiv.style.display = 'block';
                }} catch (error) {{
                    msgDiv.className = 'error';
                    msgDiv.innerHTML = `❌ <strong>خطأ في الاتصال</strong><br>يرجى المحاولة مرة أخرى.`;
                    msgDiv.style.display = 'block';
                    confirmBtn.disabled = false;
                    confirmBtn.textContent = '✅ أكد المشاهدة';
                }}
            }}
        </script>
    </body>
    </html>
    """
    
    return HTMLResponse(content=html_content)


@app.post("/api/complete-ad")
async def complete_ad(request: CompleteAdRequest):
    token = request.token
    token_data = get_token_data(token)
    
    if not token_data:
        raise HTTPException(status_code=404, detail="Token not found")
    
    if token_data["verified"]:
        raise HTTPException(status_code=400, detail="Already verified")
    
    update_token_status(token, verified=True)
    
    # إرسال Postback لـ Monetag
    postback_url = MONETAG_POSTBACK_URL.format(token=token)
    
    try:
        async with aiohttp.ClientSession() as session:
            # هنا يتم إرسال طلب Postback ولا يهم نتيجته النهائية لرد الـ API
            await session.get(postback_url, timeout=5) 
    except Exception as e:
        logger.error(f"❌ Error sending postback for token {token}: {e}")
    
    return {
        "success": True,
        "message": "Ad verification completed successfully",
        "user_id": token_data["user_id"]
    }

@app.get("/")
async def root():
    return {"service": "Manhaj AI - Ad Verification API", "status": "running"}
