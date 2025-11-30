import requests
import socket
import time
from PyQt5.QtCore import QThread, pyqtSignal

class NetworkChecker(QThread):
    """网络检查线程"""
    result = pyqtSignal(bool, str)
    
    def __init__(self):
        super().__init__()
        
    def run(self):
        """执行网络检查"""
        try:
            # 测试基本网络连接
            self.result.emit(True, "正在检查网络连接...")
            time.sleep(0.5)
            
            # 测试DNS解析
            self.result.emit(True, "正在解析域名...")
            try:
                socket.getaddrinfo("www.bilibili.com", 80)
            except socket.gaierror:
                self.result.emit(False, "域名解析失败")
                return
                
            time.sleep(0.5)
            
            # 测试B站连接
            self.result.emit(True, "正在连接B站...")
            try:
                response = requests.get(
                    "https://www.bilibili.com", 
                    timeout=10,
                    headers={
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                    }
                )
                if response.status_code == 200:
                    self.result.emit(True, "网络连接正常，B站可访问")
                else:
                    self.result.emit(False, f"B站访问异常 (状态码: {response.status_code})")
            except requests.exceptions.Timeout:
                self.result.emit(False, "连接超时，请检查网络设置")
            except requests.exceptions.ConnectionError:
                self.result.emit(False, "网络连接失败，请检查网络连接")
            except Exception as e:
                self.result.emit(False, f"网络检查失败: {str(e)}")
                
        except Exception as e:
            self.result.emit(False, f"网络诊断异常: {str(e)}")
