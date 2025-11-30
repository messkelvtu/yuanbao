#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
B站音乐提取器构建脚本
自动打包为Windows可执行文件
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

# 设置标准输出编码为UTF-8
if sys.stdout.encoding != 'utf-8':
    if sys.version_info >= (3, 7):
        sys.stdout.reconfigure(encoding='utf-8')
    else:
        # Python 3.6及以下版本的兼容处理
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer)

def safe_print(message):
    """安全打印函数，处理编码问题"""
    try:
        print(message)
    except UnicodeEncodeError:
        # 如果遇到编码错误，使用ASCII替代
        safe_message = message.encode('ascii', 'replace').decode('ascii')
        print(safe_message)

def read_version():
    """读取版本号"""
    try:
        with open('version.txt', 'r', encoding='utf-8') as f:
            return f.read().strip()
    except FileNotFoundError:
        return "1.0.0"

def clean_build_dirs():
    """清理构建目录"""
    dirs_to_clean = ['build', 'dist']
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            safe_print(f"Cleaned directory: {dir_name}")

def check_project_structure():
    """检查项目结构是否完整"""
    required_dirs = [
        'src',
        'src/ui',
        'src/core',
        'src/utils'
    ]
    
    required_files = [
        'src/main.py',
        'src/ui/__init__.py',
        'src/ui/main_window.py',
        'src/ui/lyrics_window.py',
        'src/core/__init__.py',
        'src/core/downloader.py',
        'src/core/lyric_matcher.py',
        'src/core/music_manager.py',
        'src/utils/__init__.py',
        'src/utils/helpers.py'
    ]
    
    safe_print("Checking project structure...")
    
    # 检查目录
    for dir_path in required_dirs:
        if not os.path.exists(dir_path):
            safe_print(f"Creating missing directory: {dir_path}")
            os.makedirs(dir_path, exist_ok=True)
    
    # 检查文件并创建必要的空文件
    for file_path in required_files:
        if not os.path.exists(file_path):
            safe_print(f"Creating placeholder file: {file_path}")
            with open(file_path, 'w', encoding='utf-8') as f:
                if file_path.endswith('__init__.py'):
                    # 空文件即可
                    pass
                elif file_path.endswith('helpers.py'):
                    f.write('''"""
工具函数模块
"""

def sanitize_filename(filename):
    """清理文件名中的非法字符"""
    import re
    return re.sub(r'[<>:"/\\\\|?*]', '', filename)

def format_duration(seconds):
    """格式化时长（秒 -> MM:SS）"""
    minutes = seconds // 60
    seconds = seconds % 60
    return f"{minutes:02d}:{seconds:02d}"

def format_file_size(size_bytes):
    """格式化文件大小"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes/1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes/(1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes/(1024 * 1024 * 1024):.1f} GB"

def ensure_directory_exists(path):
    """确保目录存在"""
    Path(path).mkdir(parents=True, exist_ok=True)
    return Path(path)

def is_audio_file(file_path):
    """检查是否是音频文件"""
    audio_extensions = {'.mp3', '.flac', '.wav', '.m4a', '.aac', '.ogg'}
    return Path(file_path).suffix.lower() in audio_extensions

def get_unique_filename(file_path):
    """获取唯一的文件名，避免覆盖"""
    path = Path(file_path)
    if not path.exists():
        return path
        
    counter = 1
    while True:
        new_path = path.parent / f"{path.stem}_{counter}{path.suffix}"
        if not new_path.exists():
            return new_path
        counter += 1
''')
                else:
                    # 创建基本的Python文件结构
                    module_name = os.path.basename(file_path).replace('.py', '')
                    f.write(f'"""\n{module_name} 模块\n"""\n\n# TODO: 实现功能\n')
    
    safe_print("Project structure check completed")

def run_pyinstaller():
    """使用PyInstaller打包"""
    
    # 检查项目结构
    check_project_structure()
    
    # PyInstaller配置 - 使用英文参数避免编码问题
    pyinstaller_cmd = [
        'pyinstaller',
        '--name=BilibiliMusicExtractor',  # 使用英文名称
        '--windowed',  # 不显示控制台窗口
        '--onefile',   # 打包为单个exe
        '--add-data=src/ui;ui',
        '--add-data=src/core;core', 
        '--add-data=src/utils;utils',
        '--hidden-import=PyQt5.QtCore',
        '--hidden-import=PyQt5.QtGui',
        '--hidden-import=PyQt5.QtWidgets',
        '--hidden-import=requests',
        '--hidden-import=beautifulsoup4',
        '--hidden-import=lxml',
        '--hidden-import=mutagen',
        '--hidden-import=yt_dlp',
        '--clean',  # 清理临时文件
        'src/main.py'
    ]
    
    safe_print("Starting build process...")
    safe_print(f"Command: {' '.join(pyinstaller_cmd)}")
    
    try:
        # 使用UTF-8编码运行子进程
        result = subprocess.run(
            pyinstaller_cmd, 
            capture_output=True, 
            text=True, 
            encoding='utf-8',
            check=True
        )
        
        safe_print("✓ Build successful!")
        
        # 检查生成的可执行文件
        exe_path = Path('dist') / 'BilibiliMusicExtractor.exe'
        if exe_path.exists():
            file_size = exe_path.stat().st_size / (1024 * 1024)  # MB
            safe_print(f"✓ Generated file: {exe_path} ({file_size:.2f} MB)")
            return True
        else:
            safe_print("✗ Executable file not found")
            return False
            
    except subprocess.CalledProcessError as e:
        safe_print("✗ Build failed!")
        safe_print("STDOUT: " + e.stdout)
        safe_print("STDERR: " + e.stderr)
        return False
    except Exception as e:
        safe_print(f"✗ Error during build: {e}")
        return False

def main():
    """主构建流程"""
    safe_print("=" * 50)
    safe_print("Bilibili Music Extractor - Build Tool")
    safe_print("=" * 50)
    
    version = read_version()
    safe_print(f"Version: {version}")
    
    # 检查当前目录
    if not os.path.exists('src/main.py'):
        safe_print("Error: Please run this script from the project root directory")
        safe_print("Current directory contents: " + str(os.listdir('.')))
        return 1
    
    # 清理构建目录
    safe_print("\n1. Cleaning build directories...")
    clean_build_dirs()
    
    # 打包为exe
    safe_print("\n2. Building with PyInstaller...")
    if not run_pyinstaller():
        return 1
    
    safe_print("\n" + "=" * 50)
    safe_print("✓ Build completed successfully!")
    safe_print("Executable location: dist/BilibiliMusicExtractor.exe")
    safe_print("=" * 50)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
