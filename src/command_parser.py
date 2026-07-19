class CommandParser:
    """命令解析器类"""
    
    def __init__(self, player, recommender):
        self.player = player
        self.recommender = recommender
        self.current_song = None
        self.liked_songs = []
        self.commands = {
            "播放": self.play,
            "暂停": self.pause,
            "继续": self.resume,
            "停止": self.stop,
            "推荐": self.recommend,
            "喜欢": self.like,
            "不喜欢": self.dislike,
            "列表": self.list_songs,
            "状态": self.status,
            "帮助": self.help,
            "退出": self.exit
        }
        
    def parse(self, command):
        """解析并执行命令"""
        cmd = command.strip().lower()
        if cmd in self.commands:
            return self.commands[cmd]()
        return f"未知命令: {command}\n输入'帮助'查看可用命令"
    
    def play(self):
        """播放当前推荐音乐"""
        if not self.current_song:
            return "请先获取推荐音乐（输入'推荐'）"
        
        local_path = self.current_song.get("local_path")
        if not local_path:
            return f"歌曲 '{self.current_song['name']}' 没有本地文件路径\n" \
                   "注意：这是演示版本，当前不包含实际音乐文件下载功能"
        
        if self.player.load(local_path):
            if self.player.play():
                return f"开始播放: {self.current_song['name']} - {self.current_song['artist']}"
        return "播放失败，请检查音乐文件"
    
    def pause(self):
        """暂停播放"""
        if self.player.pause():
            return "已暂停"
        return "暂停失败，当前未在播放状态"
    
    def resume(self):
        """继续播放"""
        if self.player.resume():
            return "继续播放"
        return "继续播放失败，请确保已暂停"
    
    def stop(self):
        """停止播放"""
        if self.player.stop():
            return "停止播放"
        return "停止播放失败"
    
    def recommend(self):
        """获取新的音乐推荐"""
        self.current_song = self.recommender.recommend()
        
        if "info" in self.current_song:
            return self.current_song["info"]
        
        return (f"🎵 推荐音乐\n"
                f"歌曲: {self.current_song['name']}\n"
                f"歌手: {self.current_song['artist']}\n"
                f"网易云ID: {self.current_song['netease_id']}\n"
                f"\n输入 '播放' 来播放这首歌曲")
    
    def like(self):
        """标记喜欢当前音乐"""
        if not self.current_song:
            return "没有正在播放的音乐"
        
        song_key = f"{self.current_song['name']}-{self.current_song['artist']}"
        if song_key not in self.liked_songs:
            self.liked_songs.append(song_key)
        
        return f"❤️ 已标记喜欢: {self.current_song['name']} - {self.current_song['artist']}\n" \
               "这将在未来帮助优化您的推荐"
    
    def dislike(self):
        """标记不喜欢当前音乐"""
        if not self.current_song:
            return "没有正在播放的音乐"
        
        return f"👎 已记录您的反馈: {self.current_song['name']} - {self.current_song['artist']}\n" \
               "这将在未来帮助优化您的推荐"
    
    def list_songs(self):
        """列出数据库中的所有歌曲"""
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from database import fetch_all_songs, get_song_count
        
        count = get_song_count()
        if count == 0:
            return "数据库中没有歌曲"
        
        songs = fetch_all_songs()
        result = [f"📚 数据库中的歌曲（共 {count} 首）:"]
        
        for i, song in enumerate(songs[:20], 1):  # 最多显示20首
            result.append(f"{i}. {song['name']} - {song['artist']}")
        
        if count > 20:
            result.append(f"... 还有 {count - 20} 首")
        
        return "\n".join(result)
    
    def status(self):
        """获取播放状态"""
        status = self.player.get_status()
        
        song_info = ""
        if self.current_song:
            song_info = f"\n当前推荐: {self.current_song['name']} - {self.current_song['artist']}"
        
        return (f"状态: {'播放中' if status['playing'] else '已暂停'}\n"
                f"当前曲目: {status['current_track'] or '无'}\n"
                f"位置: {status['position']:.1f}秒"
                f"{song_info}")
    
    def help(self):
        """显示帮助信息"""
        return ("可用命令:\n"
                "  推荐 - 获取新的音乐推荐\n"
                "  播放 - 播放当前推荐\n"
                "  暂停 - 暂停播放\n"
                "  继续 - 继续播放\n"
                "  停止 - 停止播放\n"
                "  列表 - 查看数据库中的所有歌曲\n"
                "  喜欢 - 标记喜欢当前音乐\n"
                "  不喜欢 - 标记不喜欢当前音乐\n"
                "  状态 - 查看播放状态\n"
                "  帮助 - 显示帮助信息\n"
                "  退出 - 退出程序")
    
    def exit(self):
        """退出程序"""
        self.player.stop()
        return "exit"