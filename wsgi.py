# ในไฟล์ wsgi.py
from app import app # <-- แก้ไข 'app' ตัวแรกให้เป็นชื่อไฟล์ .py หลักของคุณ

if __name__ == "__main__":
    app.run()