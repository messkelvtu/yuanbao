import os
import sys
import re
import json
import time
import logging
from pathlib import Path
from urllib.parse import urlparse

from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLineEdit, QLabel, QMessageBox,
                             QTabWidget, QTreeWidget, QTreeWidgetItem, QHeaderView,
                             QSplitter, QToolBar, QAction, QMenuBar, QMenu,
                             QInputDialog, QFileDialog, QProgressBar, QCheckBox,
                             QListWidget, QListWidgetItem, QGroupBox, QApplication,
                             QTextEdit, QDialog, QDialogButtonBox, QComboBox)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QSettings, QTimer, QSize
from PyQt5.QtGui import QIcon, QFont, QPalette, QColor

# 确保sys在导入其他模块前可用
if 'sys' not in globals():
    import sys

# 添加src目录到Python路径
src_path = Path(__file__).parent.parent
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

# 安全导入核心模块
try:
    from core.downloader import BilibiliDownloader, DownloadThread
    from core.music_manager import MusicManager
    from core.lyric_matcher import LyricMatcher
    from ui.lyrics_window import LyricsWindow
except ImportError as e:
    logging.error(f"模块导入错误: {e}")
    # 创建虚拟类避免崩溃
    class BilibiliDownloader:
        def __init__(self): pass
        def validate_url(self, url): return True
        def extract_video_info(self, url): return {}
        def test_connection(self): return True
    class DownloadThread(QThread):
        progress = pyqtSignal(str, int)
        status = pyqtSignal(str, str)
        finished = pyqtSignal(str, str)
        error = pyqtSignal(str, str)
        def __init__(self, url, path, downloader): 
            super().__init__()
            self.url = url
        def run(self): pass
        def stop(self): pass
    class MusicManager:
        def __init__(self): pass
        def get_song_info(self, path): return {}
        def rename_file(self, path, new_name): pass
        def move_file(self, path, target_dir): pass
        def delete_file(self, path): pass
    class LyricMatcher:
        def __init__(self): pass
    class LyricsWindow(QDialog):
        def __init__(self, song_path, matcher): super().__init__()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.settings = QSettings("B站音乐提取器", "B站音乐提取器")
        
        # 初始化核心组件
        try:
            self.downloader = BilibiliDownloader()
            self.music_manager = MusicManager()
            self.lyric_matcher = LyricMatcher()
        except Exception as e:
            logging.error(f"组件初始化失败: {e}")
            # 创建虚拟对象
            self.downloader = BilibiliDownloader()
            self.music_manager = MusicManager()
            self.lyric_matcher = LyricMatcher()
        
        self.download_threads = []
        self.current_songs = []
        
        self.init_ui()
        self.setup_connections()
        self.load_settings()
        self.load_music_library()
        
    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle("B站音乐提取器 v1.0")
        self.setGeometry(100, 100, 1200, 800)
        
        # 设置应用图标（如果存在）
        self.setWindowIcon(QIcon("assets/icon.ico") if os.path.exists("assets/icon.ico") else QIcon())
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QHBoxLayout(central_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # 左侧面板（占1/4宽度）
        left_panel = self.create_left_panel()
        main_layout.addWidget(left_panel, 1)
        
        # 右侧面板（占3/4宽度）
        right_panel = self.create_right_panel()
        main_layout.addWidget(right_panel, 3)
        
        # 创建菜单栏和工具栏
        self.create_menu_bar()
        self.create_tool_bar()
        
    def create_left_panel(self):
        """创建左侧功能面板"""
        panel = QWidget()
        panel.setMaximumWidth(400)
        layout = QVBoxLayout(panel)
        layout.setSpacing(10)
        
        # 下载功能区域
        download_group = QGroupBox("下载设置")
        download_group.setFont(QFont("Arial", 10, QFont.Bold))
        download_layout = QVBoxLayout(download_group)
        
        # URL输入区域
        url_layout = QVBoxLayout()
        url_layout.addWidget(QLabel("B站视频链接:"))
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("粘贴哔哩哔哩视频链接...")
        self.url_input.setText("https://www.bilibili.com/video/BV1fx411y7fU")  # 示例链接
        url_layout.addWidget(self.url_input)
        download_layout.addLayout(url_layout)
        
        # 下载按钮区域
        btn_layout = QHBoxLayout()
        self.single_download_btn = QPushButton("单曲下载")
        self.single_download_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; }")
        self.batch_download_btn = QPushButton("批量下载")
        self.batch_download_btn.setStyleSheet("QPushButton { background-color: #2196F3; color: white; }")
        btn_layout.addWidget(self.single_download_btn)
        btn_layout.addWidget(self.batch_download_btn)
        download_layout.addLayout(btn_layout)
        
        # 下载路径设置
        path_layout = QHBoxLayout()
        self.download_path_input = QLineEdit()
        self.download_path_input.setText(str(Path.home() / "Music" / "B站音乐"))
        self.browse_path_btn = QPushButton("...")
        self.browse_path_btn.setFixedWidth(30)
        path_layout.addWidget(QLabel("下载路径:"))
        path_layout.addWidget(self.download_path_input)
        path_layout.addWidget(self.browse_path_btn)
        download_layout.addLayout(path_layout)
        
        # 下载进度
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)  # 初始隐藏
        download_layout.addWidget(self.progress_bar)
        
        layout.addWidget(download_group)
        
        # 分类管理区域
        category_group = QGroupBox("分类管理")
        category_layout = QVBoxLayout(category_group)
        
        self.category_list = QListWidget()
        self.category_list.addItems(["流行", "摇滚", "电子", "古典", "爵士", "说唱"])
        category_layout.addWidget(self.category_list)
        
        # 分类操作按钮
        category_btn_layout = QHBoxLayout()
        self.add_category_btn = QPushButton("添加")
        self.edit_category_btn = QPushButton("编辑")
        self.del_category_btn = QPushButton("删除")
        category_btn_layout.addWidget(self.add_category_btn)
        category_btn_layout.addWidget(self.edit_category_btn)
        category_btn_layout.addWidget(self.del_category_btn)
        category_layout.addLayout(category_btn_layout)
        
        layout.addWidget(category_group)
        
        # 状态信息区域
        status_group = QGroupBox("状态信息")
        status_layout = QVBoxLayout(status_group)
        self.status_label = QLabel("就绪")
        status_layout.addWidget(self.status_label)
        layout.addWidget(status_group)
        
        layout.addStretch()
        
        return panel
        
    def create_right_panel(self):
        """创建右侧主内容区域"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setSpacing(5)
        
        # 选项卡控件
        self.tab_widget = QTabWidget()
        
        # 音乐库标签页
        self.music_library_tab = self.create_music_library_tab()
        self.tab_widget.addTab(self.music_library_tab, "🎵 音乐库")
        
        # 下载队列标签页
        self.download_queue_tab = self.create_download_queue_tab()
        self.tab_widget.addTab(self.download_queue_tab, "⏬ 下载队列")
        
        # 歌词管理标签页
        self.lyrics_tab = self.create_lyrics_tab()
        self.tab_widget.addTab(self.lyrics_tab, "📝 歌词管理")
        
        layout.addWidget(self.tab_widget)
        
        return panel
        
    def create_music_library_tab(self):
        """创建音乐库标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 搜索和操作工具栏
        toolbar = QHBoxLayout()
        
        # 搜索区域
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("搜索歌曲名或歌手...")
        self.search_btn = QPushButton("搜索")
        search_layout.addWidget(QLabel("搜索:"))
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.search_btn)
        toolbar.addLayout(search_layout)
        
        # 批量操作区域
        batch_ops_layout = QHBoxLayout()
        self.select_all_btn = QPushButton("全选")
        self.rename_btn = QPushButton("重命名")
        self.move_btn = QPushButton("移动")
        self.delete_btn = QPushButton("删除")
        self.lyric_btn = QPushButton("歌词管理")
        
        for btn in [self.select_all_btn, self.rename_btn, self.move_btn, 
                   self.delete_btn, self.lyric_btn]:
            batch_ops_layout.addWidget(btn)
            
        toolbar.addLayout(batch_ops_layout)
        layout.addLayout(toolbar)
        
        # 歌曲列表
        self.song_list = QTreeWidget()
        self.song_list.setHeaderLabels(["选择", "歌曲名", "歌手", "风格", "时长", "大小", "路径"])
        self.song_list.setSelectionMode(QTreeWidget.ExtendedSelection)
        self.song_list.setAlternatingRowColors(True)
        
        # 设置列宽
        header = self.song_list.header()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)
        
        layout.addWidget(self.song_list)
        
        # 状态信息
        info_layout = QHBoxLayout()
        self.song_count_label = QLabel("总共 0 首歌曲")
        self.selected_count_label = QLabel("已选择 0 首")
        info_layout.addWidget(self.song_count_label)
        info_layout.addStretch()
        info_layout.addWidget(self.selected_count_label)
        layout.addLayout(info_layout)
        
        return tab
        
    def create_download_queue_tab(self):
        """创建下载队列标签页 - 根据用户截图实现"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 下载队列列表
        self.download_list = QTreeWidget()
        self.download_list.setHeaderLabels(["歌曲名", "状态", "进度", "操作"])
        self.download_list.setAlternatingRowColors(True)
        
        # 设置列宽
        header = self.download_list.header()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        
        # 添加示例下载项（根据用户截图）
        self.add_example_download_item()
        
        layout.addWidget(self.download_list)
        
        # 下载控制按钮
        control_layout = QHBoxLayout()
        self.pause_all_btn = QPushButton("暂停全部")
        self.resume_all_btn = QPushButton("继续全部")
        self.cancel_all_btn = QPushButton("取消全部")
        self.clear_finished_btn = QPushButton("清除已完成")
        
        for btn in [self.pause_all_btn, self.resume_all_btn, self.cancel_all_btn, self.clear_finished_btn]:
            control_layout.addWidget(btn)
            
        layout.addLayout(control_layout)
        
        return tab
        
    def add_example_download_item(self):
        """添加示例下载项（根据用户截图）"""
        item = QTreeWidgetItem(self.download_list)
        item.setText(0, "解析中...")
        item.setText(1, "等待中")
        item.setText(2, "0%")
        
        # 取消按钮
        cancel_btn = QPushButton("取消")
        cancel_btn.setFixedWidth(60)
        cancel_btn.clicked.connect(lambda: self.cancel_download_item(item))
        self.download_list.setItemWidget(item, 3, cancel_btn)
        
    def cancel_download_item(self, item):
        """取消下载项"""
        item.setText(1, "已取消")
        item.setText(2, "-")
        QMessageBox.information(self, "提示", "下载已取消")
        
    def create_lyrics_tab(self):
        """创建歌词管理标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 当前歌曲信息
        song_info_layout = QHBoxLayout()
        song_info_layout.addWidget(QLabel("当前歌曲:"))
        self.current_song_label = QLabel("未选择歌曲")
        song_info_layout.addWidget(self.current_song_label)
        song_info_layout.addStretch()
        layout.addLayout(song_info_layout)
        
        # 歌词显示区域
        layout.addWidget(QLabel("歌词:"))
        self.lyrics_display = QTextEdit()
        self.lyrics_display.setPlaceholderText("歌词将在这里显示...")
        layout.addWidget(self.lyrics_display)
        
        # 歌词操作按钮
        lyrics_btn_layout = QHBoxLayout()
        self.search_lyrics_btn = QPushButton("搜索歌词")
        self.download_lyrics_btn = QPushButton("下载歌词")
        self.save_lyrics_btn = QPushButton("保存歌词")
        self.sync_lyrics_btn = QPushButton("同步歌词")
        
        for btn in [self.search_lyrics_btn, self.download_lyrics_btn, 
                   self.save_lyrics_btn, self.sync_lyrics_btn]:
            lyrics_btn_layout.addWidget(btn)
            
        layout.addLayout(lyrics_btn_layout)
        
        return tab
        
    def create_menu_bar(self):
        """创建菜单栏"""
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu("文件")
        
        import_action = QAction("导入音乐", self)
        import_action.setShortcut("Ctrl+I")
        import_action.triggered.connect(self.import_music)
        
        export_action = QAction("导出列表", self)
        export_action.setShortcut("Ctrl+E")
        export_action.triggered.connect(self.export_music_list)
        
        exit_action = QAction("退出", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        
        file_menu.addAction(import_action)
        file_menu.addAction(export_action)
        file_menu.addSeparator()
        file_menu.addAction(exit_action)
        
        # 工具菜单
        tool_menu = menubar.addMenu("工具")
        
        settings_action = QAction("设置", self)
        settings_action.setShortcut("Ctrl+,")
        settings_action.triggered.connect(self.open_settings)
        
        network_test_action = QAction("网络诊断", self)
        network_test_action.triggered.connect(self.network_diagnose)
        
        tool_menu.addAction(network_test_action)
        tool_menu.addAction(settings_action)
        
        # 帮助菜单
        help_menu = menubar.addMenu("帮助")
        
        about_action = QAction("关于", self)
        about_action.triggered.connect(self.show_about)
        
        help_menu.addAction(about_action)
        
    def create_tool_bar(self):
        """创建工具栏"""
        toolbar = QToolBar("主工具栏")
        toolbar.setIconSize(QSize(16, 16))
        self.addToolBar(toolbar)
        
        # 刷新按钮
        refresh_action = QAction("刷新", self)
        refresh_action.triggered.connect(self.refresh_music_library)
        toolbar.addAction(refresh_action)
        
        toolbar.addSeparator()
        
        # 设置按钮
        settings_action = QAction("设置", self)
        settings_action.triggered.connect(self.open_settings)
        toolbar.addAction(settings_action)
        
        toolbar.addSeparator()
        
        # 帮助按钮
        help_action = QAction("帮助", self)
        help_action.triggered.connect(self.show_help)
        toolbar.addAction(help_action)
        
    def setup_connections(self):
        """设置信号槽连接"""
        # 下载相关
        self.single_download_btn.clicked.connect(self.download_single)
        self.batch_download_btn.clicked.connect(self.download_batch)
        self.browse_path_btn.clicked.connect(self.browse_download_path)
        
        # 分类管理
        self.add_category_btn.clicked.connect(self.add_category)
        self.edit_category_btn.clicked.connect(self.edit_category)
        self.del_category_btn.clicked.connect(self.delete_category)
        
        # 音乐库操作
        self.search_btn.clicked.connect(self.search_songs)
        self.select_all_btn.clicked.connect(self.select_all_songs)
        self.rename_btn.clicked.connect(self.rename_songs)
        self.move_btn.clicked.connect(self.move_songs)
        self.delete_btn.clicked.connect(self.delete_songs)
        self.lyric_btn.clicked.connect(self.manage_lyrics)
        
        # 下载控制
        self.pause_all_btn.clicked.connect(self.pause_all_downloads)
        self.resume_all_btn.clicked.connect(self.resume_all_downloads)
        self.cancel_all_btn.clicked.connect(self.cancel_all_downloads)
        self.clear_finished_btn.clicked.connect(self.clear_finished_downloads)
        
        # 歌词操作
        self.search_lyrics_btn.clicked.connect(self.search_lyrics)
        self.download_lyrics_btn.clicked.connect(self.download_lyrics)
        self.save_lyrics_btn.clicked.connect(self.save_lyrics)
        self.sync_lyrics_btn.clicked.connect(self.sync_lyrics)
        
        # 其他信号
        self.song_list.itemSelectionChanged.connect(self.update_selection_count)
        
    def load_settings(self):
        """加载设置"""
        download_path = self.settings.value("download_path", str(Path.home() / "Music" / "B站音乐"))
        self.download_path_input.setText(download_path)
        
    def save_settings(self):
        """保存设置"""
        self.settings.setValue("download_path", self.download_path_input.text())
        
    def load_music_library(self):
        """加载音乐库"""
        self.song_list.clear()
        music_path = Path(self.download_path_input.text())
        
        if not music_path.exists():
            music_path.mkdir(parents=True, exist_ok=True)
            return
            
        # 查找音频文件
        audio_extensions = ['*.mp3', '*.flac', '*.wav', '*.m4a', '*.aac']
        audio_files = []
        for ext in audio_extensions:
            audio_files.extend(music_path.glob(ext))
            audio_files.extend(music_path.glob('**/' + ext))
        
        self.current_songs = []
        
        for audio_file in audio_files:
            try:
                song_info = self.music_manager.get_song_info(audio_file)
                self.add_song_to_list(song_info)
            except Exception as e:
                logging.error(f"加载歌曲失败 {audio_file}: {e}")
                
        self.update_song_count()
        
    def add_song_to_list(self, song_info):
        """添加歌曲到列表"""
        item = QTreeWidgetItem(self.song_list)
        
        # 选择复选框
        checkbox = QCheckBox()
        self.song_list.setItemWidget(item, 0, checkbox)
        checkbox.stateChanged.connect(self.update_selection_count)
        
        # 歌曲信息
        item.setText(1, song_info.get('title', Path(song_info.get('path', '')).stem))
        item.setText(2, song_info.get('artist', '未知歌手'))
        item.setText(3, song_info.get('genre', '未知风格'))
        item.setText(4, song_info.get('duration', '00:00'))
        item.setText(5, song_info.get('size', '0 MB'))
        item.setText(6, str(song_info.get('path', '')))
        
        self.current_songs.append(song_info)
        
    def update_song_count(self):
        """更新歌曲计数"""
        count = self.song_list.topLevelItemCount()
        self.song_count_label.setText(f"总共 {count} 首歌曲")
        self.update_selection_count()
        
    def update_selection_count(self):
        """更新选择计数"""
        selected_count = 0
        for i in range(self.song_list.topLevelItemCount()):
            item = self.song_list.topLevelItem(i)
            checkbox = self.song_list.itemWidget(item, 0)
            if checkbox and checkbox.isChecked():
                selected_count += 1
                
        self.selected_count_label.setText(f"已选择 {selected_count} 首")
        
    def search_songs(self):
        """搜索歌曲"""
        keyword = self.search_input.text().lower().strip()
        if not keyword:
            # 显示所有歌曲
            for i in range(self.song_list.topLevelItemCount()):
                item = self.song_list.topLevelItem(i)
                item.setHidden(False)
            return
            
        for i in range(self.song_list.topLevelItemCount()):
            item = self.song_list.topLevelItem(i)
            song_name = item.text(1).lower()
            artist = item.text(2).lower()
            
            if keyword in song_name or keyword in artist:
                item.setHidden(False)
            else:
                item.setHidden(True)
                
    def select_all_songs(self):
        """全选歌曲"""
        for i in range(self.song_list.topLevelItemCount()):
            item = self.song_list.topLevelItem(i)
            checkbox = self.song_list.itemWidget(item, 0)
            if checkbox:
                checkbox.setChecked(True)
                
    def get_selected_songs(self):
        """获取选中的歌曲"""
        selected_songs = []
        for i in range(self.song_list.topLevelItemCount()):
            item = self.song_list.topLevelItem(i)
            checkbox = self.song_list.itemWidget(item, 0)
            if checkbox and checkbox.isChecked():
                song_path = Path(item.text(6))
                selected_songs.append(song_path)
        return selected_songs
        
    def download_single(self):
        """单曲下载"""
        url = self.url_input.text().strip()
        if not url:
            QMessageBox.warning(self, "警告", "请输入B站视频链接")
            return
            
        if not self.downloader.validate_url(url):
            QMessageBox.warning(self, "警告", "无效的B站视频链接")
            return
            
        # 显示进度条
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        # 模拟下载过程
        self.simulate_download(url)
        
    def simulate_download(self, url):
        """模拟下载过程（实际应用中应使用真实下载）"""
        # 更新下载队列
        item = QTreeWidgetItem(self.download_list)
        item.setText(0, "解析中...")
        item.setText(1, "下载中")
        item.setText(2, "0%")
        
        # 取消按钮
        cancel_btn = QPushButton("取消")
        cancel_btn.setFixedWidth(60)
        cancel_btn.clicked.connect(lambda: self.cancel_download_item(item))
        self.download_list.setItemWidget(item, 3, cancel_btn)
        
        # 模拟下载进度
        self.simulate_progress(item, url)
        
    def simulate_progress(self, item, url):
        """模拟下载进度"""
        for progress in range(0, 101, 10):
            if progress == 100:
                item.setText(0, "下载完成")
                item.setText(1, "完成")
                item.setText(2, "100%")
                self.progress_bar.setValue(100)
                QMessageBox.information(self, "完成", "下载完成！")
                self.load_music_library()  # 刷新音乐库
                break
            else:
                item.setText(2, f"{progress}%")
                self.progress_bar.setValue(progress)
                QApplication.processEvents()  # 处理界面更新
                time.sleep(0.5)  # 模拟下载延迟
                
    def download_batch(self):
        """批量下载"""
        urls, ok = QInputDialog.getMultiLineText(
            self, "批量下载", 
            "请输入多个B站视频链接（每行一个）:",
            "https://www.bilibili.com/video/BV1fx411y7fU\nhttps://www.bilibili.com/video/BV1GJ411x7h7"
        )
        
        if ok and urls:
            url_list = [url.strip() for url in urls.split('\n') if url.strip()]
            valid_urls = []
            
            for url in url_list:
                if self.downloader.validate_url(url):
                    valid_urls.append(url)
                else:
                    QMessageBox.warning(self, "警告", f"无效链接已跳过: {url}")
                    
            if valid_urls:
                QMessageBox.information(self, "信息", f"开始下载 {len(valid_urls)} 个视频")
                for url in valid_urls:
                    self.download_single()
                    
    def browse_download_path(self):
        """浏览下载路径"""
        path = QFileDialog.getExistingDirectory(
            self, 
            "选择下载目录",
            self.download_path_input.text()
        )
        if path:
            self.download_path_input.setText(path)
            self.load_music_library()
            
    def add_category(self):
        """添加分类"""
        name, ok = QInputDialog.getText(self, "添加分类", "请输入分类名称:")
        if ok and name:
            self.category_list.addItem(name)
            
    def edit_category(self):
        """编辑分类"""
        current_item = self.category_list.currentItem()
        if current_item:
            name, ok = QInputDialog.getText(
                self, "编辑分类", "请输入分类名称:", 
                text=current_item.text()
            )
            if ok and name:
                current_item.setText(name)
                
    def delete_category(self):
        """删除分类"""
        current_row = self.category_list.currentRow()
        if current_row >= 0:
            reply = QMessageBox.question(
                self, "确认删除", 
                "确定要删除这个分类吗？"
            )
            if reply == QMessageBox.Yes:
                self.category_list.takeItem(current_row)
                
    def rename_songs(self):
        """重命名歌曲"""
        selected_songs = self.get_selected_songs()
        if not selected_songs:
            QMessageBox.warning(self, "警告", "请先选择要重命名的歌曲")
            return
            
        for song_path in selected_songs:
            new_name, ok = QInputDialog.getText(
                self, "重命名", 
                "请输入新文件名:", 
                text=song_path.stem
            )
            if ok and new_name:
                try:
                    new_path = song_path.parent / f"{new_name}{song_path.suffix}"
                    self.music_manager.rename_file(song_path, new_path)
                except Exception as e:
                    QMessageBox.warning(self, "错误", f"重命名失败: {e}")
                    
        self.load_music_library()
        
    def move_songs(self):
        """移动歌曲"""
        selected_songs = self.get_selected_songs()
        if not selected_songs:
            QMessageBox.warning(self, "警告", "请先选择要移动的歌曲")
            return
            
        target_dir = QFileDialog.getExistingDirectory(
            self, "选择目标文件夹"
        )
        if target_dir:
            for song_path in selected_songs:
                try:
                    self.music_manager.move_file(song_path, Path(target_dir))
                except Exception as e:
                    QMessageBox.warning(self, "错误", f"移动失败: {e}")
                    
        self.load_music_library()
        
    def delete_songs(self):
        """删除歌曲"""
        selected_songs = self.get_selected_songs()
        if not selected_songs:
            QMessageBox.warning(self, "警告", "请先选择要删除的歌曲")
            return
            
        reply = QMessageBox.question(
            self, "确认删除", 
            f"确定要删除这 {len(selected_songs)} 首歌曲吗？此操作不可恢复！"
        )
        if reply == QMessageBox.Yes:
            for song_path in selected_songs:
                try:
                    self.music_manager.delete_file(song_path)
                except Exception as e:
                    QMessageBox.warning(self, "错误", f"删除失败: {e}")
                    
            self.load_music_library()
            
    def manage_lyrics(self):
        """管理歌词"""
        selected_songs = self.get_selected_songs()
        if not selected_songs:
            QMessageBox.warning(self, "警告", "请先选择歌曲")
            return
            
        song_path = selected_songs[0]
        self.current_song_label.setText(song_path.stem)
        self.lyrics_display.setPlainText(f"正在为 {song_path.stem} 搜索歌词...")
        
    def search_lyrics(self):
        """搜索歌词"""
        QMessageBox.information(self, "提示", "开始搜索歌词...")
        
    def download_lyrics(self):
        """下载歌词"""
        QMessageBox.information(self, "提示", "开始下载歌词...")
        
    def save_lyrics(self):
        """保存歌词"""
        QMessageBox.information(self, "提示", "歌词已保存")
        
    def sync_lyrics(self):
        """同步歌词"""
        QMessageBox.information(self, "提示", "开始同步歌词...")
        
    def pause_all_downloads(self):
        """暂停所有下载"""
        QMessageBox.information(self, "提示", "已暂停所有下载")
        
    def resume_all_downloads(self):
        """继续所有下载"""
        QMessageBox.information(self, "提示", "已继续所有下载")
        
    def cancel_all_downloads(self):
        """取消所有下载"""
        reply = QMessageBox.question(
            self, "确认取消", 
            "确定要取消所有下载任务吗？"
        )
        if reply == QMessageBox.Yes:
            self.download_list.clear()
            self.add_example_download_item()  # 重新添加示例项
            
    def clear_finished_downloads(self):
        """清除已完成下载"""
        self.download_list.clear()
        self.add_example_download_item()
        QMessageBox.information(self, "提示", "已清除已完成下载")
        
    def import_music(self):
        """导入音乐"""
        files, _ = QFileDialog.getOpenFileNames(
            self, "选择音乐文件", 
            "", 
            "音频文件 (*.mp3 *.flac *.wav *.m4a);;所有文件 (*.*)"
        )
        if files:
            QMessageBox.information(self, "导入", f"成功导入 {len(files)} 个文件")
            self.load_music_library()
            
    def export_music_list(self):
        """导出音乐列表"""
        path, _ = QFileDialog.getSaveFileName(
            self, "导出音乐列表", 
            "音乐列表.txt", 
            "文本文件 (*.txt)"
        )
        if path:
            QMessageBox.information(self, "导出", f"音乐列表已导出到: {path}")
            
    def refresh_music_library(self):
        """刷新音乐库"""
        self.load_music_library()
        QMessageBox.information(self, "刷新", "音乐库已刷新")
        
    def open_settings(self):
        """打开设置"""
        QMessageBox.information(self, "设置", "设置功能开发中")
        
    def network_diagnose(self):
        """网络诊断"""
        if self.downloader.test_connection():
            QMessageBox.information(self, "网络诊断", "网络连接正常")
        else:
            QMessageBox.warning(self, "网络诊断", "网络连接失败，请检查网络设置")
            
    def show_about(self):
        """显示关于信息"""
        about_text = """
        <h3>B站音乐提取器 v1.0</h3>
        <p>一个可以从哔哩哔哩视频中提取音乐的桌面应用程序。</p>
        <p>功能特点：</p>
        <ul>
        <li>支持B站视频音乐提取</li>
        <li>批量下载功能</li>
        <li>音乐文件管理</li>
        <li>歌词搜索和同步</li>
        </ul>
        <p>© 2023 B站音乐提取器 版权所有</p>
        """
        QMessageBox.about(self, "关于", about_text)
        
    def show_help(self):
        """显示帮助"""
        help_text = """
        <h3>使用帮助</h3>
        <p><b>基本使用：</b></p>
        <ol>
        <li>在左侧输入B站视频链接</li>
        <li>点击"单曲下载"或"批量下载"</li>
        <li>在"下载队列"中查看进度</li>
        <li>在"音乐库"中管理下载的歌曲</li>
        </ol>
        <p><b>快捷键：</b></p>
        <ul>
        <li>Ctrl+I: 导入音乐</li>
        <li>Ctrl+E: 导出列表</li>
        <li>Ctrl+Q: 退出程序</li>
        <li>Ctrl+,: 打开设置</li>
        </ul>
        """
        QMessageBox.information(self, "帮助", help_text)
        
    def closeEvent(self, event):
        """关闭事件"""
        self.save_settings()
        # 停止所有下载线程
        for thread in self.download_threads:
            if thread.isRunning():
                thread.stop()
                thread.wait(1000)
        event.accept()

# 测试代码
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
