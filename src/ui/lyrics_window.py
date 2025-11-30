from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QTextEdit, QPushButton, QLineEdit, QListWidget,
                             QProgressBar, QMessageBox, QListWidgetItem)
from PyQt5.QtCore import Qt, QThread, pyqtSignal

class LyricSearchThread(QThread):
    """歌词搜索线程"""
    finished = pyqtSignal(list)
    error = pyqtSignal(str)
    
    def __init__(self, song_name, artist=""):
        super().__init__()
        self.song_name = song_name
        self.artist = artist
        
    def run(self):
        try:
            lyrics = self.search_lyrics(self.song_name, self.artist)
            self.finished.emit(lyrics)
        except Exception as e:
            self.error.emit(str(e))
            
    def search_lyrics(self, song_name, artist=""):
        """搜索歌词"""
        # 这里使用模拟数据，实际应用中应该调用真实的歌词API
        # 例如网易云音乐API、QQ音乐API等
        
        # 模拟搜索结果
        results = []
        
        if song_name:
            # 模拟从不同来源获取歌词
            sources = [
                {"source": "网易云音乐", "lyric": f"[00:00.00]{song_name} - 歌词\n[00:05.00]第一行歌词\n[00:10.00]第二行歌词"},
                {"source": "QQ音乐", "lyric": f"[00:00.00]{song_name} 歌词\n[00:05.00]QQ音乐版本歌词第一行\n[00:10.00]QQ音乐版本歌词第二行"},
                {"source": "酷狗音乐", "lyric": f"[00:00.00]酷狗音乐-{song_name}\n[00:05.00]酷狗版本歌词第一行\n[00:10.00]酷狗版本歌词第二行"}
            ]
            
            for source in sources:
                results.append({
                    "title": f"{song_name} - {source['source']}",
                    "lyric": source['lyric'],
                    "source": source['source']
                })
                
        return results

class LyricsWindow(QDialog):
    def __init__(self, song_path, lyric_matcher, parent=None):
        super().__init__(parent)
        self.song_path = song_path
        self.lyric_matcher = lyric_matcher
        self.current_lyric = ""
        
        self.setWindowTitle("歌词管理")
        self.setGeometry(200, 200, 600, 500)
        self.init_ui()
        self.load_song_info()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # 当前歌曲信息
        song_info_layout = QHBoxLayout()
        song_info_layout.addWidget(QLabel("当前歌曲:"))
        self.song_label = QLabel("未知歌曲")
        song_info_layout.addWidget(self.song_label)
        song_info_layout.addStretch()
        
        layout.addLayout(song_info_layout)
        
        # 歌词显示区域
        layout.addWidget(QLabel("歌词:"))
        self.lyric_display = QTextEdit()
        self.lyric_display.setPlaceholderText("歌词将在这里显示...")
        layout.addWidget(self.lyric_display)
        
        # 歌词搜索
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("搜索歌词...")
        self.search_btn = QPushButton("搜索")
        search_layout.addWidget(QLabel("搜索:"))
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.search_btn)
        layout.addLayout(search_layout)
        
        # 搜索结果列表
        layout.addWidget(QLabel("搜索结果:"))
        self.result_list = QListWidget()
        layout.addWidget(self.result_list)
        
        # 操作按钮
        btn_layout = QHBoxLayout()
        self.match_btn = QPushButton("自动匹配")
        self.download_btn = QPushButton("下载歌词")
        self.save_btn = QPushButton("保存歌词")
        self.close_btn = QPushButton("关闭")
        
        for btn in [self.match_btn, self.download_btn, self.save_btn, self.close_btn]:
            btn_layout.addWidget(btn)
            
        layout.addLayout(btn_layout)
        
        # 连接信号
        self.setup_connections()
        
    def setup_connections(self):
        self.match_btn.clicked.connect(self.auto_match_lyrics)
        self.search_btn.clicked.connect(self.search_lyrics)
        self.download_btn.clicked.connect(self.download_lyrics)
        self.save_btn.clicked.connect(self.save_lyrics)
        self.close_btn.clicked.connect(self.close)
        self.result_list.itemClicked.connect(self.on_lyric_selected)
        
    def load_song_info(self):
        """加载歌曲信息"""
        try:
            song_info = self.lyric_matcher.get_song_info(self.song_path)
            song_name = song_info.get('title', self.song_path.stem)
            artist = song_info.get('artist', '未知歌手')
            
            self.song_label.setText(f"{song_name} - {artist}")
            self.search_input.setText(f"{song_name} {artist}")
            
            # 尝试加载现有歌词
            self.load_existing_lyric()
        except Exception as e:
            self.song_label.setText(f"{self.song_path.stem}")
            self.search_input.setText(f"{self.song_path.stem}")
            
    def load_existing_lyric(self):
        """加载现有歌词"""
        try:
            lrc_path = self.song_path.with_suffix('.lrc')
            if lrc_path.exists():
                with open(lrc_path, 'r', encoding='utf-8') as f:
                    self.current_lyric = f.read()
                    self.lyric_display.setPlainText(self.current_lyric)
        except:
            pass
                
    def auto_match_lyrics(self):
        """自动匹配歌词"""
        song_info = self.lyric_matcher.get_song_info(self.song_path)
        song_name = song_info.get('title', self.song_path.stem)
        artist = song_info.get('artist', '')
        
        QMessageBox.information(self, "提示", f"开始为 {song_name} 自动匹配歌词...")
        
        # 启动搜索线程
        self.search_thread = LyricSearchThread(song_name, artist)
        self.search_thread.finished.connect(self.on_lyrics_found)
        self.search_thread.error.connect(self.on_lyric_error)
        self.search_thread.start()
        
        self.match_btn.setEnabled(False)
        self.match_btn.setText("搜索中...")
        
    def search_lyrics(self):
        """搜索歌词"""
        keyword = self.search_input.text().strip()
        if not keyword:
            QMessageBox.warning(self, "警告", "请输入搜索关键词")
            return
            
        QMessageBox.information(self, "提示", f"开始搜索歌词: {keyword}")
        
        # 启动搜索线程
        self.search_thread = LyricSearchThread(keyword)
        self.search_thread.finished.connect(self.on_lyrics_found)
        self.search_thread.error.connect(self.on_lyric_error)
        self.search_thread.start()
        
        self.search_btn.setEnabled(False)
        self.search_btn.setText("搜索中...")
        
    def on_lyrics_found(self, lyrics):
        """歌词搜索完成"""
        self.result_list.clear()
        
        for lyric in lyrics:
            item = QListWidgetItem(lyric['title'])
            item.setData(Qt.UserRole, lyric)
            self.result_list.addItem(item)
            
        self.match_btn.setEnabled(True)
        self.match_btn.setText("自动匹配")
        self.search_btn.setEnabled(True)
        self.search_btn.setText("搜索")
        
        if not lyrics:
            QMessageBox.information(self, "提示", "未找到相关歌词")
            
    def on_lyric_error(self, error_msg):
        """歌词搜索错误"""
        QMessageBox.warning(self, "错误", f"搜索歌词时发生错误: {error_msg}")
        
        self.match_btn.setEnabled(True)
        self.match_btn.setText("自动匹配")
        self.search_btn.setEnabled(True)
        self.search_btn.setText("搜索")
        
    def on_lyric_selected(self, item):
        """选择歌词"""
        lyric_data = item.data(Qt.UserRole)
        if lyric_data:
            self.current_lyric = lyric_data['lyric']
            self.lyric_display.setPlainText(self.current_lyric)
            
    def download_lyrics(self):
        """下载歌词"""
        if not self.current_lyric:
            QMessageBox.warning(self, "警告", "请先选择或输入歌词")
            return
            
        QMessageBox.information(self, "提示", "歌词下载功能")
        # 实际应用中这里应该调用歌词下载逻辑
        
    def save_lyrics(self):
        """保存歌词"""
        if not self.current_lyric:
            QMessageBox.warning(self, "警告", "没有歌词可保存")
            return
            
        # 保存为LRC文件
        lrc_path = self.song_path.with_suffix('.lrc')
        
        try:
            with open(lrc_path, 'w', encoding='utf-8') as f:
                f.write(self.current_lyric)
                
            QMessageBox.information(self, "成功", f"歌词已保存到: {lrc_path}")
        except Exception as e:
            QMessageBox.warning(self, "错误", f"保存歌词失败: {str(e)}")
