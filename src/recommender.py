import os
import random
from dotenv import load_dotenv
from src.weather_service import get_weather
from src.sentiment_analysis import analyze_sentiment
from src.preference_store import save_preference, get_preferences
from datetime import datetime
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import fetch_all_songs, get_random_song, get_song_count

# 加载环境变量
load_dotenv()

class MusicRecommender:
    """音乐推荐核心类"""
    
    def __init__(self):
        self.weather_api_key = os.getenv("WEATHER_API_KEY")
        self.city = os.getenv("CITY", "Beijing")
        
    def get_context(self):
        """获取当前上下文"""
        try:
            weather_data = get_weather(self.weather_api_key, self.city)
        except:
            # 在测试环境下返回模拟数据
            weather_data = {
                "temperature": 25,
                "humidity": 40,
                "description": "晴"
            }
        return {
            "weather": weather_data,
            "date": datetime.now(),
            "time": datetime.now().time()
        }
    
    def recommend(self, user_input: str = ""):
        """生成音乐推荐 - 返回完整的歌曲信息字典"""
        # 获取当前上下文
        context = self.get_context()
        
        # 分析用户情绪
        sentiment = analyze_sentiment(user_input)
        
        # 从数据库获取歌曲
        song = self._get_song_from_db(context, sentiment)
        
        if not song:
            return {
                "name": "暂无推荐",
                "artist": "系统",
                "netease_id": "",
                "local_path": None,
                "info": "数据库中没有歌曲，请先添加歌曲"
            }
        
        # 如果配置了阿里云大模型，则使用大模型优化推荐
        if os.getenv("ALIYUN_LLM_API_KEY"):
            try:
                from src.aliyun_llm import generate_music_recommendation
                llm_recommendation = generate_music_recommendation({
                    "weather": context["weather"],
                    "date": context["date"],
                    "time": context["time"],
                    "sentiment": sentiment,
                    "user_input": user_input
                })
                
                # 如果大模型返回有效推荐，则使用大模型推荐结果
                if llm_recommendation and isinstance(llm_recommendation, dict):
                    song = llm_recommendation
            except ImportError:
                print("警告: 未找到aliyun_llm模块，请确保文件存在")
            except Exception as e:
                print(f"大模型推荐失败: {e}")
        
        # 保存偏好历史
        if user_input:
            save_preference({
                "input": user_input,
                "sentiment": sentiment,
                "recommendation": f"{song['name']} - {song['artist']}",
                "timestamp": datetime.now().isoformat()
            })
            
        return song
    
    def _get_song_from_db(self, context, sentiment):
        """从数据库获取合适的歌曲"""
        all_songs = fetch_all_songs()
        
        if not all_songs:
            return None
        
        weather_desc = context["weather"]["description"].lower()
        sentiment_val = sentiment["polarity"]
        
        # 简单的基于上下文的筛选逻辑
        filtered_songs = all_songs
        
        # 这里可以根据实际需求添加更多筛选逻辑
        # 比如根据情绪、天气等条件筛选
        
        # 随机从筛选结果中选择一首
        return random.choice(filtered_songs)
    
    def search_song(self, keyword: str) -> dict:
        """
        在数据库中搜索歌曲
        返回匹配的歌曲信息，没有找到返回None
        
        参数:
            keyword: 搜索关键词（歌曲名或歌手名）
            
        返回:
            dict: 歌曲信息，没有找到返回None
        """
        all_songs = fetch_all_songs()
        
        if not all_songs:
            return None
        
        # 转换为小写进行模糊匹配
        keyword_lower = keyword.lower()
        
        for song in all_songs:
            song_name = song.get("name", "").lower()
            artist = song.get("artist", "").lower()
            
            # 检查歌曲名或歌手名是否包含关键词
            if keyword_lower in song_name or keyword_lower in artist:
                return song
        
        return None

if __name__ == "__main__":
    recommender = MusicRecommender()
    result = recommender.recommend("今天心情很好")
    print(f"推荐: {result['name']} - {result['artist']}")