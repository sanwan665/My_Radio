# -*- coding: utf-8 -*-
"""
网易云音乐开放平台API客户端
用于调用官方API获取推荐等功能
"""

import os
import time
import json
import base64
import hashlib
import httpx
from dotenv import load_dotenv


class NeteaseOpenAPIClient:
    def __init__(self):
        load_dotenv()
        self.app_id = os.getenv("NETEASE_APP_ID", "")
        self.app_secret = os.getenv("NETEASE_APP_SECRET", "")
        self.private_key_str = os.getenv("NETEASE_PRIVATE_KEY", "")
        self.public_key_str = os.getenv("NETEASE_PUBLIC_KEY", "")
        
        self.base_url = "https://openapi.music.163.com"
        self.access_token = None
        self.token_expire_time = 0
        
        # 检查配置是否完整
        self._configured = all([
            self.app_id and self.app_id.strip() != "",
            self.app_secret and self.app_secret.strip() != ""
        ])
        
    def _fix_base64_padding(self, data: str) -> str:
        """修复base64编码的填充问题"""
        data = data.replace(" ", "").replace("\n", "").replace("\r", "")
        # 添加缺失的填充字符
        missing_padding = len(data) % 4
        if missing_padding != 0:
            data += "=" * (4 - missing_padding)
        return data
    
    def _generate_signature(self, params: dict, timestamp: int) -> str:
        """
        生成签名（简化版，不使用RSA）
        按参数名ASCII排序后拼接，然后进行签名
        """
        # 按参数名排序
        sorted_keys = sorted(params.keys())
        param_str = "&".join([f"{k}={params[k]}" for k in sorted_keys])
        param_str += f"&timestamp={timestamp}&appSecret={self.app_secret}"
        
        # SHA256哈希
        h = hashlib.sha256(param_str.encode('utf-8'))
        return h.hexdigest()
    
    def is_configured(self) -> bool:
        """检查是否配置了必要的参数"""
        return self._configured
    
    def get_access_token(self) -> str:
        """
        获取访问Token
        """
        if not self.is_configured():
            print("未配置网易云开放平台")
            return ""
        
        # 检查Token是否还有效
        if self.access_token and time.time() < self.token_expire_time:
            return self.access_token
        
        timestamp = int(time.time() * 1000)
        
        params = {
            "appId": self.app_id,
            "timestamp": timestamp
        }
        
        # 生成签名
        signature = self._generate_signature(params, timestamp)
        params["signature"] = signature
        
        try:
            url = f"{self.base_url}/openapi/getToken"
            response = httpx.post(url, json=params, timeout=15)
            data = response.json()
            
            if data.get("code") == 200:
                self.access_token = data.get("accessToken", "")
                expires_in = data.get("expiresIn", 7200)
                self.token_expire_time = time.time() + expires_in - 60  # 提前60秒过期
                print(f"获取Token成功，有效期: {expires_in}秒")
                return self.access_token
            else:
                print(f"获取Token失败: {data.get('msg', '未知错误')}")
                print(f"响应数据: {data}")
                return ""
                
        except Exception as e:
            print(f"获取Token异常: {e}")
            import traceback
            traceback.print_exc()
            return ""
    
    def _call_api(self, endpoint: str, params: dict = None, method: str = "GET") -> dict:
        """
        调用开放平台API
        """
        token = self.get_access_token()
        if not token:
            return {"code": -1, "msg": "获取Token失败"}
        
        if params is None:
            params = {}
        
        timestamp = int(time.time() * 1000)
        params["timestamp"] = timestamp
        
        headers = {
            "accessToken": token,
            "Content-Type": "application/json"
        }
        
        try:
            url = f"{self.base_url}{endpoint}"
            if method == "GET":
                response = httpx.get(url, params=params, headers=headers, timeout=15)
            else:
                response = httpx.post(url, json=params, headers=headers, timeout=15)
            
            return response.json()
            
        except Exception as e:
            print(f"调用API失败: {e}")
            return {"code": -1, "msg": str(e)}
    
    def get_recommend_playlists(self) -> list:
        """
        获取推荐歌单
        官方API: /openapi/music/basic/recommend/playlist/get
        """
        result = self._call_api("/openapi/music/basic/recommend/playlist/get")
        
        if result.get("code") == 200:
            playlists = result.get("data", [])
            return playlists
        
        print(f"获取推荐歌单失败: {result.get('msg', '未知错误')}")
        return []
    
    def get_recommend_songs(self) -> list:
        """
        获取推荐歌曲
        官方API: /openapi/music/basic/recommend/songlist/get/v2
        """
        result = self._call_api("/openapi/music/basic/recommend/songlist/get/v2")
        
        if result.get("code") == 200:
            songs = result.get("data", [])
            return songs
        
        print(f"获取推荐歌曲失败: {result.get('msg', '未知错误')}")
        return []
    
    def get_similar_songs(self, song_id: str = "") -> list:
        """
        获取相似歌曲
        官方API: /openapi/music/basic/similar/song/list/get/v2
        """
        params = {}
        if song_id:
            params["songId"] = song_id
        
        result = self._call_api("/openapi/music/basic/similar/song/list/get/v2", params)
        
        if result.get("code") == 200:
            songs = result.get("data", [])
            return songs
        
        print(f"获取相似歌曲失败: {result.get('msg', '未知错误')}")
        return []
    
    def search_songs(self, keyword: str, limit: int = 10) -> list:
        """
        搜索歌曲
        （注意：需要看开放平台是否有此接口，没有的话返回空）
        """
        params = {
            "keyword": keyword,
            "limit": limit
        }
        
        # 假设的搜索接口，实际需要根据官方文档调整
        result = self._call_api("/openapi/music/basic/search/song", params, method="POST")
        
        if result.get("code") == 200:
            songs = result.get("data", [])
            return songs
        
        return []


# 全局实例
_openapi_client = None


def get_openapi_client() -> NeteaseOpenAPIClient:
    """获取网易云开放平台客户端实例"""
    global _openapi_client
    if _openapi_client is None:
        _openapi_client = NeteaseOpenAPIClient()
    return _openapi_client


if __name__ == "__main__":
    # 测试
    client = NeteaseOpenAPIClient()
    print(f"是否配置: {client.is_configured()}")
    
    if client.is_configured():
        token = client.get_access_token()
        print(f"Token: {token[:30] if token else 'None'}...")
        
        if token:
            playlists = client.get_recommend_playlists()
            print(f"推荐歌单数: {len(playlists)}")
            
            songs = client.get_recommend_songs()
            print(f"推荐歌曲数: {len(songs)}")
    else:
        print("网易云开放平台未配置，将使用本地数据库推荐")
