import os, sys, json
# logger
import logging
from logging.handlers import RotatingFileHandler


# 获取资源的绝对路径, 打包后默认返回只读目录, 容开发环境和 PyInstaller 打包后
def get_path(relative_path=None, use_program_dir=False):
    """获取程序目录或资源文件的绝对路径。
    
    参数:
        relative_path: 相对路径字符串。若为 None, 返回程序所在目录。
        use_program_dir: 仅在打包后且 relative_path 非 None 时有效。
                         True  → 使用程序所在目录 (sys.executable 所在目录)
                         False → 使用exe内只读目录 (sys._MEIPASS, 只读)
                         开发环境下此参数无区别。
    
    返回:
        绝对路径字符串。
    """
    if getattr(sys, 'frozen', False):
        # PyInstaller 打包后
        if relative_path is None or use_program_dir:
            base_path = os.path.dirname(sys.executable)  # 程序目录，可写
        else:
            base_path = sys._MEIPASS                      # 只读资源目录
    else:
        # 开发环境（脚本运行）
        base_path = os.path.dirname(os.path.abspath(__file__))
    
    if relative_path is None:
        return base_path
    else:
        return os.path.join(base_path, relative_path)




# 全局标志，防止重复配置
_logger_configured = False

def setup_logger(log_dir):
    """
    log_dir: 日志存放的目录路径，例如 '/plugin_root/plugin_log'
    """
    global _logger_configured
    if _logger_configured:
        return logging.getLogger('str_editor_plugin')  # 已配置则直接返回

    # 1. 创建日志目录（如果不存在）
    os.makedirs(log_dir, exist_ok=True)

    # 2. 读取 manifest.json（位于 log_dir 的父目录）
    manifest_path = get_path("manifest.json", use_program_dir=True)
    try:
        with open(manifest_path, 'r', encoding='utf-8') as f:
            debug = json.load(f).get("debug", False)
    except Exception:
        debug = False  # 默认关闭调试日志，但错误日志仍会记录

    # 3. 创建 logger
    logger = logging.getLogger('str_editor_plugin')
    logger.setLevel(logging.DEBUG if debug else logging.INFO)

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
    )

    # 4. 错误日志（始终写入）
    error_path = os.path.join(log_dir, "plugin_error.log")
    error_handler = RotatingFileHandler(
        error_path, maxBytes=10*1024*1024, backupCount=5, encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    logger.addHandler(error_handler)

    # 5. 调试/信息日志（仅当 debug=True）
    if debug:
        info_path = os.path.join(log_dir, "plugin_info.log")
        info_handler = RotatingFileHandler(
            info_path, maxBytes=10*1024*1024, backupCount=5, encoding='utf-8'
        )
        info_handler.setLevel(logging.DEBUG)
        info_handler.setFormatter(formatter)
        logger.addHandler(info_handler)

    _logger_configured = True
    return logger
