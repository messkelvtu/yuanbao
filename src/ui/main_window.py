import os
import re
import json
from pathlib import Path
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLineEdit, QLabel, QMessageBox,
                             QTabWidget, QTreeWidget, QTreeWidgetItem, QHeaderView,
                             QSplitter, QToolBar, QAction, QMenuBar, QMenu,
                             QInputDialog, QFileDialog, QProgressBar, QCheckBox,
                             QListWidget, QListWidgetItem, QGroupBox)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QSettings
from PyQt5.QtGui import QIcon

from core.downloader import BilibiliDownloader, DownloadThread
from core.music_manager import MusicManager
from core.lyric_matcher import LyricMatcher
from ui.lyrics_window import LyricsWindow

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.settings = QSettings("B站音乐提取器", "B站音乐提取器")
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
        self.setWindowTitle("B站音乐提取器")
        self.setGeometry(100, 100, 1200, 800)
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QHBoxLayout(central_widget)
        
        # 左侧功能面板
        left_panel = self.create_left_panel()
        main_layout.addWidget(left_panel, 1)
        
        # 右侧主内容区域
        right_panel = self.create_right_panel()
        main_layout.addWidget(right_panel, 3)
        
        # 创建菜单栏
        self.create_menu_bar()
        
        # 创建工具栏
        self.create_tool_bar()
        
    def create_left_panel(self):
        """创建左侧功能面板"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # 下载功能区域
        download_group = QGroupBox("下载设置")
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
        
        # 下载路径设置
        path_layout = QHBoxLayout()
        self.download_path_input = QLineEdit()
        self.download_path_input.setText(str(Path.home() / "Music" / "B站音乐"))
        self.browse_path_btn = QPushButton("浏览")
        path_layout.addWidget(QLabel("下载路径:"))
        path_layout.addWidget(self.download_path_input)
        path_layout.addWidget(self.browse_path_btn)
        download_layout.addLayout(path_layout)
        
        # 下载进度
        self.progress_bar = QProgressBar()
        download_layout.addWidget(self.progress_bar)
        
        layout.addWidget(download_group)
        
        # 分类管理
        category_group = QGroupBox("分类管理")
        category_layout = QVBoxLayout(category_group)
        
        self.category_list = QListWidget()
        category_layout.addWidget(self.category_list)
        
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
        self.search_input.textChanged.connect(self.search_songs)
        toolbar.addWidget(QLabel("搜索:"))
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
        self.song_list.setHeaderLabels(["选择", "歌曲名", "歌手", "风格", "时长", "大小", "路径"])
        self.song_list.header().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.song_list.setSelectionMode(QTreeWidget.ExtendedSelection)
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
        self.download_list.header().setSectionResizeMode(QHeaderView.ResizeToContents)
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
        
    def create_menu_bar(self):
        """创建菜单栏"""
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu("文件")
        
        import_action = QAction("导入音乐", self)
        import_action.triggered.connect(self.import_music)
        export_action = QAction("导出列表", self)
        export_action.triggered.connect(self.export_music_list)
        exit_action = QAction("退出", self)
        exit_action.triggered.connect(self.close)
        
        file_menu.addAction(import_action)
        file_menu.addAction(export_action)
        file_menu.addSeparator()
        file_menu.addAction(exit_action)
        
        # 工具菜单
        tool_menu = menubar.addMenu("工具")
        settings_action = QAction("设置", self)
        settings_action.triggered.connect(self.open_settings)
        tool_menu.addAction(settings_action)
        
    def create_tool_bar(self):
        """创建工具栏"""
        toolbar = self.addToolBar("主工具栏")
        
        # 添加工具按钮
        refresh_act = QAction("刷新", self)
        refresh_act.triggered.connect(self.refresh_music_library)
        settings_act = QAction("设置", self)
        settings_act.triggered.connect(self.open_settings)
        help_act = QAction("帮助", self)
        help_act.triggered.connect(self.show_help)
        
        toolbar.addAction(refresh_act)
        toolbar.addAction(settings_act)
        toolbar.addAction(help_act)
        
    def setup_connections(self):
        """设置信号槽连接"""
        self.single_download_btn.clicked.connect(self.download_single)
        self.batch_download_btn.clicked.connect(self.download_batch)
        self.browse_path_btn.clicked.connect(self.browse_download_path)
        self.add_category_btn.clicked.connect(self.add_category)
        self.edit_category_btn.clicked.connect(self.edit_category)
        self.del_category_btn.clicked.connect(self.delete_category)
        self.lyric_btn.clicked.connect(self.open_lyric_manager)
        self.select_all_btn.clicked.connect(self.select_all_songs)
        self.rename_btn.clicked.connect(self.rename_songs)
        self.move_btn.clicked.connect(self.move_songs)
        self.delete_btn.clicked.connect(self.delete_songs)
        
        self.pause_all_btn.clicked.connect(self.pause_all_downloads)
        self.resume_all_btn.clicked.connect(self.resume_all_downloads)
        self.cancel_all_btn.clicked.connect(self.cancel_all_downloads)
        self.clear_finished_btn.clicked.connect(self.clear_finished_downloads)
        
    def load_settings(self):
        """加载设置"""
        download_path = self.settings.value("download_path", str(Path.home() / "Music" / "B站音乐"))
        self.download_path_input.setText(download_path)
        
        # 加载分类
        categories = self.settings.value("categories", ["流行", "摇滚", "电子", "古典", "爵士"])
        for category in categories:
            self.category_list.addItem(category)
        
    def save_settings(self):
        """保存设置"""
        self.settings.setValue("download_path", self.download_path_input.text())
        categories = []
        for i in range(self.category_list.count()):
            categories.append(self.category_list.item(i).text())
        self.settings.setValue("categories", categories)
        
    def load_music_library(self):
        """加载音乐库"""
        self.song_list.clear()
        music_library_path = Path(self.download_path_input.text())
        
        if not music_library_path.exists():
            return
            
        audio_files = list(music_library_path.glob("*.mp3")) + list(music_library_path.glob("*.flac")) + \
                     list(music_library_path.glob("*.wav")) + list(music_library_path.glob("*.m4a"))
        
        self.current_songs = []
        
        for audio_file in audio_files:
            song_info = self.music_manager.get_song_info(audio_file)
            self.add_song_to_list(song_info)
            
        self.update_status_label()
        
    def add_song_to_list(self, song_info):
        """添加歌曲到列表"""
        item = QTreeWidgetItem(self.song_list)
        
        # 选择复选框
        checkbox = QCheckBox()
        self.song_list.setItemWidget(item, 0, checkbox)
        
        # 歌曲信息
        item.setText(1, song_info.get('title', '未知歌曲'))
        item.setText(2, song_info.get('artist', '未知歌手'))
        item.setText(3, song_info.get('genre', '未知风格'))
        item.setText(4, song_info.get('duration', '00:00'))
        item.setText(5, song_info.get('size', '0 MB'))
        item.setText(6, str(song_info.get('path', '')))
        
        self.current_songs.append(song_info)
        
    def update_status_label(self):
        """更新状态标签"""
        count = self.song_list.topLevelItemCount()
        self.status_label.setText(f"总共 {count} 首歌曲")
        
    def search_songs(self):
        """搜索歌曲"""
        keyword = self.search_input.text().lower()
        
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
            QMessageBox.warning(self, "警告", "请输入有效的B站视频链接")
            return
            
        download_path = Path(self.download_path_input.text())
        download_path.mkdir(parents=True, exist_ok=True)
        
        # 创建下载线程
        thread = DownloadThread(url, str(download_path), self.downloader)
        thread.progress.connect(self.update_download_progress)
        thread.finished.connect(self.download_finished)
        thread.error.connect(self.download_error)
        
        # 添加到下载列表
        self.add_download_to_list(url, thread)
        
        # 启动下载
        thread.start()
        self.download_threads.append(thread)
        
    def download_batch(self):
        """批量下载"""
        urls, ok = QInputDialog.getMultiLineText(self, "批量下载", 
                                                "请输入多个B站视频链接(每行一个):")
        if ok and urls:
            url_list = [url.strip() for url in urls.split('\n') if url.strip()]
            
            download_path = Path(self.download_path_input.text())
            download_path.mkdir(parents=True, exist_ok=True)
            
            for url in url_list:
                thread = DownloadThread(url, str(download_path), self.downloader)
                thread.progress.connect(self.update_download_progress)
                thread.finished.connect(self.download_finished)
                thread.error.connect(self.download_error)
                
                self.add_download_to_list(url, thread)
                thread.start()
                self.download_threads.append(thread)
                
    def add_download_to_list(self, url, thread):
        """添加下载任务到列表"""
        item = QTreeWidgetItem(self.download_list)
        item.setText(0, "解析中...")
        item.setText(1, "等待中")
        item.setText(2, "0%")
        
        # 取消按钮
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(lambda: self.cancel_download(thread))
        self.download_list.setItemWidget(item, 3, cancel_btn)
        
        # 保存线程和项目的关联
        thread.item = item
        thread.url = url
        
    def update_download_progress(self, url, progress):
        """更新下载进度"""
        for i in range(self.download_list.topLevelItemCount()):
            item = self.download_list.topLevelItem(i)
            if hasattr(item, 'thread') and item.thread.url == url:
                item.setText(2, f"{progress}%")
                if progress == 100:
                    item.setText(1, "完成")
                    
    def download_finished(self, url, file_path):
        """下载完成"""
        # 刷新音乐库
        self.load_music_library()
        
    def download_error(self, url, error_msg):
        """下载错误"""
        for i in range(self.download_list.topLevelItemCount()):
            item = self.download_list.topLevelItem(i)
            if hasattr(item, 'thread') and item.thread.url == url:
                item.setText(1, f"错误: {error_msg}")
                
    def cancel_download(self, thread):
        """取消下载"""
        if thread.isRunning():
            thread.stop()
            
    def pause_all_downloads(self):
        """暂停所有下载"""
        for thread in self.download_threads:
            if thread.isRunning():
                thread.pause()
                
    def resume_all_downloads(self):
        """继续所有下载"""
        for thread in self.download_threads:
            if thread.isPaused():
                thread.resume()
                
    def cancel_all_downloads(self):
        """取消所有下载"""
        for thread in self.download_threads:
            if thread.isRunning():
                thread.stop()
                
    def clear_finished_downloads(self):
        """清除已完成下载"""
        for i in range(self.download_list.topLevelItemCount() - 1, -1, -1):
            item = self.download_list.topLevelItem(i)
            if item.text(1) in ["完成", "错误"]:
                self.download_list.takeTopLevelItem(i)
                
    def browse_download_path(self):
        """浏览下载路径"""
        path = QFileDialog.getExistingDirectory(self, "选择下载路径", self.download_path_input.text())
        if path:
            self.download_path_input.setText(path)
            self.load_music_library()
            
    def add_category(self):
        """添加分类"""
        name, ok = QInputDialog.getText(self, "添加分类", "请输入分类名称:")
        if ok and name:
            self.category_list.addItem(name)
            self.save_settings()
            
    def edit_category(self):
        """编辑分类"""
        current_item = self.category_list.currentItem()
        if current_item:
            name, ok = QInputDialog.getText(self, "编辑分类", "请输入分类名称:", text=current_item.text())
            if ok and name:
                current_item.setText(name)
                self.save_settings()
                
    def delete_category(self):
        """删除分类"""
        current_row = self.category_list.currentRow()
        if current_row >= 0:
            reply = QMessageBox.question(self, "确认删除", "确定要删除这个分类吗?")
            if reply == QMessageBox.Yes:
                self.category_list.takeItem(current_row)
                self.save_settings()
                
    def rename_songs(self):
        """重命名歌曲"""
        selected_songs = self.get_selected_songs()
        if not selected_songs:
            QMessageBox.warning(self, "警告", "请先选择要重命名的歌曲")
            return
            
        for song_path in selected_songs:
            new_name, ok = QInputDialog.getText(self, "重命名", "请输入新文件名:", text=song_path.stem)
            if ok and new_name:
                self.music_manager.rename_file(song_path, new_name + song_path.suffix)
                
        self.load_music_library()
        
    def move_songs(self):
        """移动歌曲"""
        selected_songs = self.get_selected_songs()
        if not selected_songs:
            QMessageBox.warning(self, "警告", "请先选择要移动的歌曲")
            return
            
        path = QFileDialog.getExistingDirectory(self, "选择目标文件夹")
        if path:
            for song_path in selected_songs:
                self.music_manager.move_file(song_path, Path(path))
                
        self.load_music_library()
        
    def delete_songs(self):
        """删除歌曲"""
        selected_songs = self.get_selected_songs()
        if not selected_songs:
            QMessageBox.warning(self, "警告", "请先选择要删除的歌曲")
            return
            
        reply = QMessageBox.question(self, "确认删除", f"确定要删除这 {len(selected_songs)} 首歌曲吗?")
        if reply == QMessageBox.Yes:
            for song_path in selected_songs:
                self.music_manager.delete_file(song_path)
                
        self.load_music_library()
        
    def open_lyric_manager(self):
        """打开歌词管理器"""
        selected_songs = self.get_selected_songs()
        if not selected_songs:
            QMessageBox.warning(self, "警告", "请先选择歌曲")
            return
            
        self.lyrics_window = LyricsWindow(selected_songs[0], self.lyric_matcher)
        self.lyrics_window.show()
        
    def import_music(self):
        """导入音乐"""
        files, _ = QFileDialog.getOpenFileNames(
            self, "选择音乐文件", "", 
            "音频文件 (*.mp3 *.flac *.wav *.m4a);;所有文件 (*.*)"
        )
        
        if files:
            download_path = Path(self.download_path_input.text())
            download_path.mkdir(parents=True, exist_ok=True)
            
            for file in files:
                file_path = Path(file)
                target_path = download_path / file_path.name
                
                # 复制文件到下载目录
                import shutil
                shutil.copy2(file_path, target_path)
                
            self.load_music_library()
            
    def export_music_list(self):
        """导出音乐列表"""
        path, _ = QFileDialog.getSaveFileName(
            self, "导出音乐列表", "音乐列表.txt", "文本文件 (*.txt)"
        )
        
        if path:
            with open(path, 'w', encoding='utf-8') as f:
                f.write("音乐列表\n")
                f.write("=" * 50 + "\n")
                
                for i in range(self.song_list.topLevelItemCount()):
                    item = self.song_list.topLevelItem(i)
                    f.write(f"{i+1}. {item.text(1)} - {item.text(2)} ({item.text(4)})\n")
                    
            QMessageBox.information(self, "导出成功", f"音乐列表已导出到: {path}")
            
    def open_settings(self):
        """打开设置对话框"""
        QMessageBox.information(self, "设置", "设置功能开发中")
        
    def refresh_music_library(self):
        """刷新音乐库"""
        self.load_music_library()
        QMessageBox.information(self, "刷新完成", "音乐库已刷新")
        
    def show_help(self):
        """显示帮助"""
        QMessageBox.information(self, "帮助", 
            "B站音乐提取器使用说明:\n\n"
            "1. 在左侧输入B站视频链接，点击下载\n"
            "2. 下载完成后可在音乐库中管理歌曲\n"
            "3. 支持批量重命名、移动、删除操作\n"
            "4. 可以自动匹配和搜索歌词"
        )
        
    def closeEvent(self, event):
        """关闭事件"""
        self.save_settings()
        
        # 停止所有下载线程
        for thread in self.download_threads:
            if thread.isRunning():
                thread.stop()
                thread.wait(1000)  # 等待1秒
                
        event.accept()
