import requests

def get_weather(api_key: str, city: str) -> dict:
    """获取当前天气数据"""
    # 如果API key为空，直接返回模拟数据
    if not api_key or api_key == "your_api_key_here":
        print("警告: WEATHER_API_KEY未设置，使用模拟天气数据")
        return {"temperature": 25, "humidity": 50, "description": "晴"}
    
    try:
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
        response = requests.get(url)
        response.raise_for_status()
        
        data = response.json()
        return {
            "temperature": data["main"]["temp"],
            "humidity": data["main"]["humidity"],
            "description": data["weather"][0]["description"]
        }
    except requests.RequestException as e:
        print(f"天气请求失败: {e}")
        return {"temperature": 25, "humidity": 50, "description": "晴"}

# 测试代码
if __name__ == "__main__":
    # 需要先在.env设置WEATHER_API_KEY
    from dotenv import load_dotenv
    import os
    
    load_dotenv()
    print(get_weather(os.getenv("WEATHER_API_KEY"), "Beijing"))