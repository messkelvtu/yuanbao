from setuptools import setup, find_packages
import os

# 读取版本号
with open('version.txt', 'r', encoding='utf-8') as f:
    version = f.read().strip()

# 读取依赖
with open('requirements.txt', 'r', encoding='utf-8') as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]

setup(
    name="bilibili_music_extractor",
    version=version,
    description="B站音乐提取器 - 从哔哩哔哩视频提取音乐并管理",
    author="Your Name",
    author_email="your.email@example.com",
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    install_requires=requirements,
    python_requires='>=3.8',
    entry_points={
        'console_scripts': [
            'bilibili-music-extractor=main:main',
        ],
    },
    include_package_data=True,
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: MIT License',
        'Operating System :: Microsoft :: Windows',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
    ],
)
