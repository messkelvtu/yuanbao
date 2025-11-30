import sys
import os
import logging
from pathlib import Path

# 添加src目录到Python路径
src_path = Path(__file__).parent
sys.path.insert(0, str(src_path))

def setup_logging():
    """设置日志配置"""
    log_dir = Path.home() / '.bilibili_music_extractor' / 'logs'
    log_dir.mkdir(parents=True, exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / 'app.log', encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )

def main():
    """主函数"""
    # 设置日志
    setup_logging()
    
    try:
        from PyQt5.QtWidgets import QApplication
        from ui.main_window import MainWindow
        
        # 创建应用
        app = QApplication(sys.argv)
        app.setApplicationName("B站音乐提取器")
        app.setApplicationVersion("1.0.0")
        app.setOrganizationName("B站音乐提取器")
        
        # 创建主窗口
        window = MainWindow()
        window.show()
        
        # 运行应用
        return app.exec_()
        
    except Exception as e:
        logging.error(f"应用启动失败: {e}")
        
        # 显示错误对话框
        from PyQt5.QtWidgets import QMessageBox, QApplication
        import sys
        
        error_app = QApplication(sys.argv)
        QMessageBox.critical(
            None, 
            "启动错误", 
            f"应用启动时发生错误:\n{str(e)}\n\n请检查安装是否完整。"
        )
        return 1

if __name__ == "__main__":
    sys.exit(main())
