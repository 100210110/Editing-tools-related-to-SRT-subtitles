# -*- coding: utf-8 -*-
"""
插件统一入口（适用于打包成 exe）
所有事件处理函数都写在此文件中，通过事件名手动分发。
"""

import io
import sys
import json



# ==================== 各事件的具体处理函数 ====================
def event_main(params: dict):
    """默认事件（main）的处理逻辑"""
    from test import run
    run(params=params)
    return "默认事件执行成功"   # 该返回值会传递到 output_result


def event_test_2(params: dict):
    """install 事件的处理逻辑"""
    from test_1 import run
    run(params=params)
    return "安装完成"






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
        match event:
            case "main":
                result = event_main(params)
            
            case "test2":
                result = event_test_2(params)
                raise KeyboardInterrupt
    
            case _:
                result = event_main(params)


        # 执行成功，返回结果
        output_result(True, message=result)

    except Exception as e:
        import traceback
        traceback.print_exc(file=sys.stderr)
        output_result(False, message=str(e))