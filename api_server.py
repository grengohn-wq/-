"""
Manhaj AI - Ad & Task Verification API
FastAPI server للتحقق من الإعلانات والمهام
"""
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import secrets
import aiohttp
import logging
from datetime import datetime
from typing import Dict, Optional
import json
import os

# Setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Manhaj AI Verification API")

# Constants
BOT_SECRET = "3HydCoOi2byXBvkjAtG98KOT1u-r18t0G5aPPbHWvcY"
MONETAG_POSTBACK_URL = "https://api.monetag.com/postback?token={token}&status=completed"
AD_LINK = "https://otieu.com/4/10231904"

# In-memory storage (يتم استبداله بقاعدة بيانات في Production)
tokens_store: Dict[str, dict] = {}

# ==================== Models ====================
class CreateTokenRequest(BaseModel):
    user_id: int
    secret: str

class CreateTaskTokenRequest(BaseModel):
    user_id: int
    task_id: int
    task_url: str
    task_description: str
    task_points: int
    secret: str

class CheckTokenRequest(BaseModel):
    token: str
    secret: str

class CompleteRequest(BaseModel):
    token: str

# ==================== Storage Functions ====================
def save_token(token: str, data: dict):
    """حفظ توكن في الذاكرة"""
    tokens_store[token] = data
    logger.info(f"💾 Token saved: {token}")

def get_token(token: str) -> Optional[dict]:
    """جلب توكن من الذاكرة"""
    return tokens_store.get(token)

def update_token(token: str, verified: bool):
    """تحديث حالة التوكن"""
    if token in tokens_store:
        tokens_store[token]["verified"] = verified
        tokens_store[token]["verified_at"] = datetime.now().isoformat()
        logger.info(f"✅ Token verified: {token}")

# ==================== API Endpoints ====================

@app.post("/api/create-token")
async def create_ad_token(request: CreateTokenRequest):
    """إنشاء توكن للإعلانات"""
    if request.secret != BOT_SECRET:
        raise HTTPException(status_code=403, detail="Invalid secret")
    
    token = secrets.token_urlsafe(32)
    save_token(token, {
        "user_id": request.user_id,
        "token": token,
        "verified": False,
        "created_at": datetime.now().isoformat(),
        "verified_at": None,
        "type": "ad"
    })
    
    return {
        "success": True,
        "token": token,
        "verify_url": f"https://manhaj-ai-api.vercel.app/verify-ad/{token}",
        "user_id": request.user_id
    }

@app.post("/api/create-task-token")
async def create_task_token(request: CreateTaskTokenRequest):
    """إنشاء توكن للمهام"""
    if request.secret != BOT_SECRET:
        raise HTTPException(status_code=403, detail="Invalid secret")
    
    token = secrets.token_urlsafe(32)
    save_token(token, {
        "user_id": request.user_id,
        "token": token,
        "verified": False,
        "created_at": datetime.now().isoformat(),
        "verified_at": None,
        "type": "task",
        "task_data": {
            "task_id": request.task_id,
            "task_url": request.task_url,
            "task_description": request.task_description,
            "task_points": request.task_points
        }
    })
    
    return {
        "success": True,
        "token": token,
        "verify_url": f"https://manhaj-ai-api.vercel.app/verify-task/{token}",
        "user_id": request.user_id,
        "task_id": request.task_id
    }

@app.post("/api/check-token")
async def check_token(request: CheckTokenRequest):
    """التحقق من حالة التوكن"""
    if request.secret != BOT_SECRET:
        raise HTTPException(status_code=403, detail="Invalid secret")
    
    token_data = get_token(request.token)
    if not token_data:
        return {"success": False, "verified": False, "error": "Token not found"}
    
    return {
        "success": True,
        "verified": token_data["verified"],
        "user_id": token_data["user_id"],
        "created_at": token_data["created_at"],
        "verified_at": token_data.get("verified_at")
    }

@app.get("/verify-ad/{token}", response_class=HTMLResponse)
async def verify_ad_page(token: str):
    """صفحة HTML لمشاهدة الإعلان"""
    token_data = get_token(token)
    
    if not token_data:
        return "<html><body style='text-align:center;padding:50px;font-family:Arial;'><h1>❌ رابط غير صالح</h1></body></html>"
    
    if token_data["verified"]:
        return "<html><body style='text-align:center;padding:50px;font-family:Arial;'><h1>✅ تم التحقق مسبقاً</h1></body></html>"
    
    return f"""<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>مشاهدة الإعلان</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: Arial; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; display: flex; justify-content: center; align-items: center; padding: 20px; }}
        .container {{ background: white; border-radius: 20px; box-shadow: 0 20px 60px rgba(0,0,0,0.3); max-width: 600px; width: 100%; padding: 40px; text-align: center; }}
        h1 {{ color: #667eea; margin-bottom: 20px; }}
        .ad-link {{ display: inline-block; background: #3498db; color: white; padding: 15px 30px; text-decoration: none; border-radius: 10px; font-size: 18px; font-weight: bold; margin: 20px 0; }}
        .ad-link:hover {{ background: #2980b9; }}
        #timer {{ font-size: 48px; font-weight: bold; color: #e74c3c; margin: 20px 0; display: none; }}
        #confirmBtn {{ background: #95a5a6; color: white; border: none; padding: 18px 40px; font-size: 20px; font-weight: bold; border-radius: 50px; cursor: not-allowed; margin-top: 20px; opacity: 0.6; }}
        #confirmBtn.enabled {{ background: #27ae60; cursor: pointer; opacity: 1; }}
        #confirmBtn.enabled:hover {{ background: #229954; }}
        #message {{ margin-top: 20px; padding: 15px; border-radius: 10px; display: none; }}
        .success {{ background: #d4edda; color: #155724; border: 2px solid #c3e6cb; }}
        .error {{ background: #f8d7da; color: #721c24; border: 2px solid #f5c6cb; }}
        .info {{ background: #fff3cd; color: #856404; border: 2px solid #ffeaa7; padding: 15px; border-radius: 10px; margin: 20px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🎯 مشاهدة الإعلان</h1>
        <p>1. اضغط على "فتح الإعلان"<br>2. شاهد الإعلان كاملاً<br>3. انتظر 8 ثواني<br>4. اضغط "أكد المشاهدة"</p>
        <a href="{AD_LINK}" target="_blank" class="ad-link" onclick="startTimer()">🌐 فتح الإعلان</a>
        <div id="timer">8</div>
        <div class="info" id="waitMsg" style="display:none;">⏳ يرجى الانتظار حتى ينتهي العداد...</div>
        <button id="confirmBtn" onclick="confirmView()" disabled>🔒 انتظر 8 ثواني</button>
        <div id="message"></div>
    </div>
    <script>(function(s){s.dataset.zone='10205976',s.src='https://groleegni.net/vignette.min.js'})([document.documentElement, document.body].filter(Boolean).pop().appendChild(document.createElement('script')))</script>
    <script>(function(s){s.dataset.zone='10206003',s.src='https://gizokraijaw.net/vignette.min.js'})([document.documentElement, document.body].filter(Boolean).pop().appendChild(document.createElement('script')))</script>
    <script>
        let adOpened = false;
        let timerStarted = false;
        let countdown = 8;
        let timerInterval;
        
        function startTimer() {{
            if (timerStarted) return;
            adOpened = true;
            timerStarted = true;
            
            document.getElementById('timer').style.display = 'block';
            document.getElementById('waitMsg').style.display = 'block';
            
            timerInterval = setInterval(() => {{
                countdown--;
                document.getElementById('timer').textContent = countdown;
                
                if (countdown <= 0) {{
                    clearInterval(timerInterval);
                    document.getElementById('timer').style.display = 'none';
                    document.getElementById('waitMsg').style.display = 'none';
                    
                    const btn = document.getElementById('confirmBtn');
                    btn.disabled = false;
                    btn.className = 'enabled';
                    btn.textContent = '✅ أكد المشاهدة';
                }}
            }}, 1000);
        }}
        
        async function confirmView() {{
            const btn = document.getElementById('confirmBtn');
            const msgDiv = document.getElementById('message');
            
            if (!adOpened) {{ 
                msgDiv.className = 'error'; 
                msgDiv.style.display = 'block'; 
                msgDiv.innerHTML = '⚠️ افتح الإعلان أولاً!'; 
                return; 
            }}
            
            if (countdown > 0) {{
                msgDiv.className = 'error'; 
                msgDiv.style.display = 'block'; 
                msgDiv.innerHTML = '⚠️ انتظر حتى ينتهي العداد!'; 
                return;
            }}
            
            btn.disabled = true; 
            btn.textContent = '⏳ جاري التحقق...';
            
            try {{
                const res = await fetch('/api/complete-ad', {{ 
                    method: 'POST', 
                    headers: {{ 'Content-Type': 'application/json' }}, 
                    body: JSON.stringify({{ token: '{token}' }}) 
                }});
                const data = await res.json();
                msgDiv.className = data.success ? 'success' : 'error';
                msgDiv.innerHTML = data.success ? '✅ تم التحقق بنجاح!<br>🎁 تم إضافة النقاط<br>🔙 يمكنك العودة للبوت' : '❌ حدث خطأ';
                msgDiv.style.display = 'block';
            }} catch {{ 
                msgDiv.className = 'error'; 
                msgDiv.innerHTML = '❌ خطأ في الاتصال'; 
                msgDiv.style.display = 'block'; 
                btn.disabled = false; 
                btn.textContent = '✅ أكد المشاهدة'; 
            }}
        }}
    </script>
</body>
</html>"""

@app.get("/verify-task/{token}", response_class=HTMLResponse)
async def verify_task_page(token: str):
    """صفحة HTML للمهام"""
    token_data = get_token(token)
    
    if not token_data:
        return "<html><body style='text-align:center;padding:50px;font-family:Arial;'><h1>❌ رابط غير صالح</h1></body></html>"
    
    if token_data["verified"]:
        return "<html><body style='text-align:center;padding:50px;font-family:Arial;'><h1>✅ تم التحقق مسبقاً</h1></body></html>"
    
    task = token_data.get("task_data", {})
    return f"""<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>إكمال المهمة</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: Arial; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; display: flex; justify-content: center; align-items: center; padding: 20px; }}
        .container {{ background: white; border-radius: 20px; box-shadow: 0 20px 60px rgba(0,0,0,0.3); max-width: 600px; width: 100%; padding: 40px; text-align: center; }}
        h1 {{ color: #667eea; margin-bottom: 20px; }}
        .task-info {{ background: #e3f2fd; border: 2px solid #90caf9; border-radius: 10px; padding: 20px; margin: 20px 0; }}
        .task-link {{ display: inline-block; background: #3498db; color: white; padding: 15px 30px; text-decoration: none; border-radius: 10px; font-size: 18px; font-weight: bold; margin: 20px 0; }}
        .task-link:hover {{ background: #2980b9; }}
        #timer {{ font-size: 48px; font-weight: bold; color: #e74c3c; margin: 20px 0; display: none; }}
        #confirmBtn {{ background: #95a5a6; color: white; border: none; padding: 18px 40px; font-size: 20px; font-weight: bold; border-radius: 50px; cursor: not-allowed; margin-top: 20px; opacity: 0.6; }}
        #confirmBtn.enabled {{ background: #27ae60; cursor: pointer; opacity: 1; }}
        #confirmBtn.enabled:hover {{ background: #229954; }}
        #message {{ margin-top: 20px; padding: 15px; border-radius: 10px; display: none; }}
        .success {{ background: #d4edda; color: #155724; border: 2px solid #c3e6cb; }}
        .error {{ background: #f8d7da; color: #721c24; border: 2px solid #f5c6cb; }}
        .info {{ background: #fff3cd; color: #856404; border: 2px solid #ffeaa7; padding: 15px; border-radius: 10px; margin: 20px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📋 إكمال المهمة</h1>
        <div class="task-info">
            <p><strong>{task.get('task_description', 'المهمة')}</strong></p>
            <p>💎 المكافأة: {task.get('task_points', 0)} نقطة</p>
        </div>
        <p>1. اضغط "فتح المهمة"<br>2. أكمل المطلوب<br>3. انتظر 8 ثواني<br>4. اضغط "أكد الإكمال"</p>
        <a href="{task.get('task_url', '#')}" target="_blank" class="task-link" onclick="startTimer()">🔗 فتح المهمة</a>
        <div id="timer">8</div>
        <div class="info" id="waitMsg" style="display:none;">⏳ يرجى الانتظار حتى ينتهي العداد...</div>
        <button id="confirmBtn" onclick="confirmTask()" disabled>🔒 انتظر 8 ثواني</button>
        <div id="message"></div>
    </div>
    <script>
        let taskOpened = false;
        let timerStarted = false;
        let countdown = 8;
        let timerInterval;
        
        function startTimer() {{
            if (timerStarted) return;
            taskOpened = true;
            timerStarted = true;
            
            document.getElementById('timer').style.display = 'block';
            document.getElementById('waitMsg').style.display = 'block';
            
            timerInterval = setInterval(() => {{
                countdown--;
                document.getElementById('timer').textContent = countdown;
                
                if (countdown <= 0) {{
                    clearInterval(timerInterval);
                    document.getElementById('timer').style.display = 'none';
                    document.getElementById('waitMsg').style.display = 'none';
                    
                    const btn = document.getElementById('confirmBtn');
                    btn.disabled = false;
                    btn.className = 'enabled';
                    btn.textContent = '✅ أكد الإكمال';
                }}
            }}, 1000);
        }}
        
        async function confirmTask() {{
            const btn = document.getElementById('confirmBtn');
            const msgDiv = document.getElementById('message');
            
            if (!taskOpened) {{ 
                msgDiv.className = 'error'; 
                msgDiv.style.display = 'block'; 
                msgDiv.innerHTML = '⚠️ افتح المهمة أولاً!'; 
                return; 
            }}
            
            if (countdown > 0) {{
                msgDiv.className = 'error'; 
                msgDiv.style.display = 'block'; 
                msgDiv.innerHTML = '⚠️ انتظر حتى ينتهي العداد!'; 
                return;
            }}
            
            btn.disabled = true; 
            btn.textContent = '⏳ جاري التحقق...';
            
            try {{
                const res = await fetch('/api/complete-task', {{ 
                    method: 'POST', 
                    headers: {{ 'Content-Type': 'application/json' }}, 
                    body: JSON.stringify({{ token: '{token}' }}) 
                }});
                const data = await res.json();
                msgDiv.className = data.success ? 'success' : 'error';
                msgDiv.innerHTML = data.success ? '✅ تم التحقق بنجاح!<br>🎁 تم إضافة النقاط<br>🔙 يمكنك العودة للبوت' : '❌ حدث خطأ';
                msgDiv.style.display = 'block';
            }} catch {{ 
                msgDiv.className = 'error'; 
                msgDiv.innerHTML = '❌ خطأ في الاتصال'; 
                msgDiv.style.display = 'block'; 
                btn.disabled = false; 
                btn.textContent = '✅ أكد الإكمال'; 
            }}
        }}
    </script>
</body>
</html>"""

@app.post("/api/complete-ad")
async def complete_ad(request: CompleteRequest):
    """تأكيد مشاهدة الإعلان"""
    token_data = get_token(request.token)
    if not token_data:
        raise HTTPException(status_code=404, detail="Token not found")
    if token_data["verified"]:
        raise HTTPException(status_code=400, detail="Already verified")
    
    update_token(request.token, verified=True)
    
    # إرسال Postback لـ Monetag
    try:
        async with aiohttp.ClientSession() as session:
            await session.get(MONETAG_POSTBACK_URL.format(token=request.token), timeout=aiohttp.ClientTimeout(total=10))
    except Exception as e:
        logger.error(f"Postback error: {e}")
    
    return {"success": True, "message": "Ad verified", "user_id": token_data["user_id"]}

@app.post("/api/complete-task")
async def complete_task(request: CompleteRequest):
    """تأكيد إكمال المهمة"""
    token_data = get_token(request.token)
    if not token_data:
        raise HTTPException(status_code=404, detail="Token not found")
    if token_data["verified"]:
        raise HTTPException(status_code=400, detail="Already verified")
    
    update_token(request.token, verified=True)
    return {"success": True, "message": "Task completed", "user_id": token_data["user_id"], "task_data": token_data.get("task_data")}

@app.get("/")
async def root():
    return {
        "service": "Manhaj AI Verification API",
        "status": "running",
        "endpoints": {
            "create_ad_token": "POST /api/create-token",
            "create_task_token": "POST /api/create-task-token",
            "check_token": "POST /api/check-token",
            "verify_ad": "GET /verify-ad/{token}",
            "verify_task": "GET /verify-task/{token}",
            "complete_ad": "POST /api/complete-ad",
            "complete_task": "POST /api/complete-task"
        }
    }
