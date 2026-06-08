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
default_config = {"delete":{"profanity":["傻逼","傻波","卧槽","哎呦我草","我操","我草","我靠","我去","哦李现","what's up","what the fuck","我的fuck","fuck","你他妈的","你他喵的","ntmd","你妈的","nmd","他妈的","他喵的","TMD","tmd","妈的","喵的","md","你妈","nm","他妈","他喵","tm"],"others":["呃","huh","uh"]},"repeat":{"完了":{"max_times":2},"哈":{"max_times":3},"不行":{"max_times":3},"我知道":{"max_times":3},"别":{"max_times":3}},"replace":{"卡慕":["卡布","卡莫","卡木","卡不","卡姆","karm","come"],"卡慕SaMa":["卡慕sama","卡慕Sama","卡慕沙发","卡慕沙吧","砍不上吗","卡慕萨巴"],"谭俊峰":["传进风"],"米洛":["米诺","米罗","笔落"],"碧月狐":["碧月湖","闭月狐","毕业胡","b月湖","b月会","B2胡","月壶","夜壶","壁虎","鳖胡","别胡","憋活"],"曹某":["Tom"],"曹小龙":["草药龙","张小龙","操小龙","超小龙","曹勇","沙拉龙","条龙"],"qiqi":["KI KI","QIQI","QI QI"],"贺子鹏":["蔡子鹏","鹤头","赫德王"],"药儿":["幺儿"],"流赫":["流贺","刘贺","刘赫","刘河","刘恒"],"烦华":["芳芳"],"鸽一品":["葛一平","GEP"],"蘑菇牛":["蘑菇流"],"猪灵":["朱玲"],"烈焰人":["猎人"],"末影人":["梦人"],"末影龙":["莫云龙"],"龙息":["浓稀"],"细雪":["气血"],"煤炭":["没炭"],"岩浆":["岩尖"],"刷怪笼":["创二龙"],"末影水晶":["魔女水晶"],"主世界":["主界"],"OK":["okay"],"厉害":["牛逼"],"巴克什":["8个10","挖个10","BUG10"],"普坝":["普巴"],"大坝":["大巴"],"蓝汀":["蓝厅"],"水泥厂":["水泥铲"],"坝顶":["霸顶"],"西楼":["西路"],"报点":["爆点"],"破夜":["破译"],"AUG":["AOG"],"麦晓雯":["麦小文"],"威龙":["维鲁"],"弹挂":["半挂"],"护航":["护盘"],"六套":["刘涛","6炮"]}}


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

# 读配置，出问题则重置配置
def get_config():
    # 获取配置文件路径
    config_path = get_path("config.json", use_program_dir=True)
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"配置文件 {config_path} 未找到，重建默认配置", file=sys.stderr)
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, ensure_ascii=False, indent=4)
        return default_config
    except Exception as e:
        print(f"读取配置文件时发生错误: {e}", file=sys.stderr)
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, ensure_ascii=False, indent=4)
        print("已覆盖为默认配置文件\n", file=sys.stderr)
        return default_config

# 根据配置创建正则和替换函数
def create_regex():
    config = get_config()   # 从 json 读取配置

    delete_set = set()
    for category in config["delete"]:
        delete_set.update(config["delete"][category])
    profanity_set = set(config["delete"]["profanity"])
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
            if word in profanity_set:
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
        if i > 10:
            str_text += "   ...\n"
            break
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
        "processed": len(completed_output_list),
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