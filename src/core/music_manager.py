import os
import shutil
from pathlib import Path
from mutagen import File
from mutagen.id3 import ID3, TIT2, TPE1, TALB, TCON, TDRC

class MusicManager:
    def __init__(self):
        pass
        
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
                elif 'title' in audio.tags:
                    info['title'] = str(audio.tags['title'][0])
                    
                if 'TPE1' in audio.tags:
                    info['artist'] = str(audio.tags['TPE1'])
                elif 'artist' in audio.tags:
                    info['artist'] = str(audio.tags['artist'][0])
                    
                if 'TALB' in audio.tags:
                    info['album'] = str(audio.tags['TALB'])
                elif 'album' in audio.tags:
                    info['album'] = str(audio.tags['album'][0])
                    
                if 'TCON' in audio.tags:
                    info['genre'] = str(audio.tags['TCON'])
                elif 'genre' in audio.tags:
                    info['genre'] = str(audio.tags['genre'][0])
                    
                if 'TDRC' in audio.tags:
                    info['year'] = str(audio.tags['TDRC'])
                elif 'date' in audio.tags:
                    info['year'] = str(audio.tags['date'][0])
                    
            # 如果标签中没有信息，使用文件名
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
            
    def rename_file(self, file_path, new_name):
        """重命名文件"""
        try:
            new_path = file_path.parent / new_name
            file_path.rename(new_path)
            
            # 同时重命名关联的歌词文件
            lrc_path = file_path.with_suffix('.lrc')
            if lrc_path.exists():
                new_lrc_path = new_path.with_suffix('.lrc')
                lrc_path.rename(new_lrc_path)
                
            return True
        except Exception as e:
            return False
            
    def move_file(self, file_path, target_dir):
        """移动文件"""
        try:
            target_path = target_dir / file_path.name
            shutil.move(file_path, target_path)
            
            # 同时移动关联的歌词文件
            lrc_path = file_path.with_suffix('.lrc')
            if lrc_path.exists():
                target_lrc_path = target_dir / lrc_path.name
                shutil.move(lrc_path, target_lrc_path)
                
            return True
        except Exception as e:
            return False
            
    def delete_file(self, file_path):
        """删除文件"""
        try:
            file_path.unlink()
            
            # 同时删除关联的歌词文件
            lrc_path = file_path.with_suffix('.lrc')
            if lrc_path.exists():
                lrc_path.unlink()
                
            return True
        except Exception as e:
            return False
            
    def update_id3_tags(self, file_path, title="", artist="", album="", genre="", year=""):
        """更新ID3标签"""
        try:
            audio = File(file_path)
            if audio is None:
                return False
                
            if not hasattr(audio, 'tags'):
                audio.add_tags()
                
            if title and 'TIT2' in audio.tags:
                audio.tags['TIT2'] = TIT2(encoding=3, text=title)
            if artist and 'TPE1' in audio.tags:
                audio.tags['TPE1'] = TPE1(encoding=3, text=artist)
            if album and 'TALB' in audio.tags:
                audio.tags['TALB'] = TALB(encoding=3, text=album)
            if genre and 'TCON' in audio.tags:
                audio.tags['TCON'] = TCON(encoding=3, text=genre)
            if year and 'TDRC' in audio.tags:
                audio.tags['TDRC'] = TDRC(encoding=3, text=year)
                
            audio.save()
            return True
            
        except Exception as e:
            return False
