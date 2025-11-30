import sys
import os
from pathlib import Path

# 添加src目录到Python路径
src_path = Path(__file__).parent
sys.path.insert(0, str(src_path))

def main():
    """主函数"""
    try:
        from PyQt5.QtWidgets import QApplication, QMessageBox
        from ui.main_window import MainWindow
        
        # 创建应用
        app = QApplication(sys.argv)
        app.setApplicationName("B站音乐提取器")
        app.setApplicationVersion("1.0.0")
        
        # 创建主窗口
        window = MainWindow()
        window.show()
        
        # 运行应用
        return app.exec_()
        
    except Exception as e:
        # 显示错误对话框
        error_app = QApplication(sys.argv)
        QMessageBox.critical(
            None, 
            "启动错误", 
            f"应用启动时发生错误:\n{str(e)}\n\n请检查安装是否完整。"
        )
        return 1

if __name__ == "__main__":
    sys.exit(main())
