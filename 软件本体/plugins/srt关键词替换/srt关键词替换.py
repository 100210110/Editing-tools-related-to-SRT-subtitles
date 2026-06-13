import sys, os, re, io, json
from typing import Dict, List, Set
import ahocorasick
from build_automaton import SubtitleRuleProcessor

# 强制所有标准流使用 UTF-8
sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding='utf-8')
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


logs = ""


# 获取资源的绝对路径, 打包后默认返回只读目录, 容开发环境和 PyInstaller 打包后
def get_path(relative_path=None, use_program_dir=False):
    """获取程序目录或资源文件的绝对路径。
    
    参数:
        relative_path: 相对路径字符串。若为 None，返回程序所在目录。
        use_program_dir: 仅在打包后且 relative_path 非 None 时有效。
                         True  → 使用程序所在目录（sys.executable 所在目录）
                         False → 使用资源临时目录（sys._MEIPASS，只读）
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



# 文明用语小助手
def print_times(count_dict):
    if not count_dict:
        str_text = "count_dict 内部为空\n" \
        "无实际处理文件"
        global logs
        logs += f"\n{str_text}"

    str_text = ""

    # 按删除次数降序排序
    sorted_items = sorted(count_dict.items(), key=lambda item: item[1], reverse=True)
    i = 1
    str_text += "删词统计:\n"
    for file, count in sorted_items:
        if i > 10:
            str_text += "   ...\n"
            break
        str_text += f"{i}. {file} 抓到 {count} 个敏感词\n"
        i += 1

    str_text += "\n文明小助手提示您: \n" \
    "   视频千万条, 文明第一条\n" \
    "   讲话不规范, 后期两行泪\n"

    return str_text




# 主函数
def main():
    # 读取所有输入
    data = sys.stdin.read()
    if not data:
        print("没有收到数据", file=sys.stderr)
        sys.exit(1)
    
    try:
        params = json.loads(data)
    except json.JSONDecodeError as e:
        print(f"JSON解析失败: {e}", file=sys.stderr)
        sys.exit(1)
    
    cache_dir = params.get("output_path")
    file_lists = params.get("pending_file_lists", [])
    # 确保输出路径存在
    os.makedirs(cache_dir, exist_ok=True)

    deleted_counts = {}
    completed_output_list = []
    
    global logs
    logs += f"\n开始构建自动机"

    # 构件自动机、加载规则
    processor = SubtitleRuleProcessor()
    processor.load_rules()
    def process_srt_file(file_path):
        processor.reset_profanity_count()
        with open(file_path, 'r', encoding='utf-8') as f:
            original_text = f.read()
        cleaned_text = processor.process_text(original_text)
        return cleaned_text, processor.get_profanity_count()
    
    logs += f"\n构建自动机完成"

    for file_path in file_lists:
        if file_path.lower().endswith('.srt'):
            try:
                logs += f"\n正在处理{file_path}"

                cleaned_text, profanity_count = process_srt_file(file_path)
                base_name = os.path.splitext(os.path.basename(file_path))[0]
                deleted_counts[base_name] = profanity_count   # 直接存入统计结果
                # 生成输出文件名（保持原后缀）
                ext = os.path.splitext(file_path)[1]
                output_path = os.path.join(cache_dir, base_name + ext)


                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(cleaned_text)
                    completed_output_list.append(output_path)
            except Exception as e:
                text = f"处理失败：{file_path}, 错误: {e}"
                print(text, file=sys.stderr)
                logs += f"\n{text}"
        else:
            text = f"跳过非 SRT 文件：{file_path}"
            print(text, file=sys.stderr)
            logs += f"\n{text}"
            

                
    str_text = print_times(deleted_counts)  # 输出删除统计
    log_text = f"cache_dir: {cache_dir}\n" \
    f"file_lists: {file_lists}\n" \
    f"completed_output_list: {completed_output_list}\n" \
    f"logs :{logs}"

    return_data = {
        "status": "ok",
        "processed": len(completed_output_list),
        "completed_output_lists": completed_output_list,
        "popup": {
            "title": "文明小助手",
            "message": str_text
        }
    }
    print(json.dumps(return_data, ensure_ascii=False), file=sys.stdout)




if __name__ == "__main__":
    main()
