# -*- coding: utf-8 -*-
import io
import os
import sys
import json
from common import get_path, setup_logger

sys.stdin.reconfigure(encoding='utf-8')
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

logger = setup_logger(get_path("plugin_log", use_program_dir=True))  
logger.info("程序启动成功")


# ==================== 各事件的具体处理函数 ====================
def event_main(params):
    """默认事件（main）的处理逻辑"""
    from srt_keyword_editor import run
    
    logger.info(str(params))
    run(params=params)
    return "默认事件执行成功"   # 该返回值会传递到 output_result


def event_subtitle_rule_editor():
    """字幕替换规则编辑器"""
    from subtitle_rule_editor import run

    exit_code = run()
    logger.info(f"规则编辑器关闭，退出码: {exit_code}")
    return "字幕替换规则修改完成"


# ==================== 事件分发 ====================
def handle_event(event, params):
    """按事件名分发，并负责统一输出。

    `main` 分支由 `srt_keyword_editor.main()` 自己输出带 `completed_output_lists`
    的结果 JSON，这里不重复输出；其余事件统一经 `output_result` 输出。

    子函数直接 `sys.exit` 抛出的 `SystemExit` 由调用方的 `except SystemExit` 接住，
    保证"先输出统一 JSON 再退出"，不会让主程序收到空 stdout。
    """
    match event:
        case "subtitle_rule_editor":
            result = event_subtitle_rule_editor()
            output_result(True, message=result)
        case _:
            event_main(params)






# ==================== 统一输出格式 ====================
def output_result(success: bool, message=None):
    return_data = {
        "status": success,
        "popup": {
            "title": "返回消息",
            "message": f"{message}"
        }
    }
    print(json.dumps(return_data, ensure_ascii=False), file=sys.stdout)





if __name__ == "__main__":

    # 读取输入, 解析 JSON
    raw = sys.stdin.read()
    if not raw:
        output_result(False, message="stdin 无传入数据")
        sys.exit(1)
    try:
        params = json.loads(raw)
    except json.JSONDecodeError as e:
        output_result(False, message=f"JSON解析失败: {e}")
        sys.exit(1)


    # 手动分发事件到对应的处理函数
    event = params.get("event", "main")
    try:
        handle_event(event, params)

    except SystemExit as e:
        # 子函数直接 sys.exit 时兜底：SystemExit 不是 Exception，必须单独接住，
        # 否则主程序收不到 JSON。0 视为正常结束，非 0 报失败。
        code = e.code if isinstance(e.code, int) else 1
        logger.info(f"插件在事件 {event} 中提前退出，退出码: {code}")
        if code == 0:
            output_result(True, message="插件正常结束")
        else:
            output_result(False, message=f"插件提前退出（退出码 {code}）")

    except Exception as e:
        import traceback
        error_msg = traceback.format_exc()
        # 写入日志
        logger.error(error_msg)
        traceback.print_exc(file=sys.stderr)
        output_result(False, message=str(e))