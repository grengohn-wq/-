# storage_utils.py - التخزين المؤقت في الذاكرة (يمنع خطأ 500 على Vercel)

from datetime import datetime
from typing import Optional, Dict

# القاموس الذي سيحتوي على بيانات التوكن في الذاكرة (غير دائم)
TOKEN_STORE: Dict[str, Dict] = {}

def create_new_token(user_id: int, token: str) -> Dict:
    """ إنشاء توكن جديد وحفظه في الذاكرة """
    token_data = {
        "user_id": user_id,
        "token": token,
        "verified": False,
        "created_at": datetime.now().isoformat(),
        "verified_at": None
    }
    
    global TOKEN_STORE 
    TOKEN_STORE[token] = token_data
    return token_data

def update_token_status(token: str, verified: bool = True) -> bool:
    """ تحديث حالة التوكن في الذاكرة """
    global TOKEN_STORE
    if token not in TOKEN_STORE:
        return False
    
    TOKEN_STORE[token]["verified"] = verified
    if verified:
        TOKEN_STORE[token]["verified_at"] = datetime.now().isoformat()
    
    return True

def get_token_data(token: str) -> Optional[Dict]:
    """ جلب بيانات توكن معين من الذاكرة """
    return TOKEN_STORE.get(token)

def initialize_db():
    """ لا حاجة لإنشاء ملفات، الدالة فارغة. """
    pass
