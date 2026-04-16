import sys
import os
import json
import re
import io

# 强制所有标准流使用 UTF-8
sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding='utf-8')
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


# 默认配置
default_config = {
    "delete": ["卧槽", "我操", "我草", "what's up", "你他妈的", "ntmd", "你妈的", "nmd", "他妈的", "tmd", "妈的", "md", "你妈", "nm", "他妈", "tm"],
    "replace": {
        "卡慕": ["卡布", "卡莫", "卡木", "傻逼"],
        "米洛": ["米诺", "米罗"],
        "碧月狐": ["月壶", "夜壶", "壁虎"]
    }
}


# 读配置，出问题则重置配置
def get_config():
    try:
        with open("config.json", 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print("配置文件 config.json 未找到\n" \
        "重建默认配置文件", file=sys.stderr)
        with open("config.json", 'w', encoding='utf-8') as f:
            json.dump(default_config, f, ensure_ascii=False, indent=4)
        return default_config
    except Exception as e:
        print(f"读取配置文件时发生错误: {e}", file=sys.stderr)
        with open("config.json", 'w', encoding='utf-8') as f:
            json.dump(default_config, f, ensure_ascii=False, indent=4)
        print("已覆盖为默认配置文件\n", file=sys.stderr)
        return default_config

# 根据配置创建正则和替换函数
def create_regex():
    config = get_config()   # 从 json 读取配置

    delete_set = set(config["delete"])
    bad_to_good = {}
    for good, bad_list in config["replace"].items():
        for bad in bad_list:
            bad_to_good[bad] = good

    all_keywords = list(delete_set) + list(bad_to_good.keys())
    all_keywords.sort(key=len, reverse=True)
    regex = re.compile("|".join(re.escape(k) for k in all_keywords))
    print(f"已加载配置: {len(delete_set)} 个删除词, {len(bad_to_good)} 个替换词\n", file=sys.stderr)

    # 闭包：捕获 delete_set 和 bad_to_good
    deleted_times = 0
    def replacer(match):
        word = match.group(0)
        if word in delete_set:
            nonlocal deleted_times
            deleted_times += 1
            return ""
        elif word in bad_to_good:
            return bad_to_good[word]
        else:
            return word
    
    # 重置删除计数
    def reset_deleted_count():
        nonlocal deleted_times
        deleted_times = 0
    
    # 获取删除计数
    def get_deleted_count():
        return deleted_times

    # 返回一个可直接处理文本的函数
    def process(text):
        return regex.sub(replacer, text)

    return process, reset_deleted_count, get_deleted_count

# 文本处理函数
def clean_text(file_path, processor):
    with open(file_path, 'r', encoding='utf-8') as f:
        text = f.read()
    return processor(text)


# 文明用语小助手
def print_times(count_dict):

    str_text = ""

    # 按删除次数降序排序
    sorted_items = sorted(count_dict.items(), key=lambda item: item[1], reverse=True)
    i = 1
    str_text += "删词统计:\n"
    for file, count in sorted_items:
        str_text += f"{i}. {file} 抓到 {count} 个敏感词\n"
        i += 1

    str_text += "\n文明小助手提示您: \n" \
    "   视频千万条, 文明第一条\n" \
    "   讲话不规范, 后期两行泪"

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
    


    # 解包三个函数
    process_func, reset_count, get_count = create_regex()
    
    os.makedirs(cache_dir, exist_ok=True)

    deleted_counts = {}
    completed_output_list = []
    for file_path in file_lists:
        # 你的原有处理逻辑
        print(f"处理: {file_path}", file=sys.stderr)
        if os.path.isfile(file_path) and file_path.lower().endswith('.srt'):
            try:
                reset_count()                           # 重置计数
                text = clean_text(file_path, process_func)   # 处理文本
                
                base_name = os.path.splitext(os.path.basename(file_path))[0]
                deleted_counts[base_name] = get_count()      # 获取计数
                
                # 生成输出文件名（保持原后缀）
                ext = os.path.splitext(file_path)[1]
                output_path = os.path.join(cache_dir, base_name + ext)


                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(text)
                    completed_output_list.append(output_path)

                print(f"已处理：{file_path} -> {output_path}", file=sys.stderr)
            except Exception as e:
                print(f"❌ 处理失败：{file_path}\n错误: {e}", file=sys.stderr)
        else:
            print(f"⚠️ 跳过非 SRT 文件：{file_path}", file=sys.stderr)

    str_text = print_times(deleted_counts)  # 输出删除统计

    return_data = {
        "status": "ok",
        "processed": len(file_lists),
        "completed_output_lists": completed_output_list,
        "popup": {
            "title": "文明小助手",
            "message": str_text
        }
    }
    print(json.dumps(return_data, ensure_ascii=False), file=sys.stdout)



# 测试
def test():
    create_regex()
    pass


if __name__ == "__main__":
    main()





# # 旧的主函数
# def main_old():
#     # 检查是否有文件路径参数
#     if len(sys.argv) < 2:
#         print("请将srt文件拖放到本脚本上, 手动输入没写\n" \
#         "本工具为替换文本文件关键词用\n" \
#         "1. 把文件拖到本工具上\n" \
#         "2. 选择是否需要新建文件\n" )
#         get_config()  # 确保配置文件存在
#         input("按 Enter 键退出...")
#         sys.exit(1)

#     # 解包三个函数
#     process_func, reset_count, get_count = create_regex()
#     base_dir = get_base_dir()
#     temp_dir = os.path.join(base_dir, "output")
#     os.makedirs(temp_dir, exist_ok=True)

#     deleted_counts = {}
#     for file_path in sys.argv[1:]:
#         if os.path.isfile(file_path) and file_path.lower().endswith('.srt'):
#             try:
#                 reset_count()                           # 重置计数
#                 text = clean_text(file_path, process_func)   # 处理文本
                
#                 base_name = os.path.splitext(os.path.basename(file_path))[0]
#                 deleted_counts[base_name] = get_count()      # 获取计数
                
#                 # 生成输出文件名（保持原后缀）
#                 ext = os.path.splitext(file_path)[1]
#                 output_path = os.path.join(temp_dir, base_name + ext)

#                 # 重名处理
#                 counter = 1
#                 while os.path.exists(output_path):
#                     output_path = os.path.join(temp_dir, f"{base_name}_{counter}{ext}")
#                     counter += 1

#                 with open(output_path, 'w', encoding='utf-8') as f:
#                     f.write(text)
#                 print(f"已处理：{file_path} -> {output_path}")
#             except Exception as e:
#                 print(f"❌ 处理失败：{file_path}\n错误: {e}")
#         else:
#             print(f"⚠️ 跳过非 SRT 文件：{file_path}")

#     print_times(deleted_counts)  # 输出删除统计