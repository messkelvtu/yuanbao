"""
工具函数模块
"""

import os
import re
from pathlib import Path

def sanitize_filename(filename):
    """清理文件名中的非法字符"""
    # 移除Windows文件名中的非法字符
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)
    # 移除首尾空格和点
    filename = filename.strip().strip('.')
    # 限制文件名长度
    if len(filename) > 100:
        filename = filename[:100]
    return filename

def format_duration(seconds):
    """格式化时长（秒 -> MM:SS）"""
    if not seconds:
        return "00:00"
        
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
