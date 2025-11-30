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
    with open('version.txt', 'r', encoding='utf-8') as f:
        return f.read().strip()

def clean_build_dirs():
    """清理构建目录"""
    dirs_to_clean = ['build', 'dist']
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"已清理目录: {dir_name}")

def run_pyinstaller():
    """使用PyInstaller打包"""
    
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
        '--clean',  # 清理临时文件
        'src/main.py'
    ]
    
    # 过滤空参数
    pyinstaller_cmd = [arg for arg in pyinstaller_cmd if arg]
    
    print("开始打包...")
    print(f"执行命令: {' '.join(pyinstaller_cmd)}")
    
    result = subprocess.run(pyinstaller_cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✓ 打包成功!")
        
        # 检查生成的可执行文件
        exe_path = Path('dist') / 'B站音乐提取器.exe'
        if exe_path.exists():
            file_size = exe_path.stat().st_size / (1024 * 1024)  # MB
            print(f"✓ 生成文件: {exe_path} ({file_size:.2f} MB)")
        else:
            print("✗ 未找到生成的可执行文件")
            return False
            
    else:
        print("✗ 打包失败!")
        print("STDOUT:", result.stdout)
        print("STDERR:", result.stderr)
        return False
        
    return True

def create_installer():
    """创建安装包（可选）"""
    # 这里可以使用Inno Setup或NSIS创建安装包
    # 由于云编译环境限制，这里暂不实现
    print("跳过安装包创建（需要额外配置）")
    return True

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
        return 1
    
    # 清理构建目录
    print("\n1. 清理构建目录...")
    clean_build_dirs()
    
    # 打包为exe
    print("\n2. 使用PyInstaller打包...")
    if not run_pyinstaller():
        return 1
    
    # 创建安装包（可选）
    print("\n3. 创建安装包...")
    create_installer()
    
    print("\n" + "=" * 50)
    print("✓ 构建完成!")
    print(f"可执行文件位置: dist/B站音乐提取器.exe")
    print("=" * 50)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
