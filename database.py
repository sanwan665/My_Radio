import sqlite3
import random
from pathlib import Path

# 数据库路径（可配置）
DB_PATH = Path("music.db")

def init_db():
    """初始化数据库，创建 songs 表"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 创建 songs 表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS songs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            artist TEXT NOT NULL,
            netease_id TEXT NOT NULL UNIQUE,
            local_path TEXT
        )
    ''')
    
    conn.commit()
    conn.close()
    print(f"数据库已初始化，表 'songs' 创建成功。数据库路径: {DB_PATH}")

def insert_song(name, artist, netease_id, local_path=None):
    """插入歌曲数据到数据库"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute('''
            INSERT INTO songs (name, artist, netease_id, local_path)
            VALUES (?, ?, ?, ?)
        ''', (name, artist, netease_id, local_path))

        conn.commit()
    except sqlite3.IntegrityError:
        pass
    finally:
        conn.close()

def fetch_all_songs():
    """查询所有歌曲数据"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM songs")
    songs = cursor.fetchall()
    
    conn.close()
    return [dict(row) for row in songs]

def get_random_song():
    """随机获取一首歌曲"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM songs ORDER BY RANDOM() LIMIT 1")
    song = cursor.fetchone()
    
    conn.close()
    return dict(song) if song else None

def search_songs(keyword):
    """根据关键词搜索歌曲"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM songs WHERE name LIKE ? OR artist LIKE ?", 
                  (f"%{keyword}%", f"%{keyword}%"))
    songs = cursor.fetchall()
    
    conn.close()
    return [dict(row) for row in songs]

def update_song_path(netease_id, local_path):
    """更新歌曲的本地路径"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("UPDATE songs SET local_path = ? WHERE netease_id = ?", 
                  (local_path, netease_id))
    
    conn.commit()
    conn.close()

def get_song_count():
    """获取歌曲总数"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM songs")
    count = cursor.fetchone()[0]
    
    conn.close()
    return count

def add_sample_songs():
    """添加示例歌曲（用于测试）"""
    sample_songs = [
        {"name": "晴天", "artist": "周杰伦", "netease_id": "186016"},
        {"name": "小幸运", "artist": "田馥甄", "netease_id": "32507038"},
        {"name": "平凡之路", "artist": "朴树", "netease_id": "28287132"},
        {"name": "起风了", "artist": "买辣椒也用券", "netease_id": "523251118"},
        {"name": "夜曲", "artist": "周杰伦", "netease_id": "185674"},
        {"name": "稻香", "artist": "周杰伦", "netease_id": "185692"},
        {"name": "成都", "artist": "赵雷", "netease_id": "436514312"},
        {"name": "童话", "artist": "光良", "netease_id": "287174"},
        {"name": "后来", "artist": "刘若英", "netease_id": "33894312"},
        {"name": "告白气球", "artist": "周杰伦", "netease_id": "415792804"}
    ]
    
    existing_count = get_song_count()
    if existing_count > 0:
        print(f"数据库中已有 {existing_count} 首歌曲，跳过添加示例歌曲。")
        return
    
    for song in sample_songs:
        insert_song(song["name"], song["artist"], song["netease_id"])
    
    print("已添加 10 首示例歌曲到数据库。")

if __name__ == "__main__":
    # 初始化数据库
    init_db()
    # 添加示例歌曲
    add_sample_songs()