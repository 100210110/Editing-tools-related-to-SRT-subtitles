import PySimpleGUI as sg
from tkinterdnd2 import DND_FILES, TkinterDnD
import re
import sys
import os
import json
import subprocess

file_list = []  # 全局文件列表变量

def parse_dropped_files(data):
    data = data.strip()
    if not data:
        return []
    if '{' in data and '}' in data:
        return re.findall(r'{([^{}]*)}', data)
    if '\n' in data:
        return [p for p in data.split('\n') if p.strip()]
    if ' ' in data:
        parts = data.split(' ')
        return [p for p in parts if p.strip()]
    return [data]

def update_listbox(window, file_list):
    """同步更新列表框显示"""
    window["-FILE_LIST-"].update(values=file_list)
    print(f"更新列表框: {file_list}")


def on_drop(event, window):
    global file_list
    raw_data = event.data
    print("\n=== 拖放事件 ===")
    print("原始数据:", repr(raw_data))
    new_paths = parse_dropped_files(raw_data)
    print("新拖入的路径:", new_paths)
    # 去重添加
    added = 0
    for p in new_paths:
        if p not in file_list:
            file_list.append(p)
            added += 1
    print(f"添加了 {added} 个新文件")
    print(f"当前文件列表: {file_list}")
    update_listbox(window, file_list)
    print("===============\n")





# 扫描插件，返回列表：每个元素为 (category, name, exe_path, unique_key)
def scan_plugins(plugins_dir="plugins"):
    plugins = []
    if not os.path.exists(plugins_dir):
        return plugins
    for folder in os.listdir(plugins_dir):
        folder_path = os.path.join(plugins_dir, folder)
        if not os.path.isdir(folder_path):
            continue
        json_path = os.path.join(folder_path, "manifest.json")
        if not os.path.exists(json_path):
            continue
        with open(json_path, "r", encoding="utf-8") as f:
            info = json.load(f)
        name = info.get("name", folder)
        category = info.get("category", "未分类")
        exe_path = os.path.join(folder_path, info.get("executable", ""))
        if not os.path.exists(exe_path):
            print(f"警告：插件 {name} 的可执行文件不存在 {exe_path}")
            continue
        # 生成唯一 key，例如 "PLUGIN_字幕自动打轴"
        key = f"PLUGIN_{name}"
        plugins.append((category, name, exe_path, key))
    return plugins

# 动态构建 layout
def build_layout(plugins):
    # 固定部分（文件列表区域）
    layout = [
        [sg.Text("拖入文件，可以选中一个或多个移除")],
        [sg.Listbox(values=[], size=(80, 15), key="-FILE_LIST-", select_mode=sg.SELECT_MODE_EXTENDED)],
        [sg.Button("清空所有"), sg.Button("移除选中")],
    ]
    
    # 按类别分组
    categories = {}
    for cat, name, exe_path, key in plugins:
        categories.setdefault(cat, []).append((name, exe_path, key))
    
    # 为每个类别添加一个 Frame（可折叠的框），内部每个按钮一行
    for cat, items in categories.items():
        # 类别标题（不可点击，仅用于分组）
        layout.append([sg.Text(cat, font=("微软雅黑", 10, "bold"))])
        # 该类别下的所有按钮，每个占一行
        for name, exe_path, key in items:
            layout.append([sg.Button(name, key=key, size=(20, 1))])
        layout.append([sg.HorizontalSeparator()])  # 分割线
    
    return layout

# 把文件列表发送给插件执行
def run_plugin(plugin_path, file_list):

    # 获取脚本/EXE所在目录
    if getattr(sys, 'frozen', False):
        # 打包成EXE后的路径
        program_dir = os.path.dirname(sys.executable)
    else:
        # 开发时运行的脚本路径
        program_dir = os.path.dirname(os.path.abspath(__file__))

    # 然后拼接自定义文件夹，例如 "cache"
    cache_dir = os.path.join(program_dir, "cache/output")

    forward_json = {
        "output_path": cache_dir,  # 插件可以从这里读取输出路径等参数
        "pending_file_lists": file_list  # 直接传递文件列表
    }

    json_str = json.dumps(forward_json, ensure_ascii=False)

    proc = subprocess.Popen(
        [sys.executable, plugin_path],   # 确保用当前解释器执行
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        encoding='utf-8'                 # 明确 UTF-8 编码
    )

    stdout, stderr = proc.communicate(json_str)

    if proc.returncode == 0:
        print("插件处理成功")
        if stdout:
            print(stdout)
    else:
        print(f"插件出错，退出码 {proc.returncode}")
        if stderr:
            print(stderr)

# 主程序
def main():
    # 扫描插件
    plugins = scan_plugins()
    if not plugins:
        sg.popup_error("未找到任何插件，请检查 plugins 文件夹")
        return
    
    root = TkinterDnD.Tk()
    root.withdraw()

    layout = build_layout(plugins)
    window = sg.Window("视频后期工具箱", layout, finalize=True)

    listbox_widget = window["-FILE_LIST-"].Widget
    listbox_widget.drop_target_register(DND_FILES)
    listbox_widget.dnd_bind('<<Drop>>', lambda e: on_drop(e, window))


    if len(sys.argv) > 1:
        print("从命令行参数添加文件:")
        for file_path in sys.argv[1:]:
            file_list.append(file_path)
            print(f"添加: {file_path}")
        update_listbox(window, file_list)

    def refresh_listbox():
        update_listbox(window, file_list)
    
    # 事件循环
    while True:
        event, values = window.read()
        if event == sg.WIN_CLOSED:
            break
        
        # 固定按钮
        if event == "清空所有":
            file_list.clear()
            update_listbox(window, file_list)
            print("\n手动清空所有文件\n")
        
        if event == "移除选中":
            print("\n=== 移除选中事件 ===")
            print("当前文件列表:", file_list)
            selected_values = values["-FILE_LIST-"]  # 选中的值
            print("选中的值:", selected_values)
            if not selected_values:
                sg.popup("请先选中要移除的项目")
            else:
                # 从 file_list 中删除选中的项
                original_len = len(file_list)
                for item in selected_values:
                    if item in file_list:
                        file_list.remove(item)
                print(f"删除了 {original_len - len(file_list)} 个文件")
                print(f"剩余文件列表: {file_list}")
                update_listbox(window, file_list)
            print("==================\n")
        
        # 插件按钮：所有插件按钮的 key 都以 "PLUGIN_" 开头
        elif event.startswith("PLUGIN_"):
            # 根据 key 找到对应的插件信息
            for cat, name, exe_path, key in plugins:
                if key == event:
                    print(f"启动插件：{name}")
                    run_plugin(exe_path, file_list)
                    break
            else:
                print(f"未找到插件：{event}")
    
    window.close()


if __name__ == "__main__":
    main()


# root = TkinterDnD.Tk()
# root.withdraw()

# layout = [
#     [sg.Text("拖入文件，可以选中一个或多个移除")],
#     [sg.Listbox(values=[], size=(80, 15), key="-FILE_LIST-", select_mode=sg.SELECT_MODE_EXTENDED)],
#     [sg.Button("清空所有"), sg.Button("移除选中")],
#     [sg.Text("字幕处理相关")],
#     [sg.Button("占位1", size=(10, 1), key="-测试-")]
# ]

# window = sg.Window("Re插件调度台", layout, finalize=True, location=(500,300))

# listbox_widget = window["-FILE_LIST-"].Widget
# listbox_widget.drop_target_register(DND_FILES)
# listbox_widget.dnd_bind('<<Drop>>', lambda e: on_drop(e, window))


# # 用一个独立的 Python 列表来存储所有文件路径
# file_list = []

# if len(sys.argv) > 1:
#     print("从命令行参数添加文件:")
#     for file_path in sys.argv[1:]:
#         file_list.append(file_path)
#         print(f"添加: {file_path}")
#     update_listbox(window, file_list)

# # 扫描插件并创建按钮
# while True:
#     event, values = window.read()
#     if event == sg.WIN_CLOSED:
#         break

#     if event == "清空所有":
#         file_list.clear()
#         update_listbox(window, file_list)
#         print("\n手动清空所有文件\n")

#     if event == "移除选中":
#         print("\n=== 移除选中事件 ===")
#         selected_values = values["-FILE_LIST-"]  # 选中的值
#         print("选中的值:", selected_values)
#         if not selected_values:
#             sg.popup("你也没选中啊")
#         else:
#             # 从 file_list 中删除选中的项
#             original_len = len(file_list)
#             for item in selected_values:
#                 if item in file_list:
#                     file_list.remove(item)
#             print(f"删除了 {original_len - len(file_list)} 个文件")
#             print(f"剩余文件列表: {file_list}")
#             update_listbox(window, file_list)
#         print("==================\n")
    
#     if event == "-测试-":
#         sg.popup("这是一个占位按钮，可以绑定其他功能")

# window.close()