import sys
import os
import logging
from pathlib import Path

# 设置标准输出编码为UTF-8
try:
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    elif sys.version_info < (3, 7):
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer)
except:
    pass

def setup_logging():
    """设置日志配置"""
    try:
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
    except Exception as e:
        print(f"日志设置失败: {e}")

def main():
    """主函数"""
    # 确保sys在函数内可用
    global sys
    if 'sys' not in globals():
        import sys
    
    # 设置日志
    setup_logging()
    
    try:
        # 添加src目录到Python路径
        src_path = Path(__file__).parent
        if str(src_path) not in sys.path:
            sys.path.insert(0, str(src_path))
        
        from PyQt5.QtWidgets import QApplication, QMessageBox
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
        
        # 显示错误对话框 - 修复sys引用问题
        try:
            # 确保在函数内部正确导入
            from PyQt5.QtWidgets import QApplication, QMessageBox
            
            # 创建临时应用实例显示错误信息
            app = QApplication([])
            QMessageBox.critical(
                None, 
                "启动错误", 
                f"应用启动时发生错误:\n{str(e)}\n\n请检查安装是否完整。"
            )
            return 1
        except Exception as dialog_error:
            # 如果连错误对话框都无法显示，直接打印到控制台
            print(f"严重错误: {dialog_error}")
            return 1

if __name__ == "__main__":
    # 确保sys在全局可用
    if 'sys' not in globals():
        import sys
    sys.exit(main())
