import sqlite3
import os
from datetime import datetime

# 数据库文件路径
DB_PATH = "preferences.db"

def init_db():
    """初始化数据库"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS preferences (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_input TEXT,
        sentiment_polarity REAL,
        sentiment_subjectivity REAL,
        recommendation TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)
    conn.commit()
    conn.close()

def save_preference(data: dict):
    """保存用户偏好"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
    INSERT INTO preferences (
        user_input, 
        sentiment_polarity, 
        sentiment_subjectivity, 
        recommendation
    ) VALUES (?, ?, ?, ?)
    """, (
        data["input"],
        data["sentiment"]["polarity"],
        data["sentiment"]["subjectivity"],
        data["recommendation"]
    ))
    
    conn.commit()
    conn.close()

def get_preferences(limit: int = 10):
    """获取历史偏好"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM preferences ORDER BY timestamp DESC LIMIT ?", (limit,))
    results = cursor.fetchall()
    
    conn.close()
    return [dict(row) for row in results]

# 初始化数据库
if not os.path.exists(DB_PATH):
    init_db()