import os
import re
import time
import yt_dlp
import requests
import threading
from pathlib import Path
from urllib.parse import urlparse, parse_qs
from PyQt5.QtCore import QThread, pyqtSignal, QMutex, QObject

class DownloadProgressHandler(QObject):
    """下载进度处理器"""
    progress = pyqtSignal(str, int)  # url, 进度百分比
    status = pyqtSignal(str, str)    # url, 状态信息
    finished = pyqtSignal(str, str)  # url, 文件路径
    error = pyqtSignal(str, str)     # url, 错误信息
    
    def __init__(self):
        super().__init__()
        self._mutex = QMutex()
        self._active_downloads = {}

class DownloadThread(QThread):
    """下载线程"""
    progress = pyqtSignal(str, int)  # url, 进度百分比
    status = pyqtSignal(str, str)    # url, 状态信息
    finished = pyqtSignal(str, str)  # url, 文件路径
    error = pyqtSignal(str, str)     # url, 错误信息
    
    def __init__(self, url, download_path, downloader, parent=None):
        super().__init__(parent)
        self.url = url
        self.download_path = Path(download_path)
        self.downloader = downloader
        self._is_running = True
        self._is_paused = False
        self._mutex = QMutex()
        self.current_progress = 0
        
    def run(self):
        """主下载逻辑"""
        try:
            if not self._is_running:
                return
                
            # 验证URL
            if not self.validate_url(self.url):
                self.error.emit(self.url, "无效的B站视频链接")
                return
                
            # 更新状态为"解析中"
            self.status.emit(self.url, "解析视频信息")
            self.progress.emit(self.url, 10)
            
            # 提取视频信息
            try:
                video_info = self.downloader.extract_video_info(self.url)
                if not video_info:
                    self.error.emit(self.url, "无法获取视频信息")
                    return
                    
                self.status.emit(self.url, f"解析成功: {video_info.get('title', '未知标题')}")
                self.progress.emit(self.url, 20)
                
            except Exception as e:
                self.error.emit(self.url, f"视频信息解析失败: {str(e)}")
                return
                
            # 检查下载路径
            self.download_path.mkdir(parents=True, exist_ok=True)
            
            # 下载音频
            if not self._is_running:
                return
                
            self.status.emit(self.url, "开始下载音频")
            self.progress.emit(self.url, 30)
            
            # 使用yt-dlp下载
            file_path = self.download_with_ytdlp(self.url, str(self.download_path))
            
            if self._is_running and file_path and Path(file_path).exists():
                file_size = Path(file_path).stat().st_size
                if file_size > 0:
                    self.progress.emit(self.url, 100)
                    self.status.emit(self.url, "下载完成")
                    self.finished.emit(self.url, file_path)
                else:
                    self.error.emit(self.url, "下载文件为空")
            else:
                self.error.emit(self.url, "下载被取消或文件不存在")
                
        except Exception as e:
            error_msg = f"下载过程中发生错误: {str(e)}"
            self.error.emit(self.url, error_msg)
            
    def validate_url(self, url):
        """验证URL格式"""
        bilibili_patterns = [
            r'https?://(www\.)?bilibili\.com/video/[A-Za-z0-9]+',
            r'https?://(www\.)?b23\.tv/[A-Za-z0-9]+',
            r'https?://m\.bilibili\.com/video/[A-Za-z0-9]+',
            r'https?://bilibili\.com/video/BV[a-zA-Z0-9]+',
            r'https?://www\.bilibili\.com/video/BV[a-zA-Z0-9]+',
            r'https?://b23\.tv/BV[a-zA-Z0-9]+'
        ]
        
        for pattern in bilibili_patterns:
            if re.match(pattern, url, re.IGNORECASE):
                return True
        return False
        
    def download_with_ytdlp(self, url, download_path):
        """使用yt-dlp下载音频"""
        try:
            # 配置yt-dlp选项
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': os.path.join(download_path, '%(title)s.%(ext)s'),
                'restrictfilenames': True,
                'noplaylist': True,
                'nocheckcertificate': True,
                'ignoreerrors': False,
                'logtostderr': False,
                'quiet': True,
                'no_warnings': True,
                'extractaudio': True,
                'audioformat': 'mp3',
                'audioquality': '192',
                'prefer_ffmpeg': True,
                'keepvideo': False,
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'progress_hooks': [self.ytdlp_progress_hook],
                'socket_timeout': 30,
                'retries': 3,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # 提取信息获取文件名
                info = ydl.extract_info(url, download=False)
                original_title = info.get('title', 'download')
                
                # 清理文件名
                safe_title = self.sanitize_filename(original_title)
                expected_path = os.path.join(download_path, f"{safe_title}.mp3")
                
                # 如果文件已存在，添加数字后缀
                counter = 1
                while os.path.exists(expected_path):
                    expected_path = os.path.join(download_path, f"{safe_title}_{counter}.mp3")
                    counter += 1
                
                # 设置最终输出模板
                ydl_opts['outtmpl'] = os.path.join(download_path, f"{safe_title}.%(ext)s")
                
                # 重新创建ydl实例
                with yt_dlp.YoutubeDL(ydl_opts) as final_ydl:
                    final_ydl.download([url])
                
                # 检查文件是否生成
                if os.path.exists(expected_path):
                    return expected_path
                else:
                    # 尝试查找实际生成的文件
                    for ext in ['.mp3', '.webm', '.m4a']:
                        possible_path = os.path.join(download_path, f"{safe_title}{ext}")
                        if os.path.exists(possible_path):
                            return possible_path
                    
                    return None
                    
        except yt_dlp.DownloadError as e:
            if "Unable to download webpage" in str(e):
                raise Exception("网络连接失败，请检查网络设置")
            elif "Video unavailable" in str(e):
                raise Exception("视频不可用或已被删除")
            elif "Private video" in str(e):
                raise Exception("视频为私密视频，无法访问")
            elif "Sign in to confirm" in str(e):
                raise Exception("该视频需要登录才能观看")
            else:
                raise Exception(f"下载失败: {str(e)}")
        except Exception as e:
            raise Exception(f"下载错误: {str(e)}")
            
    def ytdlp_progress_hook(self, d):
        """yt-dlp进度回调"""
        if not self._is_running:
            raise Exception("下载已取消")
            
        if d['status'] == 'downloading':
            # 计算进度百分比
            if d.get('total_bytes'):
                percent = int(d['downloaded_bytes'] * 100 / d['total_bytes'])
            elif d.get('total_bytes_estimate'):
                percent = int(d['downloaded_bytes'] * 100 / d['total_bytes_estimate'])
            else:
                percent = self.current_progress + 1
                
            # 确保进度在合理范围内
            percent = max(30, min(95, percent))
            self.current_progress = percent
            
            self.progress.emit(self.url, percent)
            speed = d.get('speed', 0)
            if speed:
                speed_str = self.format_speed(speed)
                self.status.emit(self.url, f"下载中 {percent}% ({speed_str})")
            else:
                self.status.emit(self.url, f"下载中 {percent}%")
                
        elif d['status'] == 'finished':
            self.progress.emit(self.url, 98)
            self.status.emit(self.url, "处理音频文件")
            
        elif d['status'] == 'error':
            raise Exception(f"下载错误: {d.get('error', '未知错误')}")
            
    def format_speed(self, speed_bytes):
        """格式化速度显示"""
        if speed_bytes < 1024:
            return f"{speed_bytes} B/s"
        elif speed_bytes < 1024 * 1024:
            return f"{speed_bytes/1024:.1f} KB/s"
        else:
            return f"{speed_bytes/(1024 * 1024):.1f} MB/s"
            
    def sanitize_filename(self, filename):
        """清理文件名中的非法字符"""
        # 移除Windows文件名中的非法字符
        filename = re.sub(r'[<>:"/\\|?*]', '', filename)
        # 移除或替换其他可能的问题字符
        filename = re.sub(r'[\\/\n\r\t]', ' ', filename)
        # 移除首尾空格和点
        filename = filename.strip().strip('.')
        # 限制文件名长度
        if len(filename) > 100:
            filename = filename[:100]
        return filename
        
    def stop(self):
        """停止下载"""
        self._mutex.lock()
        self._is_running = False
        self._mutex.unlock()
        
    def pause(self):
        """暂停下载"""
        self._mutex.lock()
        self._is_paused = True
        self._mutex.unlock()
        
    def resume(self):
        """继续下载"""
        self._mutex.lock()
        self._is_paused = False
        self._mutex.unlock()
        
    def is_running(self):
        """检查是否运行中"""
        self._mutex.lock()
        running = self._is_running
        self._mutex.unlock()
        return running
        
    def is_paused(self):
        """检查是否暂停"""
        self._mutex.lock()
        paused = self._is_paused
        self._mutex.unlock()
        return paused

class BilibiliDownloader:
    def __init__(self):
        self.session = requests.Session()
        # 设置请求头模拟浏览器
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Referer': 'https://www.bilibili.com/',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
        })
        
    def extract_video_info(self, url):
        """提取视频信息"""
        try:
            # 验证URL
            if not self.validate_url(url):
                raise Exception("无效的B站视频链接")
                
            # 使用yt-dlp提取信息
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                try:
                    info = ydl.extract_info(url, download=False)
                    if not info:
                        raise Exception("无法获取视频信息")
                        
                    # 计算时长
                    duration = info.get('duration', 0)
                    if duration:
                        duration_str = self.format_duration(duration)
                    else:
                        duration_str = "未知"
                        
                    return {
                        'title': info.get('title', '未知标题'),
                        'duration': duration_str,
                        'duration_seconds': duration,
                        'uploader': info.get('uploader', '未知上传者'),
                        'thumbnail': info.get('thumbnail', ''),
                        'description': info.get('description', '')[:100] + '...' if info.get('description') else '',
                        'webpage_url': info.get('webpage_url', url),
                        'view_count': info.get('view_count', 0),
                        'like_count': info.get('like_count', 0),
                        'upload_date': info.get('upload_date', ''),
                    }
                except yt_dlp.DownloadError as e:
                    error_msg = str(e)
                    if "Unable to download webpage" in error_msg:
                        raise Exception("网络连接失败，请检查网络设置")
                    elif "Video unavailable" in error_msg:
                        raise Exception("视频不可用或已被删除")
                    elif "Private video" in error_msg:
                        raise Exception("视频为私密视频，无法访问")
                    elif "Sign in to confirm" in error_msg:
                        raise Exception("该视频需要登录才能观看")
                    else:
                        raise Exception(f"解析失败: {error_msg}")
                except Exception as e:
                    raise Exception(f"视频信息提取失败: {str(e)}")
                    
        except Exception as e:
            raise Exception(f"获取视频信息时发生错误: {str(e)}")
            
    def validate_url(self, url):
        """验证URL格式"""
        bilibili_patterns = [
            r'https?://(www\.)?bilibili\.com/video/[A-Za-z0-9]+',
            r'https?://(www\.)?b23\.tv/[A-Za-z0-9]+',
            r'https?://m\.bilibili\.com/video/[A-Za-z0-9]+',
            r'https?://bilibili\.com/video/BV[a-zA-Z0-9]+',
            r'https?://www\.bilibili\.com/video/BV[a-zA-Z0-9]+',
        ]
        
        for pattern in bilibili_patterns:
            if re.match(pattern, url, re.IGNORECASE):
                return True
        return False
        
    def format_duration(self, seconds):
        """格式化时长"""
        if not seconds:
            return "00:00"
            
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        seconds = seconds % 60
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes:02d}:{seconds:02d}"
            
    def test_connection(self):
        """测试网络连接"""
        try:
            response = self.session.get("https://www.bilibili.com", timeout=10)
            return response.status_code == 200
        except:
            return False
            
    def get_supported_domains(self):
        """获取支持的域名列表"""
        return [
            "bilibili.com",
            "b23.tv", 
            "m.bilibili.com"
        ]
