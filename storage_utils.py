"""
storage_utils.py - إدارة تخزين بيانات التوكن

⚠️ تحذير هام:
استخدام ملف JSON للتخزين هو حل مؤقت للتطوير فقط.
في بيئة الإنتاج على Vercel، يجب استبدال هذا بقاعدة بيانات خارجية مثل:
- MongoDB Atlas
- PostgreSQL (Supabase/Neon)
- Redis
لأن Vercel Serverless Functions لا تحتفظ بالملفات المحلية بين الاستدعاءات.
"""

import json
import os
from datetime import datetime
from typing import Optional, Dict

TOKENS_FILE = "tokens_data.json"

def initialize_db():
    """إنشاء ملف التخزين إذا لم يكن موجوداً"""
    if not os.path.exists(TOKENS_FILE):
        with open(TOKENS_FILE, 'w', encoding='utf-8') as f:
            json.dump({}, f)

def load_tokens() -> Dict:
    """تحميل جميع التوكنات من الملف"""
    try:
        with open(TOKENS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_tokens(tokens: Dict):
    """حفظ جميع التوكنات في الملف"""
    with open(TOKENS_FILE, 'w', encoding='utf-8') as f:
        json.dump(tokens, f, ensure_ascii=False, indent=2)

def create_new_token(user_id: int, token: str, task_data: Dict = None) -> Dict:
    """
    إنشاء توكن جديد وحفظه
    
    Args:
        user_id: معرف المستخدم من تليجرام
        token: التوكن الفريد المولد
        task_data: بيانات المهمة (اختياري) - يحتوي على task_id, task_url, task_description, task_points
    
    Returns:
        بيانات التوكن المحفوظ
    """
    tokens = load_tokens()
    
    token_data = {
        "user_id": user_id,
        "token": token,
        "verified": False,
        "created_at": datetime.now().isoformat(),
        "verified_at": None
    }
    
    # إضافة بيانات المهمة إذا كانت موجودة
    if task_data:
        token_data["task_data"] = task_data
    
    tokens[token] = token_data
    save_tokens(tokens)
    
    return token_data

def update_token_status(token: str, verified: bool = True) -> bool:
    """
    تحديث حالة التوكن
    
    Args:
        token: التوكن المراد تحديثه
        verified: حالة التحقق الجديدة
    
    Returns:
        True إذا تم التحديث بنجاح، False إذا لم يوجد التوكن
    """
    tokens = load_tokens()
    
    if token not in tokens:
        return False
    
    tokens[token]["verified"] = verified
    if verified:
        tokens[token]["verified_at"] = datetime.now().isoformat()
    
    save_tokens(tokens)
    return True

def get_token_data(token: str) -> Optional[Dict]:
    """
    استرجاع بيانات توكن محدد
    
    Args:
        token: التوكن المراد البحث عنه
    
    Returns:
        بيانات التوكن أو None إذا لم يوجد
    """
    tokens = load_tokens()
    return tokens.get(token)

# تهيئة قاعدة البيانات عند استيراد الملف
initialize_db()
