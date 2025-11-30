import os
import re
import time
import yt_dlp
import requests
from pathlib import Path
from urllib.parse import urlparse, parse_qs
from PyQt5.QtCore import QThread, pyqtSignal, QMutex

class DownloadThread(QThread):
    """下载线程 - 修复版本"""
    progress = pyqtSignal(str, int)  # url, 进度百分比
    finished = pyqtSignal(str, str)  # url, 文件路径
    error = pyqtSignal(str, str)    # url, 错误信息
    status = pyqtSignal(str, str)   # url, 状态信息
    
    def __init__(self, url, download_path, downloader):
        super().__init__()
        self.url = url
        self.download_path = Path(download_path)
        self.downloader = downloader
        self._is_running = True
        self._is_paused = False
        self.mutex = QMutex()
        
    def run(self):
        try:
            if not self._is_running:
                return
                
            # 检查URL格式
            if not self.validate_url(self.url):
                self.error.emit(self.url, "无效的B站视频链接")
                return
                
            # 更新状态为"解析中"
            self.status.emit(self.url, "解析中")
            self.progress.emit(self.url, 10)
            
            # 提取视频信息
            video_info = self.downloader.extract_video_info(self.url)
            if not video_info:
                self.error.emit(self.url, "无法获取视频信息")
                return
                
            # 更新状态为"准备下载"
            self.status.emit(self.url, "准备下载")
            self.progress.emit(self.url, 30)
            
            # 下载音频
            if not self._is_running:
                return
                
            file_path = self.downloader.download_audio(
                self.url, 
                str(self.download_path), 
                self.update_progress
            )
            
            if self._is_running and file_path:
                self.progress.emit(self.url, 100)
                self.status.emit(self.url, "下载完成")
                self.finished.emit(self.url, file_path)
            else:
                self.error.emit(self.url, "下载被取消或失败")
                
        except Exception as e:
            error_msg = f"下载错误: {str(e)}"
            self.error.emit(self.url, error_msg)
            
    def validate_url(self, url):
        """验证URL格式"""
        bilibili_patterns = [
            r'https?://(www\.)?bilibili\.com/video/[A-Za-z0-9]+',
            r'https?://(www\.)?b23\.tv/[A-Za-z0-9]+',
            r'https?://m\.bilibili\.com/video/[A-Za-z0-9]+'
        ]
        
        for pattern in bilibili_patterns:
            if re.match(pattern, url):
                return True
        return False
            
    def update_progress(self, d):
        """更新下载进度"""
        if not self._is_running:
            raise Exception("下载已取消")
            
        if d['status'] == 'downloading':
            # 计算进度百分比
            if 'total_bytes' in d and d['total_bytes']:
                percent = int(d['downloaded_bytes'] * 100 / d['total_bytes'])
                # 确保进度在30-90%之间（避免跳过解析阶段）
                adjusted_percent = max(30, min(90, percent))
                self.progress.emit(self.url, adjusted_percent)
                self.status.emit(self.url, f"下载中 {percent}%")
        elif d['status'] == 'finished':
            self.progress.emit(self.url, 95)
            self.status.emit(self.url, "处理中")
        elif d['status'] == 'error':
            self.error.emit(self.url, f"下载错误: {d.get('error', '未知错误')}")
            
    def stop(self):
        """停止下载"""
        self.mutex.lock()
        self._is_running = False
        self.mutex.unlock()
        
    def pause(self):
        """暂停下载"""
        self.mutex.lock()
        self._is_paused = True
        self.mutex.unlock()
        
    def resume(self):
        """继续下载"""
        self.mutex.lock()
        self._is_paused = False
        self.mutex.unlock()
        
    def is_running(self):
        """检查是否运行中"""
        self.mutex.lock()
        running = self._is_running
        self.mutex.unlock()
        return running
        
    def is_paused(self):
        """检查是否暂停"""
        self.mutex.lock()
        paused = self._is_paused
        self.mutex.unlock()
        return paused

class BilibiliDownloader:
    def __init__(self):
        # 设置请求头模拟浏览器
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Referer': 'https://www.bilibili.com/',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        # 设置yt-dlp选项
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
            'audioquality': '0',
            'prefer_ffmpeg': True,
            'keepvideo': False,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            # 增加超时设置
            'socket_timeout': 30,
            'retries': 3,
            'buffersize': 1024 * 1024,
            'http_chunk_size': 10485760,
        }
        
    def extract_video_info(self, url):
        """提取视频信息 - 修复版本"""
        try:
            # 验证URL
            if not self.validate_url(url):
                raise Exception("无效的B站视频链接")
                
            # 使用yt-dlp提取信息
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                try:
                    info = ydl.extract_info(url, download=False)
                    if not info:
                        raise Exception("无法获取视频信息")
                        
                    return {
                        'title': info.get('title', '未知标题'),
                        'duration': info.get('duration', 0),
                        'uploader': info.get('uploader', '未知上传者'),
                        'thumbnail': info.get('thumbnail', ''),
                        'description': info.get('description', ''),
                        'webpage_url': info.get('webpage_url', url),
                        'formats': info.get('formats', [])
                    }
                except yt_dlp.DownloadError as e:
                    if "Unable to download webpage" in str(e):
                        raise Exception("网络连接失败，请检查网络设置")
                    elif "Video unavailable" in str(e):
                        raise Exception("视频不可用或已被删除")
                    elif "Private video" in str(e):
                        raise Exception("视频为私密视频，无法访问")
                    else:
                        raise Exception(f"解析失败: {str(e)}")
                        
        except Exception as e:
            raise Exception(f"视频信息提取失败: {str(e)}")
            
    def download_audio(self, url, download_path, progress_hook=None):
        """下载音频 - 修复版本"""
        try:
            # 确保下载目录存在
            download_path = Path(download_path)
            download_path.mkdir(parents=True, exist_ok=True)
            
            # 设置下载选项
            opts = self.ydl_opts.copy()
            opts['outtmpl'] = os.path.join(str(download_path), '%(title)s.%(ext)s')
            
            if progress_hook:
                opts['progress_hooks'] = [progress_hook]
                
            # 添加重试机制
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    with yt_dlp.YoutubeDL(opts) as ydl:
                        # 先提取信息获取标题
                        info = ydl.extract_info(url, download=False)
                        original_title = info.get('title', '未知标题')
                        
                        # 清理文件名
                        safe_title = self.sanitize_filename(original_title)
                        final_path = download_path / f"{safe_title}.mp3"
                        
                        # 如果文件已存在，添加数字后缀
                        counter = 1
                        while final_path.exists():
                            final_path = download_path / f"{safe_title}_{counter}.mp3"
                            counter += 1
                            
                        # 设置最终的文件名
                        opts['outtmpl'] = os.path.join(str(download_path), f"{safe_title}.%(ext)s")
                        
                        # 下载
                        ydl.download([url])
                        
                        # 验证下载文件
                        if final_path.exists() and final_path.stat().st_size > 0:
                            return str(final_path)
                        else:
                            if attempt < max_retries - 1:
                                time.sleep(2)  # 等待2秒后重试
                                continue
                            else:
                                raise Exception("下载文件为空或不存在")
                                
                except Exception as e:
                    if attempt < max_retries - 1:
                        time.sleep(2)  # 等待2秒后重试
                        continue
                    else:
                        raise e
                        
            return None
            
        except Exception as e:
            raise Exception(f"下载失败: {str(e)}")
            
    def download_batch(self, urls, download_path, progress_callback=None):
        """批量下载 - 修复版本"""
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
        
    def validate_url(self, url):
        """验证URL格式"""
        bilibili_patterns = [
            r'https?://(www\.)?bilibili\.com/video/[A-Za-z0-9]+',
            r'https?://(www\.)?b23\.tv/[A-Za-z0-9]+',
            r'https?://m\.bilibili\.com/video/[A-Za-z0-9]+'
        ]
        
        for pattern in bilibili_patterns:
            if re.match(pattern, url):
                return True
        return False
