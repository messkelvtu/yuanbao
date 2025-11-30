from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QTextEdit, QPushButton, QLineEdit)

class LyricsWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("歌词管理")
        self.setGeometry(200, 200, 500, 400)
        
        layout = QVBoxLayout(self)
        
        # 歌词显示区域
        self.lyric_display = QTextEdit()
        self.lyric_display.setPlaceholderText("歌词将在这里显示...")
        layout.addWidget(self.lyric_display)
        
        # 操作按钮
        btn_layout = QHBoxLayout()
        self.search_btn = QPushButton("搜索歌词")
        self.download_btn = QPushButton("下载歌词")
        self.close_btn = QPushButton("关闭")
        
        for btn in [self.search_btn, self.download_btn, self.close_btn]:
            btn_layout.addWidget(btn)
            
        layout.addLayout(btn_layout)
