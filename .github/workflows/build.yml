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

def create_icon_if_missing():
    """如果图标文件不存在，创建一个简单的图标（可选）"""
    icon_path = Path('assets/icon.ico')
    if not icon_path.exists():
        # 创建assets目录
        icon_path.parent.mkdir(exist_ok=True)
        safe_print("Warning: Icon file not found, using default icon")

def run_pyinstaller():
    """使用PyInstaller打包"""
    
    # 确保图标目录存在
    create_icon_if_missing()
    
    # PyInstaller配置 - 使用英文参数避免编码问题
    pyinstaller_cmd = [
        'pyinstaller',
        '--name=BilibiliMusicExtractor',  # 使用英文名称
        '--windowed',  # 不显示控制台窗口
        '--onefile',   # 打包为单个exe
        '--icon=assets/icon.ico' if os.path.exists('assets/icon.ico') else '',
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
        '--clean',  # 清理临时文件
        'src/main.py'
    ]
    
    # 过滤空参数
    pyinstaller_cmd = [arg for arg in pyinstaller_cmd if arg]
    
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

def rename_executable():
    """构建完成后重命名可执行文件为中文（如果系统支持）"""
    original_path = Path('dist') / 'BilibiliMusicExtractor.exe'
    target_path = Path('dist') / 'B站音乐提取器.exe'
    
    if original_path.exists():
        try:
            # 尝试重命名为中文
            original_path.rename(target_path)
            safe_print(f"Renamed to: {target_path}")
        except (OSError, UnicodeEncodeError):
            # 如果重命名失败，保持英文名称
            safe_print("Cannot rename to Chinese, keeping English name")
            return str(original_path)
    
    return str(target_path) if target_path.exists() else str(original_path)

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
    
    # 尝试重命名可执行文件
    safe_print("\n3. Finalizing executable...")
    final_exe_path = rename_executable()
    
    safe_print("\n" + "=" * 50)
    safe_print("✓ Build completed successfully!")
    safe_print(f"Executable location: {final_exe_path}")
    safe_print("=" * 50)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
