import os, sys, json, re, hashlib
# logger
import logging
from logging.handlers import RotatingFileHandler


# ---------- 缓存输出命名 ----------
# 插件都往同一个 cache/output 写，不同目录的同名 SRT 会互相覆盖。
# 统一用「12 位哈希前缀 + __ + 原文件名」区分来源，导出时再把前缀剥掉。
CACHE_NAME_HASH_LEN = 12
CACHE_NAME_SEPARATOR = "__"
CACHE_NAME_PREFIX_RE = re.compile(r'^[0-9a-f]{%d}%s' % (CACHE_NAME_HASH_LEN, CACHE_NAME_SEPARATOR))


def cache_output_name(src_path):
    """生成 cache/output 下的文件名：`<12位哈希>__<原文件名>`。

    前缀取源文件绝对路径（`normcase` 后）的 SHA-1 前 12 位：同一路径重复处理结果稳定，
    不同目录的同名文件则不同。已经带前缀的（链式处理产生的中间产物）原样沿用，
    不会叠加第二层前缀。
    """
    base_name = os.path.basename(src_path)
    if CACHE_NAME_PREFIX_RE.match(base_name):
        return base_name
    normalized = os.path.normcase(os.path.abspath(src_path))
    digest = hashlib.sha1(normalized.encode('utf-8')).hexdigest()[:CACHE_NAME_HASH_LEN]
    return f"{digest}{CACHE_NAME_SEPARATOR}{base_name}"


def strip_cache_prefix(file_name):
    """剥掉哈希前缀，还原原始文件名（导出、统计与说话人前缀都用它）。"""
    return CACHE_NAME_PREFIX_RE.sub('', os.path.basename(file_name))


def find_duplicate_sources(rules):
    """扫描 replace 树，找出**跨节点**重复的 source。

    返回 `[{"source": "卡布", "targets": ["卡慕", "卡布"]}]`，`targets` 按出现顺序去重。
    口径与主处理器一致：只统计 `enabled` 的节点，`group` 递归子项，其他类型忽略。
    同一个替换项内部的重复不算冲突（本来就只防单个 item 内重复）。
    """
    owners = {}
    order = []

    def walk(node):
        if not isinstance(node, dict) or not node.get("enabled", True):
            return
        node_type = node.get("type", "correction")
        if node_type == "group":
            for child in node.get("items", []) or []:
                walk(child)
            return
        if node_type != "correction":
            return
        word = node.get("word")
        for src in node.get("source", []) or []:
            targets = owners.setdefault(src, [])
            if word not in targets:
                targets.append(word)
            if src not in order:
                order.append(src)

    for node in rules.get("replace", []) or []:
        walk(node)
    return [{"source": src, "targets": owners[src]} for src in order if len(owners[src]) > 1]


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
