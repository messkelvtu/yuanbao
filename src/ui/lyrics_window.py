from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QTextEdit, QPushButton, QLineEdit, QListWidget,
                             QProgressBar, QMessageBox)
from PyQt5.QtCore import Qt

class LyricsWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("歌词管理")
        self.setGeometry(200, 200, 600, 500)
        self.init_ui()
        
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
        self.lyric_display = QTextEdit()
        self.lyric_display.setPlaceholderText("歌词将在这里显示...")
        layout.addWidget(self.lyric_display)
        
        # 歌词搜索
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("搜索歌词...")
        self.search_btn = QPushButton("搜索")
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.search_btn)
        layout.addLayout(search_layout)
        
        # 搜索结果列表
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
        
    def auto_match_lyrics(self):
        """自动匹配歌词"""
        # TODO: 调用歌词匹配功能
        QMessageBox.information(self, "提示", "开始自动匹配歌词...")
        
    def search_lyrics(self):
        """搜索歌词"""
        keyword = self.search_input.text().strip()
        if keyword:
            # TODO: 调用歌词搜索功能
            pass
            
    def download_lyrics(self):
        """下载歌词"""
        # TODO: 实现歌词下载
        pass
        
    def save_lyrics(self):
        """保存歌词"""
        # TODO: 保存歌词到文件
        pass
