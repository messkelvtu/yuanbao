from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLineEdit, QLabel, QMessageBox)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("B站音乐提取器")
        self.setGeometry(100, 100, 800, 600)
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        layout = QVBoxLayout(central_widget)
        
        # 添加一些基本控件
        title_label = QLabel("B站音乐提取器")
        layout.addWidget(title_label)
        
        # URL输入框
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("粘贴哔哩哔哩视频链接...")
        layout.addWidget(self.url_input)
        
        # 下载按钮
        download_layout = QHBoxLayout()
        self.single_download_btn = QPushButton("单曲下载")
        self.batch_download_btn = QPushButton("批量下载")
        download_layout.addWidget(self.single_download_btn)
        download_layout.addWidget(self.batch_download_btn)
        layout.addLayout(download_layout)
        
        # 状态标签
        self.status_label = QLabel("就绪")
        layout.addWidget(self.status_label)
        
        layout.addStretch()
        
        # 连接信号
        self.single_download_btn.clicked.connect(self.download_single)
        self.batch_download_btn.clicked.connect(self.download_batch)
        
    def download_single(self):
        """单曲下载"""
        url = self.url_input.text().strip()
        if url:
            QMessageBox.information(self, "信息", f"开始下载: {url}")
        else:
            QMessageBox.warning(self, "警告", "请输入B站视频链接")
            
    def download_batch(self):
        """批量下载"""
        QMessageBox.information(self, "信息", "批量下载功能")
