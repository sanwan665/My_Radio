# -*- coding: utf-8 -*-
import os
import requests
import json
from typing import Dict, Any, Optional

class LLMClient:
    """通用大模型客户端"""
    
    def __init__(self):
        # 使用用户配置或默认配置（你的API）
        self.api_key = os.getenv("LLM_API_KEY", "sk-112a264bf92c41ea857289453e7565df")
        self.endpoint = os.getenv("LLM_ENDPOINT", "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions")
        self.model = os.getenv("LLM_MODEL", "qwen-plus")
        self.provider = os.getenv("LLM_PROVIDER", "openai").lower()
        
    def is_configured(self) -> bool:
        """检查是否配置了LLM"""
        if not self.api_key or not self.endpoint:
            return False
        if self.api_key in ["your_api_key_here", ""]:
            return False
        if self.endpoint in ["your_endpoint_here", ""]:
            return False
        return True
    
    def call(self, prompt: str, max_tokens: int = 150, temperature: float = 0.7) -> Optional[str]:
        """调用大模型API"""
        if not self.is_configured():
            return None
        
        try:
            if self.provider == "openai" or "api" in self.endpoint.lower():
                return self._call_openai_compatible(prompt, max_tokens, temperature)
            elif self.provider == "anthropic":
                return self._call_anthropic(prompt, max_tokens, temperature)
            else:
                return self._call_openai_compatible(prompt, max_tokens, temperature)
        except Exception as e:
            print(f"LLM调用失败: {e}")
            return None
    
    def _call_openai_compatible(self, prompt: str, max_tokens: int, temperature: float) -> Optional[str]:
        """调用OpenAI兼容的API"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        
        response = requests.post(self.endpoint, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        
        if "choices" in result and len(result["choices"]) > 0:
            return result["choices"][0]["message"]["content"].strip()
        return None
    
    def _call_anthropic(self, prompt: str, max_tokens: int, temperature: float) -> Optional[str]:
        """调用Anthropic API"""
        headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }
        
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens
        }
        
        response = requests.post(self.endpoint, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        return result.get("content", [{}])[0].get("text", "").strip()

    def analyze_mood(self, user_input: str) -> str:
        """
        分析用户的心情，返回心情标签
        
        可选的心情标签：开心、平静、忧伤、兴奋、浪漫、随意
        
        返回:
            str: 心情标签
        """
        if not self.is_configured():
            return "随意"
        
        prompt = f"""分析以下用户的心情，从以下选项中选择一个最合适的：
选项：开心、平静、忧伤、兴奋、浪漫、随意

用户说：{user_input}

请只返回一个心情标签，不要有其他文字。"""
        
        try:
            response = self.call(prompt, max_tokens=20, temperature=0.3)
            if response:
                mood = response.strip()
                valid_moods = ["开心", "平静", "忧伤", "兴奋", "浪漫", "随意"]
                if mood in valid_moods:
                    return mood
        except:
            pass
        
        return "随意"

    def chat_with_analysis(self, user_input: str, weather: Dict[str, Any]) -> Dict[str, Any]:
        """
        与用户对话并分析心情
        
        返回:
            dict: {
                'response': AI回复,
                'mood': 分析出的心情,
                'should_recommend': 是否应该推荐歌曲
            }
        """
        if not self.is_configured():
            return {
                'response': "AI功能暂未配置，你可以试试手动推荐功能！",
                'mood': "随意",
                'should_recommend': False
            }
        
        weather_info = f"当前天气: {weather.get('description', '未知')}, 温度: {weather.get('temperature', '?')}℃"
        
        # 分析心情
        mood = self.analyze_mood(user_input)
        
        # 生成对话
        prompt = f"""你是一个热情的智能音乐电台DJ。{weather_info}

用户说：{user_input}

你的任务：
1. 优先回答用户的问题，像朋友一样自然聊天
2. 只有在合适的时候才推荐歌曲，不要太频繁
3. 如果用户在提问、分享事情或只是闲聊，先正常对话，不要强行推荐
4. 推荐时可以简单说一句理由（如"这首很适合现在的氛围"）
5. 不要出现"心情分析"、"当前天气"等机械格式

输出格式（JSON）：
{{
  "response": "你的自然对话回复",
  "should_recommend": true/false,
  "song_name": "歌曲名（没有则为空）",
  "song_artist": "歌手名（没有则为空）"
}}

示例1（用户问问题，不推荐）：
{{
  "response": "哈哈，这是我的私藏歌单！都是精心挑选的~",
  "should_recommend": false,
  "song_name": "",
  "song_artist": ""
}}

示例2（用户聊天气，适当推荐）：
{{
  "response": "今天确实很热！来首清爽的降降温吧~",
  "should_recommend": true,
  "song_name": "凉凉",
  "song_artist": "杨宗纬"
}}

示例3（用户明确点歌）：
{{
  "response": "好的！这就为你播放~",
  "should_recommend": true,
  "song_name": "夏天的风",
  "song_artist": "温岚"
}}

请确保输出是有效的JSON格式。"""
        
        response = self.call(prompt, max_tokens=200, temperature=0.8)
        
        # 解析大模型的JSON回复
        try:
            import json
            # 清理可能的多余字符
            json_str = response.strip()
            # 去掉可能的引号包裹
            if json_str.startswith('"') and json_str.endswith('"'):
                json_str = json_str[1:-1]
            # 解析JSON
            result_data = json.loads(json_str)
            
            return {
                'response': result_data.get('response', '好的！'),
                'mood': mood,
                'should_recommend': result_data.get('should_recommend', False),
                'recommended_song': {
                    'name': result_data.get('song_name', ''),
                    'artist': result_data.get('song_artist', '')
                } if result_data.get('song_name') else None
            }
        except Exception as e:
            # 如果JSON解析失败，使用原来的简单逻辑作为备用
            print(f"JSON解析失败: {e}")
            print(f"原始响应: {response}")
            
            # 备用逻辑：检查是否包含推荐相关词汇
            recommend_triggers = ['推荐', '播放', '来点', '听首', '听歌', '音乐']
            should_recommend = any(trigger in response for trigger in recommend_triggers)
            
            return {
                'response': response if response else "好的！让我为你推荐一首歌曲吧！",
                'mood': mood,
                'should_recommend': should_recommend,
                'recommended_song': None
            }

_llm_client = None

def get_llm_client() -> LLMClient:
    """获取LLM客户端单例"""
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient()
    return _llm_client

def chat_with_user(user_input: str, context: Dict[str, Any]) -> str:
    """与用户对话（兼容旧接口）"""
    client = get_llm_client()
    if not client.is_configured():
        return "⚠️ 大模型未配置，请在.env中设置 LLM_API_KEY、LLM_ENDPOINT 和 LLM_MODEL"
    
    weather = context.get("weather", {})
    result = client.chat_with_analysis(user_input, weather)
    return result['response']

if __name__ == "__main__":
    client = get_llm_client()
    print(f"LLM配置状态: {'已配置' if client.is_configured() else '未配置'}")
    
    if client.is_configured():
        test_inputs = [
            "今天天气真不错，心情很好！",
            "感觉有点难过，想听些忧伤的歌",
            "好兴奋，晚上要去聚会！",
            "想找些安静的音乐放松一下"
        ]
        
        for test in test_inputs:
            result = client.chat_with_analysis(test, {'description': '晴', 'temperature': 25})
            print(f"\n输入: {test}")
            print(f"心情: {result['mood']}")
            print(f"回复: {result['response']}")
