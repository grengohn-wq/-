# mini_app/storage_utils.py

"""
storage_utils.py - إدارة تخزين بيانات التوكن

⚠️ تنويه هام: هذه النسخة لن تحفظ البيانات بشكل دائم على Vercel. 
يجب الانتقال إلى قاعدة بيانات خارجية (MongoDB/Supabase) لضمان استمرارية التوكنات.
"""

import json
import os
import uuid
from datetime import datetime
from typing import Optional, Dict

# لا يمكن استخدام ملف محلي في Vercel، لكن نحتفظ بالمتغير لأغراض Local Testing
TOKENS_FILE = "tokens_data.json" 

# تم حذف دالة initialize_db()

def load_tokens() -> Dict:
    """تحميل جميع التوكنات من الملف. يتم تجاهل الخطأ في حالة عدم العثور على ملف (مثل Vercel)."""
    try:
        with open(TOKENS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        # في Vercel، سيتم العودة هنا بـ {}، مما يمنع التعطل.
        return {}

def save_tokens(tokens: Dict):
    """
    حفظ جميع التوكنات في الملف.
    ⚠️ في بيئة Vercel، هذه الدالة ستفشل بصمت غالباً.
    نحتفظ بها لأغراض Local Testing فقط.
    """
    try:
        with open(TOKENS_FILE, 'w', encoding='utf-8') as f:
            json.dump(tokens, f, ensure_ascii=False, indent=2)
    except Exception as e:
        # تجاهل خطأ الكتابة لتجنب تعطل الدالة في بيئة Vercel
        print(f"Ignoring save error on Vercel: {e}")


def create_new_token(user_id: int) -> Dict:
    """إنشاء توكن جديد وحفظه"""
    tokens = load_tokens()
    
    # توليد توكن فريد
    token = str(uuid.uuid4())
    
    token_data = {
        "user_id": user_id,
        "token": token,
        "verified": False,
        "created_at": datetime.now().isoformat(),
        "verified_at": None
    }
    
    tokens[token] = token_data
    save_tokens(tokens)
    
    return token_data

def update_token_status(token: str, verified: bool = True) -> bool:
    """تحديث حالة التوكن"""
    tokens = load_tokens()
    
    if token not in tokens:
        return False
    
    tokens[token]["verified"] = verified
    if verified:
        tokens[token]["verified_at"] = datetime.now().isoformat()
    
    save_tokens(tokens)
    return True

def get_token_data(token: str) -> Optional[Dict]:
    """جلب بيانات توكن معين"""
    tokens = load_tokens()
    return tokens.get(token)
