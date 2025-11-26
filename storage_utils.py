# mini_app/storage_utils.py

"""
storage_utils.py - إدارة تخزين بيانات التوكن (In-Memory Cache)

⚠️ تنبيه هام: هذا التخزين غير دائم. 
البيانات ستبقى فقط ما دامت نسخة الدالة السيرفرليس نشطة. 
يجب الانتقال إلى MongoDB لبيانات دائمة.
"""

import json
import os
import uuid
from datetime import datetime
from typing import Optional, Dict

# المتغير العالمي الذي سيحفظ التوكنات في الذاكرة
# سيتم تهيئته مرة واحدة عند "التشغيل البارد" لنسخة الدالة على Vercel
_tokens_cache: Dict[str, Dict] = {} 

# تم حذف initialize_db() و TOKENS_FILE

def load_tokens() -> Dict:
    """تحميل التوكنات من الذاكرة."""
    # نستخدم النسخ لتجنب مشاكل التزامن البسيطة
    return _tokens_cache.copy()

def save_tokens(tokens: Dict):
    """حفظ التوكنات في الذاكرة (تحديث الكاش العالمي)."""
    global _tokens_cache
    _tokens_cache = tokens

def create_new_token(user_id: int, token: str) -> Dict:
    """إنشاء توكن جديد وحفظه"""
    tokens = load_tokens()
    
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
