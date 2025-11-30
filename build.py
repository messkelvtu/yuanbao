#!/usr/bin/env python3
"""
B站音乐提取器构建脚本
自动打包为Windows可执行文件
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

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
            print(f"已清理目录: {dir_name}")

def create_icon_if_missing():
    """如果图标文件不存在，创建一个简单的图标（可选）"""
    icon_path = Path('assets/icon.ico')
    if not icon_path.exists():
        # 创建assets目录
        icon_path.parent.mkdir(exist_ok=True)
        print("⚠️ 图标文件不存在，将使用默认图标")

def run_pyinstaller():
    """使用PyInstaller打包"""
    
    # 确保图标目录存在
    create_icon_if_missing()
    
    # PyInstaller配置
    pyinstaller_cmd = [
        'pyinstaller',
        '--name=B站音乐提取器',
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
    
    print("开始打包...")
    print(f"执行命令: {' '.join(pyinstaller_cmd)}")
    
    try:
        result = subprocess.run(pyinstaller_cmd, capture_output=True, text=True, check=True)
        
        print("✓ 打包成功!")
        
        # 检查生成的可执行文件
        exe_path = Path('dist') / 'B站音乐提取器.exe'
        if exe_path.exists():
            file_size = exe_path.stat().st_size / (1024 * 1024)  # MB
            print(f"✓ 生成文件: {exe_path} ({file_size:.2f} MB)")
            return True
        else:
            print("✗ 未找到生成的可执行文件")
            return False
            
    except subprocess.CalledProcessError as e:
        print("✗ 打包失败!")
        print("STDOUT:", e.stdout)
        print("STDERR:", e.stderr)
        return False
    except Exception as e:
        print(f"✗ 打包过程中发生错误: {e}")
        return False

def main():
    """主构建流程"""
    print("=" * 50)
    print("B站音乐提取器 - 构建工具")
    print("=" * 50)
    
    version = read_version()
    print(f"版本: {version}")
    
    # 检查当前目录
    if not os.path.exists('src/main.py'):
        print("错误: 请在项目根目录运行此脚本")
        print("当前目录内容:", os.listdir('.'))
        return 1
    
    # 清理构建目录
    print("\n1. 清理构建目录...")
    clean_build_dirs()
    
    # 打包为exe
    print("\n2. 使用PyInstaller打包...")
    if not run_pyinstaller():
        return 1
    
    print("\n" + "=" * 50)
    print("✓ 构建完成!")
    print(f"可执行文件位置: dist/B站音乐提取器.exe")
    print("=" * 50)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
