import os
import requests
import json
from pathlib import Path
from mutagen import File
from mutagen.id3 import ID3, TIT2, TPE1, TALB, TCON, TDRC

class LyricMatcher:
    def __init__(self):
        self.api_sources = [
            self.netease_cloud_music,
            self.qq_music,
            self.kugou_music
        ]
        
    def get_song_info(self, file_path):
        """获取歌曲信息"""
        try:
            audio = File(file_path)
            if audio is None:
                return self.get_basic_info(file_path)
                
            info = {
                'path': str(file_path),
                'title': '',
                'artist': '',
                'album': '',
                'genre': '',
                'year': '',
                'duration': self.get_duration(audio),
                'size': self.get_file_size(file_path)
            }
            
            if hasattr(audio, 'tags'):
                if 'TIT2' in audio.tags:
                    info['title'] = str(audio.tags['TIT2'])
                if 'TPE1' in audio.tags:
                    info['artist'] = str(audio.tags['TPE1'])
                if 'TALB' in audio.tags:
                    info['album'] = str(audio.tags['TALB'])
                if 'TCON' in audio.tags:
                    info['genre'] = str(audio.tags['TCON'])
                if 'TDRC' in audio.tags:
                    info['year'] = str(audio.tags['TDRC'])
                    
            # 如果ID3标签中没有信息，使用文件名
            if not info['title']:
                info['title'] = file_path.stem
                
            return info
            
        except Exception as e:
            return self.get_basic_info(file_path)
            
    def get_basic_info(self, file_path):
        """获取基本信息"""
        return {
            'path': str(file_path),
            'title': file_path.stem,
            'artist': '未知歌手',
            'album': '',
            'genre': '未知风格',
            'year': '',
            'duration': '00:00',
            'size': self.get_file_size(file_path)
        }
        
    def get_duration(self, audio):
        """获取时长"""
        if audio is not None and hasattr(audio.info, 'length'):
            duration = int(audio.info.length)
            minutes = duration // 60
            seconds = duration % 60
            return f"{minutes:02d}:{seconds:02d}"
        return "00:00"
        
    def get_file_size(self, file_path):
        """获取文件大小"""
        size = file_path.stat().st_size
        if size < 1024 * 1024:  # 小于1MB
            return f"{size/1024:.1f} KB"
        else:
            return f"{size/(1024 * 1024):.1f} MB"
            
    def auto_match_lyrics(self, song_name, artist=""):
        """自动匹配歌词"""
        lyrics = []
        
        for api_source in self.api_sources:
            try:
                result = api_source(song_name, artist)
                if result:
                    lyrics.extend(result)
            except:
                continue
                
        return lyrics
        
    def netease_cloud_music(self, song_name, artist=""):
        """网易云音乐歌词搜索"""
        # 这里应该调用网易云音乐API
        # 由于API限制，这里返回模拟数据
        return [{
            'title': f"{song_name} - 网易云音乐",
            'lyric': f"[00:00.00]{song_name} - 网易云音乐歌词\n[00:05.00]第一行歌词\n[00:10.00]第二行歌词",
            'source': '网易云音乐'
        }]
        
    def qq_music(self, song_name, artist=""):
        """QQ音乐歌词搜索"""
        # 这里应该调用QQ音乐API
        return [{
            'title': f"{song_name} - QQ音乐",
            'lyric': f"[00:00.00]{song_name} - QQ音乐歌词\n[00:05.00]第一行歌词\n[00:10.00]第二行歌词",
            'source': 'QQ音乐'
        }]
        
    def kugou_music(self, song_name, artist=""):
        """酷狗音乐歌词搜索"""
        # 这里应该调用酷狗音乐API
        return [{
            'title': f"{song_name} - 酷狗音乐",
            'lyric': f"[00:00.00]{song_name} - 酷狗音乐歌词\n[00:05.00]第一行歌词\n[00:10.00]第二行歌词",
            'source': '酷狗音乐'
        }]
        
    def save_lyrics(self, file_path, lyrics, source=""):
        """保存歌词到文件"""
        lrc_path = file_path.with_suffix('.lrc')
        
        try:
            with open(lrc_path, 'w', encoding='utf-8') as f:
                f.write(lyrics)
            return True
        except:
            return False
