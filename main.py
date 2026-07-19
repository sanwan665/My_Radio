import os
import webbrowser
from src.recommender import MusicRecommender
from src.player import MusicPlayer
from src.command_parser import CommandParser
from src.aliyun_llm import get_llm_client, chat_with_user
from src.weather_service import get_weather
from src.sentiment_analysis import analyze_sentiment
from src.netease_openapi import get_openapi_client
from dotenv import load_dotenv

def check_config():
    """检查配置状态"""
    print("\n===== Configuration Check =====")
    
    # 检查网易云Cookie
    netease_cookie = os.getenv("NETEASE_COOKIE")
    if netease_cookie and netease_cookie != "your_cookie_here":
        print("[OK] NetEase Cookie: Configured")
    else:
        print("[X] NetEase Cookie: Not configured (cannot sync playlist)")
    
    # 检查网易云开放平台
    openapi_client = get_openapi_client()
    if openapi_client.is_configured():
        print("[OK] NetEase OpenAPI: Configured (can use official recommendations)")
    else:
        print("[~] NetEase OpenAPI: Not configured (using local database only)")
    
    # 检查大模型
    llm_client = get_llm_client()
    if llm_client.is_configured():
        print(f"[OK] LLM: Configured ({llm_client.model})")
    else:
        print("[X] LLM: Not configured (cannot use AI chat)")
    
    # 检查天气
    weather_key = os.getenv("WEATHER_API_KEY")
    if weather_key and weather_key != "your_api_key_here":
        print(f"[OK] Weather API: Configured")
    else:
        print("[~] Weather API: Not configured (using default weather)")
    
    print("================================\n")

def get_weather_info():
    """获取天气信息"""
    weather_key = os.getenv("WEATHER_API_KEY", "")
    city = os.getenv("CITY", "Beijing")
    
    try:
        weather = get_weather(weather_key, city)
        return weather
    except:
        return {"temperature": 25, "humidity": 50, "description": "晴"}

def get_official_recommendation():
    """
    从网易云开放平台获取官方推荐
    优先使用官方API，失败则使用本地数据库
    """
    openapi_client = get_openapi_client()
    
    if openapi_client.is_configured():
        try:
            # 先尝试获取推荐歌曲
            songs = openapi_client.get_recommend_songs()
            if songs and len(songs) > 0:
                # 格式化歌曲信息
                song = songs[0]
                return {
                    "name": song.get("name", "未知"),
                    "artist": song.get("artist", "未知"),
                    "netease_id": str(song.get("id", ""))
                }
            
            # 如果没获取到推荐歌曲，试试推荐歌单
            playlists = openapi_client.get_recommend_playlists()
            if playlists and len(playlists) > 0:
                print(f"获取到推荐歌单: {playlists[0].get('name', '')}")
        
        except Exception as e:
            print(f"官方推荐API调用失败: {e}")
    
    return None

def open_netease_song(song, player=None):
    """
    播放网易云歌曲 - 先尝试直接播放，失败则打开浏览器
    
    参数:
        song: 歌曲信息
        player: MusicPlayer实例（可选）
    """
    if not song.get("netease_id"):
        print("   抱歉，这首歌没有网易云ID...")
        return False
    
    netease_id = song["netease_id"]
    
    # 先尝试直接播放
    if player:
        print(f"   正在加载: {song['name']} - {song['artist']}")
        load_success = player.load_from_netease(netease_id)
        print(f"   加载结果: {'成功' if load_success else '失败'}")
        
        if load_success:
            play_success = player.play()
            print(f"   播放结果: {'成功' if play_success else '失败'}")
            
            if play_success:
                # 等待一下让音乐开始播放
                import time
                time.sleep(1)
                return True
    
    # 直接播放失败，打开浏览器
    url = f"https://music.163.com/#/song?id={netease_id}"
    print(f"   直接播放失败，正在打开浏览器: {url}")
    webbrowser.open(url)
    return True

def chat_mode(recommender, player):
    """对话模式"""
    print("\n===== AI 对话模式 =====")
    print("输入'退出'返回主菜单")
    print("输入'推荐'获取歌曲推荐")
    print("输入'暂停'暂停播放")
    print("输入'继续'继续播放")
    print("输入'停止'停止播放")
    print("=" * 22)
    
    llm_client = get_llm_client()
    
    # 显示当前播放状态
    def show_status():
        status = player.get_status()
        if status['playing']:
            print(f"🎵 正在播放中... (位置: {status['position']:.1f}秒)")
        elif status['current_track']:
            print("⏸️ 已暂停")
        else:
            print("🔇 未播放")
    
    while True:
        try:
            # 显示播放状态
            show_status()
            
            user_input = input("\n你> ").strip()
            
            if user_input.lower() in ["退出", "exit", "quit"]:
                print("退出对话模式...")
                break
            
            if user_input.lower() in ["暂停", "pause"]:
                player.pause()
                print("✅ 已暂停")
                continue
            
            if user_input.lower() in ["继续", "resume"]:
                player.resume()
                print("✅ 继续播放")
                continue
            
            if user_input.lower() in ["停止", "stop"]:
                player.stop()
                print("✅ 停止播放")
                continue
            
            if user_input.lower() in ["推荐", "推荐歌曲"]:
                # 优先使用官方API推荐
                song = get_official_recommendation()
                if not song:
                    # 官方推荐失败，使用本地数据库推荐
                    song = recommender.recommend(user_input)
                
                print(f"\n🎵 推荐: {song['name']} - {song['artist']}")
                open_netease_song(song, player)
                continue
            
            if not user_input:
                continue
            
            # 获取天气信息
            weather = get_weather_info()
            
            # 与AI对话并分析心情
            result = llm_client.chat_with_analysis(user_input, weather)
            print(f"\nAI> {result['response']}")
            
            # 根据AI的判断推荐歌曲
            if result['should_recommend']:
                song = None
                
                # 首先检查大模型是否推荐了具体歌曲
                if result.get('recommended_song'):
                    rec_song = result['recommended_song']
                    song_name = rec_song.get('name', '')
                    song_artist = rec_song.get('artist', '')
                    
                    if song_name:
                        # 在数据库中搜索大模型推荐的歌曲
                        song = recommender.search_song(song_name)
                        if not song and song_artist:
                            # 如果只搜索歌名没找到，试试搜索歌手名
                            song = recommender.search_song(song_artist)
                
                # 如果大模型推荐的歌曲没找到，再搜索用户输入中提到的歌曲
                if not song and user_input:
                    song = recommender.search_song(user_input)
                
                # 如果都没找到，使用默认推荐
                if not song:
                    # 优先使用官方API推荐
                    song = get_official_recommendation()
                    if not song:
                        # 官方推荐失败，使用本地数据库推荐
                        song = recommender.recommend(result['mood'])
                
                print(f"\n🎵 为你推荐: {song['name']} - {song['artist']}")
                user_choice = input("🎧 要播放这首歌吗？: ").strip()
                
                # 完全交给大模型来判断用户是否同意播放
                is_agree = False
                
                if llm_client.is_configured():
                    prompt = f"""用户被推荐了歌曲《{song['name']}》，用户回复："{user_choice}"
判断用户是否同意播放这首歌？请输出JSON格式：
{{
  "agree": true/false
}}"""
                    try:
                        import json
                        llm_response = llm_client.call(prompt, max_tokens=50, temperature=0)
                        response_str = llm_response.strip()
                        if response_str.startswith('"') and response_str.endswith('"'):
                            response_str = response_str[1:-1]
                        result = json.loads(response_str)
                        is_agree = result.get('agree', False)
                    except Exception as e:
                        print(f"解析失败，使用简单判断: {e}")
                        # 备用：简单关键词判断
                        positive_words = ['是', '播放', '好', 'yes', '好的', '嗯', '行', '可以', '听', '放', 'ok', 'okay']
                        is_agree = any(word in user_choice.lower() for word in positive_words)
                else:
                    # 如果大模型未配置，使用简单关键词判断
                    positive_words = ['是', '播放', '好', 'yes', '好的', '嗯', '行', '可以', '听', '放', 'ok', 'okay']
                    is_agree = any(word in user_choice.lower() for word in positive_words)
                
                if is_agree:
                    # 先停止当前播放的歌曲
                    if player.is_playing:
                        player.stop()
                    # 播放新歌曲
                    open_netease_song(song, player)
                else:
                    print("好的，下次再为你推荐！")
            
        except KeyboardInterrupt:
            print("\n退出对话模式...")
            break
        except Exception as e:
            print(f"\n发生错误: {e}")
            import traceback
            traceback.print_exc()

def main():
    """主程序入口"""
    load_dotenv()
    
    # 显示配置状态
    check_config()
    
    # 初始化组件
    recommender = MusicRecommender()
    player = MusicPlayer()
    parser = CommandParser(player, recommender)
    
    print("===== 智能音乐电台 =====")
    print("输入'对话'进入AI对话模式")
    print("输入'帮助'查看所有命令")
    
    while True:
        try:
            user_input = input("\n电台> ").strip()
            
            # 处理特殊命令
            if user_input.lower() in ["对话", "chat"]:
                chat_mode(recommender, player)
                continue
            
            # 解析并执行命令
            result = parser.parse(user_input)
            
            # 处理退出命令
            if result == "exit":
                print("感谢使用，再见！")
                player.stop()
                break
                
            # 输出结果
            print(result)
            
        except KeyboardInterrupt:
            print("\n程序已中断")
            player.stop()
            break
        except Exception as e:
            print(f"发生错误: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    main()