import sys
import os
import json
import io

# 强制所有标准流使用 UTF-8
sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding='utf-8')
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 实际执行替换的函数
def add_char_to_srt(srt_path, char, output_path=None):
    """在3 + 4 * i行插入字符"""
    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(srt_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    for i in range(2, len(lines), 4):
        lines[i] = char + lines[i].rstrip('\n') + '\n'

    out_path = output_path if output_path else srt_path
    with open(out_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)

    print(f"已处理：{srt_path}", file=sys.stderr)

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

    print(f"接收到 {len(file_lists)} 个文件路径", file=sys.stderr)
    print(f"输出目录: {cache_dir}", file=sys.stderr)

    completed_output_list = []  # 用于存储处理完成后的文件路径列表

    for file_path in file_lists:
        if os.path.isfile(file_path) and file_path.lower().endswith('.srt'):
            try:
                prefix = f"{os.path.splitext(os.path.basename(file_path))[0]}："
                
                # 构造输出文件完整路径：在 cache_dir 下保持原文件名
                base_name = os.path.basename(file_path)
                output_file = os.path.join(cache_dir, base_name)
                # 如果担心多个同名的文件（来自不同文件夹）会相互覆盖，可以加上来源目录的哈希或序号，但你的cache每次清空，暂时无妨
                
                add_char_to_srt(file_path, prefix, output_file)
                completed_output_list.append(output_file)

            except Exception as e:
                print(f"❌ 处理失败：{file_path}\n错误: {e}", file=sys.stderr)
        else:
            print(f"⚠️ 跳过非 SRT 文件：{file_path}", file=sys.stderr)

    return_data = {
    "status": "ok",
    "processed": len(file_lists),
    "completed_output_lists": completed_output_list,
    "popup": False
    }
    print(json.dumps(return_data, ensure_ascii=False), file=sys.stdout)
    sys.exit(0)  # 成功


if __name__ == "__main__":
    print("插件已启动，等待输入...", file=sys.stderr)
    main()