# -*- coding: utf-8 -*-
from database import fetch_all_songs

songs = fetch_all_songs()
with open('song_list.txt', 'w', encoding='utf-8') as f:
    f.write(f'数据库中共有 {len(songs)} 首歌曲\n')
    f.write('=' * 50 + '\n')
    for i, song in enumerate(songs):
        f.write(f"{i+1}. {song['name']} - {song['artist']}\n")
print(f'歌曲列表已保存到 song_list.txt，共 {len(songs)} 首')