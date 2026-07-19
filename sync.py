import httpx
import os
from dotenv import load_dotenv
import database

def load_cookie():
    load_dotenv()
    cookie = os.getenv("NETEASE_COOKIE", "")
    return cookie

def fetch_liked_songs(cookie: str) -> list:
    """获取用户喜欢的歌曲列表"""
    headers = {
        "Cookie": cookie,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://music.163.com/"
    }

    songs = []
    offset = 0
    limit = 100

    print("正在获取喜欢的歌曲...")

    try:
        while True:
            url = f"https://music.163.com/api/song/like/get?uid=0&offset={offset}&limit={limit}"
            response = httpx.get(url, headers=headers, timeout=15)
            data = response.json()

            if data.get("code") != 200:
                print(f"API返回错误: {data.get('msg', 'Unknown error')}")
                break

            ids = data.get("ids", [])
            if not ids:
                break

            for netease_id in ids:
                songs.append({
                    "name": "",
                    "artist": "",
                    "netease_id": str(netease_id)
                })

            print(f"获取到 {len(songs)} 首歌曲的ID")

            if len(ids) < limit:
                break

            offset += limit

    except httpx.HTTPStatusError as e:
        print(f"HTTP错误: {e.response.status_code}")
        return []
    except Exception as e:
        print(f"请求失败: {e}")
        return []

    if songs:
        print(f"获取到 {len(songs)} 首歌曲的ID，开始获取详细信息...")
        songs = fetch_song_details(songs, headers)

    return songs

def fetch_song_details(songs: list, headers: dict) -> list:
    """获取歌曲详细信息"""
    if not songs:
        return []

    for i in range(0, len(songs), 50):
        batch = songs[i:i+50]
        ids = ",".join([s["netease_id"] for s in batch])
        url = f"https://music.163.com/api/song/detail?ids={ids}"

        try:
            response = httpx.get(url, headers=headers, timeout=15)
            data = response.json()

            if data.get("code") == 200:
                details = data.get("songs", [])
                detail_map = {str(song["id"]): song for song in details}

                for song in batch:
                    netease_id = song["netease_id"]
                    if netease_id in detail_map:
                        info = detail_map[netease_id]
                        song["name"] = info.get("name", "Unknown")
                        artists = info.get("artists", info.get("ar", []))
                        song["artist"] = ", ".join([ar.get("name", "") for ar in artists])

        except Exception as e:
            print(f"获取歌曲详情失败: {e}")

    return songs

def get_user_id(cookie: str) -> str:
    """获取当前登录用户ID"""
    headers = {
        "Cookie": cookie,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://music.163.com/"
    }

    url = "https://music.163.com/api/user/playlist?uid=0&limit=1"

    try:
        response = httpx.get(url, headers=headers, timeout=15)
        data = response.json()

        if data.get("code") == 200:
            playlists = data.get("playlist", [])
            if playlists:
                creator = playlists[0].get("creator", {})
                return str(creator.get("userId", ""))

    except Exception as e:
        print(f"获取用户ID失败: {e}")
        return ""

    return ""

def fetch_playlists(cookie: str, include_favorites=False) -> list:
    """获取用户的歌单列表"""
    headers = {
        "Cookie": cookie,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://music.163.com/"
    }

    url = "https://music.163.com/api/user/playlist?uid=0&limit=100"

    try:
        response = httpx.get(url, headers=headers, timeout=15)
        data = response.json()

        if data.get("code") != 200:
            print(f"API返回错误: {data.get('msg', 'Unknown error')}")
            return []

        playlists = data.get("playlist", [])
        result = []

        user_id = ""
        if not include_favorites:
            user_id = get_user_id(cookie)
            print(f"当前用户ID: {user_id}")

        for p in playlists:
            creator = p.get("creator", {})
            creator_id = str(creator.get("userId", ""))

            if not include_favorites and user_id and creator_id != user_id:
                continue

            result.append({
                "id": p.get("id"),
                "name": p.get("name"),
                "trackCount": p.get("trackCount"),
                "description": p.get("description", ""),
                "creator": creator.get("nickname", "")
            })

        return result

    except Exception as e:
        print(f"获取歌单列表失败: {e}")
        return []

def fetch_playlist_songs(cookie: str, playlist_id: int) -> list:
    """获取指定歌单的歌曲"""
    headers = {
        "Cookie": cookie,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://music.163.com/"
    }

    songs = []
    offset = 0
    limit = 100

    print(f"正在获取歌单ID {playlist_id} 的歌曲...")

    while True:
        url = f"https://music.163.com/api/playlist/detail?id={playlist_id}&offset={offset}&limit={limit}"

        try:
            response = httpx.get(url, headers=headers, timeout=15)
            data = response.json()

            if data.get("code") != 200:
                print(f"API返回错误: {data.get('msg', 'Unknown error')}")
                break

            tracks = data.get("result", {}).get("tracks", [])
            if not tracks:
                break

            for track in tracks:
                songs.append({
                    "name": track.get("name", "Unknown"),
                    "artist": ", ".join([ar.get("name", "") for ar in track.get("artists", [])]),
                    "netease_id": str(track.get("id", ""))
                })

            if len(tracks) < limit:
                break

            offset += limit

        except Exception as e:
            print(f"获取歌单歌曲失败: {e}")
            break

    print(f"获取到 {len(songs)} 首歌曲")
    return songs

def sync_playlist(playlist_id: int):
    """同步指定歌单"""
    database.init_db()

    cookie = load_cookie()
    if not cookie:
        print("错误: 未找到网易云 Cookie 配置")
        return

    print(f"已读取 NETEASE_COOKIE: {cookie[:20]}...")

    try:
        songs = fetch_playlist_songs(cookie, playlist_id)
        print(f"获取到 {len(songs)} 首歌曲")

        if songs:
            print("正在保存到数据库...")
            success_count = 0
            for song in songs:
                try:
                    database.insert_song(
                        song["name"],
                        song["artist"],
                        song["netease_id"]
                    )
                    success_count += 1
                except Exception as e:
                    print(f"保存歌曲 '{song.get('name', 'Unknown')}' 失败: {e}")

            print(f"成功保存 {success_count} 首歌曲到数据库")
            print(f"数据库中共有 {database.get_song_count()} 首歌曲")

        return songs
    except Exception as e:
        print(f"同步失败: {e}")
        return []

def sync_liked_songs():
    """同步用户喜欢的歌曲"""
    database.init_db()

    cookie = load_cookie()
    if not cookie:
        print("错误: 未找到网易云 Cookie 配置")
        return

    print(f"已读取 NETEASE_COOKIE: {cookie[:20]}...")

    try:
        songs = fetch_liked_songs(cookie)
        print(f"获取到 {len(songs)} 首歌曲")

        if songs:
            print("正在保存到数据库...")
            success_count = 0
            for song in songs:
                try:
                    database.insert_song(
                        song["name"],
                        song["artist"],
                        song["netease_id"]
                    )
                    success_count += 1
                except Exception as e:
                    print(f"保存歌曲 '{song.get('name', 'Unknown')}' 失败: {e}")

            print(f"成功保存 {success_count} 首歌曲到数据库")
            print(f"数据库中共有 {database.get_song_count()} 首歌曲")

        return songs
    except Exception as e:
        print(f"同步失败: {e}")
        return []

def get_song_play_url(netease_id: str, cookie: str = "") -> str:
    """
    获取网易云歌曲的播放URL（优化版）
    尝试多种方式获取播放链接
    
    参数:
        netease_id: 网易云歌曲ID
        cookie: 可选的网易云Cookie（没有的话也能获取部分歌曲）
        
    返回:
        str: 播放URL，失败返回空字符串
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://music.163.com/"
    }
    
    if cookie:
        headers["Cookie"] = cookie
    
    # 尝试多种音质
    levels = ["exhigh", "higher", "standard", "lossless"]
    
    for level in levels:
        try:
            url = f"https://music.163.com/api/song/url?id={netease_id}&level={level}"
            response = httpx.get(url, headers=headers, timeout=15)
            data = response.json()
            
            if data.get("code") == 200:
                songs = data.get("data", [])
                if songs and len(songs) > 0:
                    play_url = songs[0].get("url", "")
                    if play_url:
                        print(f"获取播放链接成功 (音质: {level})")
                        return play_url
        
        except Exception as e:
            print(f"获取播放URL (音质: {level}) 失败: {e}")
            continue
    
    # 如果都失败了，尝试另一个接口
    try:
        url = f"https://music.163.com/api/song/enhance/player/url?ids=[{netease_id}]&br=320000"
        response = httpx.get(url, headers=headers, timeout=15)
        data = response.json()
        
        if data.get("code") == 200:
            songs = data.get("data", [])
            if songs and len(songs) > 0:
                play_url = songs[0].get("url", "")
                if play_url:
                    print(f"获取播放链接成功 (备用接口)")
                    return play_url
    
    except Exception as e:
        print(f"备用接口获取失败: {e}")
    
    print("所有方式都无法获取播放链接")
    return ""

def sync_all_my_playlists():
    """同步所有自己创建的歌单"""
    database.init_db()

    cookie = load_cookie()
    if not cookie:
        print("错误: 未找到网易云 Cookie 配置")
        return

    print(f"已读取 NETEASE_COOKIE: {cookie[:20]}...")

    playlists = fetch_playlists(cookie)
    print(f"\n找到 {len(playlists)} 个自己创建的歌单")

    total_songs = 0
    total_added = 0

    for playlist in playlists:
        print(f"\n正在同步歌单: {playlist['name']} (ID: {playlist['id']})")
        print(f"歌曲数: {playlist['trackCount']}")

        try:
            songs = fetch_playlist_songs(cookie, playlist['id'])
            total_songs += len(songs)

            if songs:
                print("正在保存到数据库...")
                success_count = 0
                for song in songs:
                    try:
                        database.insert_song(
                            song["name"],
                            song["artist"],
                            song["netease_id"]
                        )
                        success_count += 1
                    except Exception:
                        pass

                total_added += success_count
                print(f"成功添加 {success_count} 首新歌曲")

        except Exception as e:
            print(f"同步歌单失败: {e}")

    print(f"\n=== 同步完成 ===")
    print(f"共处理 {len(playlists)} 个歌单")
    print(f"共包含 {total_songs} 首歌曲")
    print(f"新增 {total_added} 首歌曲到数据库")
    print(f"数据库中共有 {database.get_song_count()} 首歌曲")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        if sys.argv[1] == "list":
            cookie = load_cookie()
            playlists = fetch_playlists(cookie)
            print("\n你的歌单列表:")
            print("=" * 60)
            for p in playlists:
                print(f"ID: {p['id']}")
                print(f"名称: {p['name']}")
                print(f"歌曲数: {p['trackCount']}")
                if p['description']:
                    desc = p['description'].encode('utf-8', errors='replace').decode('utf-8')
                    print(f"描述: {desc}")
                print("-" * 60)
        elif sys.argv[1] == "all":
            sync_all_my_playlists()
        elif sys.argv[1].isdigit():
            playlist_id = int(sys.argv[1])
            sync_playlist(playlist_id)
        else:
            print("用法:")
            print("  python sync.py          # 同步喜欢的歌曲")
            print("  python sync.py list     # 列出自己创建的歌单")
            print("  python sync.py all      # 同步所有自己创建的歌单")
            print("  python sync.py <歌单ID>  # 同步指定歌单")
    else:
        sync_liked_songs()