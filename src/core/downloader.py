import os
import re
import yt_dlp
from pathlib import Path
from urllib.parse import urlparse, parse_qs
from PyQt5.QtCore import QThread, pyqtSignal

class DownloadThread(QThread):
    """下载线程"""
    progress = pyqtSignal(str, int)  # url, 进度百分比
    finished = pyqtSignal(str, str)  # url, 文件路径
    error = pyqtSignal(str, str)    # url, 错误信息
    
    def __init__(self, url, download_path, downloader):
        super().__init__()
        self.url = url
        self.download_path = download_path
        self.downloader = downloader
        self._is_running = True
        self._is_paused = False
        
    def run(self):
        try:
            if not self._is_running:
                return
                
            # 下载视频并提取音频
            file_path = self.downloader.download_audio(self.url, self.download_path, self.update_progress)
            
            if self._is_running and file_path:
                self.progress.emit(self.url, 100)
                self.finished.emit(self.url, file_path)
            else:
                self.error.emit(self.url, "下载被取消")
                
        except Exception as e:
            self.error.emit(self.url, str(e))
            
    def update_progress(self, d):
        """更新下载进度"""
        if d['status'] == 'downloading':
            # 计算进度百分比
            if 'total_bytes' in d and d['total_bytes']:
                percent = int(d['downloaded_bytes'] * 100 / d['total_bytes'])
                self.progress.emit(self.url, percent)
        elif d['status'] == 'finished':
            self.progress.emit(self.url, 100)
            
    def stop(self):
        """停止下载"""
        self._is_running = False
        
    def pause(self):
        """暂停下载"""
        self._is_paused = True
        
    def resume(self):
        """继续下载"""
        self._is_paused = False
        
    def isPaused(self):
        """检查是否暂停"""
        return self._is_paused

class BilibiliDownloader:
    def __init__(self):
        self.session = yt_dlp
        # 设置下载选项
        self.ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': '%(title)s.%(ext)s',
            'restrictfilenames': True,
            'noplaylist': True,
            'nocheckcertificate': True,
            'ignoreerrors': False,
            'logtostderr': False,
            'quiet': True,
            'no_warnings': True,
            'default_search': 'auto',
            'source_address': '0.0.0.0',
            'extractaudio': True,
            'audioformat': 'mp3',
            'audioquality': '0',  # 最好质量
            'prefer_ffmpeg': True,
            'keepvideo': False,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }
        
    def extract_video_info(self, url):
        """提取视频信息"""
        try:
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                return {
                    'title': info.get('title', '未知标题'),
                    'duration': info.get('duration', 0),
                    'uploader': info.get('uploader', '未知上传者'),
                    'thumbnail': info.get('thumbnail', ''),
                    'description': info.get('description', ''),
                    'webpage_url': info.get('webpage_url', url)
                }
        except Exception as e:
            raise Exception(f"视频信息提取失败: {str(e)}")
            
    def download_audio(self, url, download_path, progress_hook=None):
        """下载音频"""
        try:
            # 设置下载路径
            opts = self.ydl_opts.copy()
            opts['outtmpl'] = os.path.join(download_path, '%(title)s.%(ext)s')
            
            if progress_hook:
                opts['progress_hooks'] = [progress_hook]
                
            with yt_dlp.YoutubeDL(opts) as ydl:
                # 先提取信息
                info = ydl.extract_info(url, download=False)
                original_title = info.get('title', '未知标题')
                
                # 清理文件名
                safe_title = self.sanitize_filename(original_title)
                final_path = os.path.join(download_path, f"{safe_title}.mp3")
                
                # 如果文件已存在，添加数字后缀
                counter = 1
                while os.path.exists(final_path):
                    final_path = os.path.join(download_path, f"{safe_title}_{counter}.mp3")
                    counter += 1
                    
                # 设置最终的文件名
                opts['outtmpl'] = os.path.join(download_path, f"{safe_title}.%(ext)s")
                
                # 下载
                ydl.download([url])
                
                return final_path
                
        except Exception as e:
            raise Exception(f"下载失败: {str(e)}")
            
    def download_batch(self, urls, download_path, progress_callback=None):
        """批量下载"""
        results = []
        total = len(urls)
        
        for i, url in enumerate(urls):
            try:
                if progress_callback:
                    progress_callback(i, total, f"正在下载 {i+1}/{total}")
                    
                file_path = self.download_audio(url, download_path)
                results.append({
                    'url': url,
                    'file_path': file_path,
                    'status': 'success'
                })
                
            except Exception as e:
                results.append({
                    'url': url,
                    'status': 'error',
                    'error': str(e)
                })
                
        return results
        
    def sanitize_filename(self, filename):
        """清理文件名中的非法字符"""
        # 移除非法字符
        filename = re.sub(r'[<>:"/\\|?*]', '', filename)
        # 移除首尾空格
        filename = filename.strip()
        # 限制文件名长度
        if len(filename) > 100:
            filename = filename[:100]
            
        return filename
