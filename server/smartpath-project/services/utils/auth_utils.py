"""
פונקציות עזר להצפנת סיסמאות ואימות.
משתמש ב-bcrypt דרך ספריית flask-bcrypt או bcrypt ישירות.
"""
import bcrypt


def hash_password(password: str) -> str:
    """
    מקבל סיסמה בטקסט נקי, מחזיר hash מוצפן.
    """
    # bcrypt מצפה bytes, ומחזיר bytes
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')


def verify_password(password: str, hashed: str) -> bool:
    """
    משווה סיסמה שהזין המשתמש מול ה-hash השמור במסד.
    מחזיר True אם הסיסמה תואמת.
    """
    password_bytes = password.encode('utf-8')
    hashed_bytes = hashed.encode('utf-8')
    return bcrypt.checkpw(password_bytes, hashed_bytes)
