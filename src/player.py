import pygame
import threading
import time
import os
import sys
import tempfile
import requests
import atexit
from dotenv import load_dotenv

# 导入获取播放URL的功能
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from sync import get_song_play_url, load_cookie
except ImportError:
    get_song_play_url = None
    load_cookie = None

class MusicPlayer:
    """音乐播放器核心类"""
    
    def __init__(self):
        pygame.mixer.init()
        self.current_track = None
        self.is_playing = False
        self.play_thread = None
        self.temp_file = None
        self.cookie = self._load_cookie()
        
        # 注册退出时清理的函数
        atexit.register(self.cleanup)
        
        # 启动时清理旧的临时文件
        self._cleanup_old_temp_files()
        
    def _load_cookie(self):
        """加载网易云Cookie"""
        if load_cookie:
            try:
                return load_cookie()
            except:
                pass
        return ""
    
    def _cleanup_old_temp_files(self):
        """清理旧的临时歌曲文件"""
        try:
            temp_dir = tempfile.gettempdir()
            # 删除所有以 temp_song_ 开头的 mp3 文件
            for filename in os.listdir(temp_dir):
                if filename.startswith("temp_song_") and filename.endswith(".mp3"):
                    filepath = os.path.join(temp_dir, filename)
                    try:
                        # 检查文件是否超过1小时未修改
                        file_age = time.time() - os.path.getmtime(filepath)
                        if file_age > 3600:  # 1小时
                            os.remove(filepath)
                            print(f"清理旧文件: {filename}")
                    except:
                        pass
        except Exception as e:
            print(f"清理临时文件失败: {e}")
    
    def cleanup(self):
        """清理临时文件"""
        if self.temp_file and os.path.exists(self.temp_file):
            try:
                os.remove(self.temp_file)
                print(f"已清理临时文件: {self.temp_file}")
            except:
                pass
            self.temp_file = None
        
    def _download_song(self, url: str) -> str:
        """
        下载歌曲到临时文件
        
        参数:
            url: 歌曲URL
            
        返回:
            str: 临时文件路径
        """
        try:
            print("正在下载歌曲...")
            response = requests.get(url, stream=True, timeout=60)
            response.raise_for_status()
            
            # 创建临时文件
            temp_dir = tempfile.gettempdir()
            temp_path = os.path.join(temp_dir, f"temp_song_{int(time.time())}.mp3")
            
            # 写入文件
            total_bytes = 0
            with open(temp_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
                    total_bytes += len(chunk)
            
            # 检查文件大小（小于1KB可能是错误信息）
            if total_bytes < 1024:
                print(f"警告：文件太小 ({total_bytes} bytes)，可能下载失败")
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                return ""
            
            print(f"下载完成: {temp_path} ({total_bytes/1024/1024:.2f} MB)")
            return temp_path
            
        except Exception as e:
            print(f"下载失败: {e}")
            return ""
        
    def load_from_netease(self, netease_id: str) -> bool:
        """
        从网易云加载歌曲
        
        参数:
            netease_id: 网易云歌曲ID
            
        返回:
            bool: 是否成功
        """
        if not get_song_play_url:
            print("获取播放URL的功能不可用")
            return False
        
        # 获取播放URL
        print(f"正在获取歌曲 {netease_id} 的播放链接...")
        play_url = get_song_play_url(netease_id, self.cookie)
        
        if not play_url:
            print("无法获取播放链接，尝试打开浏览器...")
            return False
        
        # 下载歌曲
        temp_file = self._download_song(play_url)
        if not temp_file:
            return False
        
        # 加载到播放器
        if self.load(temp_file):
            self.temp_file = temp_file
            print(f"    加载成功")
            return True
        
        print("加载失败，尝试其他方式...")
        # 清理临时文件
        if os.path.exists(temp_file):
            os.remove(temp_file)
        return False
        
    def load(self, file_path):
        """加载音乐文件"""
        try:
            pygame.mixer.music.load(file_path)
            self.current_track = file_path
            return True
        except Exception as e:
            print(f"加载失败: {str(e)}")
            # 尝试重新初始化mixer
            try:
                pygame.mixer.quit()
                pygame.mixer.init()
                pygame.mixer.music.load(file_path)
                self.current_track = file_path
                return True
            except:
                return False
            
    def play(self):
        """播放音乐"""
        print(f"    play() 调用 - is_playing={self.is_playing}, current_track={bool(self.current_track)}")
        
        if not self.is_playing and self.current_track:
            try:
                pygame.mixer.music.play()
                self.is_playing = True
                print("    开始播放...")
                
                # 启动播放状态监控线程
                self.play_thread = threading.Thread(target=self._monitor_playback)
                self.play_thread.daemon = True
                self.play_thread.start()
                return True
            except Exception as e:
                print(f"播放失败: {e}")
                import traceback
                traceback.print_exc()
                return False
        
        if self.is_playing:
            print("    播放失败：已经在播放中")
        if not self.current_track:
            print("    播放失败：没有加载音乐")
        return False
        
    def pause(self):
        """暂停播放"""
        if self.is_playing:
            pygame.mixer.music.pause()
            self.is_playing = False
            return True
        return False
        
    def resume(self):
        """继续播放"""
        if not self.is_playing and self.current_track:
            pygame.mixer.music.unpause()
            self.is_playing = True
            return True
        return False
        
    def stop(self):
        """停止播放"""
        pygame.mixer.music.stop()
        self.is_playing = False
        if self.play_thread and self.play_thread.is_alive():
            self.play_thread.join(timeout=0.5)
        
        # 清理临时文件
        self.cleanup()
        
        return True
        
    def _monitor_playback(self):
        """监控播放状态"""
        start_time = time.time()
        print(f"    监控线程已启动")
        
        while self.is_playing:
            if not pygame.mixer.music.get_busy():
                elapsed = time.time() - start_time
                self.is_playing = False
                
                # 如果播放时间太短，可能是文件问题
                if elapsed < 10:  # 小于10秒
                    print(f"\n⚠️ 播放异常结束！(仅播放了 {elapsed:.1f} 秒)")
                else:
                    print(f"\n🎵 播放完成！(共播放 {elapsed:.1f} 秒)")
                break
            time.sleep(0.5)
            
    def get_status(self):
        """获取播放状态"""
        return {
            "playing": self.is_playing,
            "current_track": self.current_track,
            "position": pygame.mixer.music.get_pos() / 1000  # 转换为秒
        }

if __name__ == "__main__":
    # 测试代码
    player = MusicPlayer()
    print("测试播放器")
    print("命令: play <网易云ID>, pause, resume, stop, exit")
    
    while True:
        try:
            cmd_line = input("> ").strip()
            if not cmd_line:
                continue
                
            parts = cmd_line.split()
            cmd = parts[0].lower()
            
            if cmd == "play":
                if len(parts) > 1:
                    netease_id = parts[1]
                    player.stop()
                    if player.load_from_netease(netease_id):
                        player.play()
                        print("开始播放")
                    else:
                        print("加载失败")
                else:
                    print("请输入网易云ID: play <ID>")
            elif cmd == "pause":
                player.pause()
                print("已暂停")
            elif cmd == "resume":
                player.resume()
                print("继续播放")
            elif cmd == "stop":
                player.stop()
                print("停止播放")
            elif cmd == "status":
                print(player.get_status())
            elif cmd == "exit":
                player.stop()
                break
        except KeyboardInterrupt:
            player.stop()
            break
        except Exception as e:
            print(f"错误: {e}")