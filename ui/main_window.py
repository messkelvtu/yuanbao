from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLineEdit, QListWidget, QTabWidget,
                             QLabel, QProgressBar, QMenuBar, QMenu, QAction,
                             QSplitter, QTreeWidget, QTreeWidgetItem, QHeaderView,
                             QToolBar, QMessageBox, QFileDialog, QInputDialog)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QIcon
import os

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.setup_connections()
        
    def init_ui(self):
        self.setWindowTitle("B站音乐提取器")
        self.setGeometry(100, 100, 1200, 800)
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QHBoxLayout(central_widget)
        
        # 左侧功能面板
        left_panel = self.create_left_panel()
        main_layout.addWidget(left_panel)
        
        # 右侧主内容区域
        right_panel = self.create_right_panel()
        main_layout.addWidget(right_panel)
        
        # 创建菜单栏
        self.create_menu_bar()
        
        # 创建工具栏
        self.create_tool_bar()
        
    def create_left_panel(self):
        """创建左侧功能面板"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # 下载功能区域
        download_group = QWidget()
        download_layout = QVBoxLayout(download_group)
        
        # URL输入
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("粘贴哔哩哔哩视频链接...")
        download_layout.addWidget(QLabel("视频链接:"))
        download_layout.addWidget(self.url_input)
        
        # 下载按钮
        btn_layout = QHBoxLayout()
        self.single_download_btn = QPushButton("单曲下载")
        self.batch_download_btn = QPushButton("批量下载")
        btn_layout.addWidget(self.single_download_btn)
        btn_layout.addWidget(self.batch_download_btn)
        download_layout.addLayout(btn_layout)
        
        # 下载进度
        self.progress_bar = QProgressBar()
        download_layout.addWidget(self.progress_bar)
        
        layout.addWidget(download_group)
        
        # 分类管理
        category_group = QWidget()
        category_layout = QVBoxLayout(category_group)
        category_layout.addWidget(QLabel("分类管理:"))
        
        self.category_tree = QTreeWidget()
        self.category_tree.setHeaderLabel("音乐分类")
        category_layout.addWidget(self.category_tree)
        
        # 分类操作按钮
        category_btn_layout = QHBoxLayout()
        self.add_category_btn = QPushButton("添加分类")
        self.edit_category_btn = QPushButton("编辑")
        self.del_category_btn = QPushButton("删除")
        category_btn_layout.addWidget(self.add_category_btn)
        category_btn_layout.addWidget(self.edit_category_btn)
        category_btn_layout.addWidget(self.del_category_btn)
        category_layout.addLayout(category_btn_layout)
        
        layout.addWidget(category_group)
        layout.addStretch()
        
        return panel
        
    def create_right_panel(self):
        """创建右侧主内容区域"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # 选项卡
        self.tab_widget = QTabWidget()
        
        # 音乐库标签页
        self.music_library_tab = self.create_music_library_tab()
        self.tab_widget.addTab(self.music_library_tab, "音乐库")
        
        # 下载队列标签页
        self.download_queue_tab = self.create_download_queue_tab()
        self.tab_widget.addTab(self.download_queue_tab, "下载队列")
        
        layout.addWidget(self.tab_widget)
        
        return panel
        
    def create_music_library_tab(self):
        """创建音乐库标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 工具栏
        toolbar = QHBoxLayout()
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("搜索歌曲...")
        toolbar.addWidget(self.search_input)
        
        self.batch_ops_layout = QHBoxLayout()
        self.select_all_btn = QPushButton("全选")
        self.rename_btn = QPushButton("重命名")
        self.move_btn = QPushButton("移动")
        self.delete_btn = QPushButton("删除")
        self.lyric_btn = QPushButton("歌词管理")
        
        for btn in [self.select_all_btn, self.rename_btn, self.move_btn, 
                   self.delete_btn, self.lyric_btn]:
            self.batch_ops_layout.addWidget(btn)
            
        toolbar.addLayout(self.batch_ops_layout)
        layout.addLayout(toolbar)
        
        # 歌曲列表
        self.song_list = QTreeWidget()
        self.song_list.setHeaderLabels(["", "歌曲名", "歌手", "风格", "时长", "大小"])
        self.song_list.header().setSectionResizeMode(QHeaderView.ResizeToContents)
        layout.addWidget(self.song_list)
        
        # 状态栏信息
        self.status_label = QLabel("总共 0 首歌曲")
        layout.addWidget(self.status_label)
        
        return tab
        
    def create_download_queue_tab(self):
        """创建下载队列标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        self.download_list = QTreeWidget()
        self.download_list.setHeaderLabels(["歌曲名", "状态", "进度", "操作"])
        layout.addWidget(self.download_list)
        
        return tab
        
    def create_menu_bar(self):
        """创建菜单栏"""
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu("文件")
        
        import_action = QAction("导入音乐", self)
        export_action = QAction("导出列表", self)
        exit_action = QAction("退出", self)
        
        file_menu.addAction(import_action)
        file_menu.addAction(export_action)
        file_menu.addSeparator()
        file_menu.addAction(exit_action)
        
        # 工具菜单
        tool_menu = menubar.addMenu("工具")
        settings_action = QAction("设置", self)
        tool_menu.addAction(settings_action)
        
    def create_tool_bar(self):
        """创建工具栏"""
        toolbar = self.addToolBar("主工具栏")
        
        # 添加工具按钮
        refresh_act = QAction("刷新", self)
        settings_act = QAction("设置", self)
        help_act = QAction("帮助", self)
        
        toolbar.addAction(refresh_act)
        toolbar.addAction(settings_act)
        toolbar.addAction(help_act)
        
    def setup_connections(self):
        """设置信号槽连接"""
        self.single_download_btn.clicked.connect(self.download_single)
        self.batch_download_btn.clicked.connect(self.download_batch)
        self.add_category_btn.clicked.connect(self.add_category)
        self.lyric_btn.clicked.connect(self.open_lyric_manager)
        
    def download_single(self):
        """单曲下载"""
        url = self.url_input.text().strip()
        if not url:
            QMessageBox.warning(self, "警告", "请输入有效的B站视频链接")
            return
            
        # TODO: 调用下载核心功能
        print(f"开始下载单曲: {url}")
        
    def download_batch(self):
        """批量下载"""
        urls, ok = QInputDialog.getMultiLineText(self, "批量下载", 
                                                "请输入多个B站视频链接(每行一个):")
        if ok and urls:
            # TODO: 调用批量下载功能
            url_list = [url.strip() for url in urls.split('\n') if url.strip()]
            print(f"开始批量下载: {len(url_list)} 个视频")
            
    def add_category(self):
        """添加分类"""
        name, ok = QInputDialog.getText(self, "添加分类", "请输入分类名称:")
        if ok and name:
            # TODO: 添加到分类树
            pass
            
    def open_lyric_manager(self):
        """打开歌词管理器"""
        from ui.lyrics_window import LyricsWindow
        self.lyrics_window = LyricsWindow()
        self.lyrics_window.show()

if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
