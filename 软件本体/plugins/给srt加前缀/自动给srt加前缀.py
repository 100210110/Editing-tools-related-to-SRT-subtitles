import sys
import os

# 实际执行替换的函数
def add_char_to_srt(srt_path, char, output_path=None):
    """在3 + 4 * i行插入字符"""
    with open(srt_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    for i in range(2, len(lines), 4):
        lines[i] = char + lines[i].rstrip('\n') + '\n'

    out_path = output_path if output_path else srt_path
    with open(out_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)

    print(f"已处理：{srt_path}")

if __name__ == "__main__":
    # 检查是否有文件路径参数
    if len(sys.argv) < 2:
        print("请将srt文件拖放到本脚本上, 手动输入没写")
        input("按 Enter 键退出...")
        sys.exit(1)

    elif len(sys.argv) >= 2:
        choose = input("是否使用文件名前缀作为字幕前缀？(y/n, 默认y): ").strip().lower() or 'y'
        if choose == 'y':
            use_filename = True
        else:
            use_filename = False


    # 支持一次拖放多个文件
    for file_path in sys.argv[1:]:
        if os.path.isfile(file_path) and file_path.lower().endswith('.srt'):
            try:
                if use_filename:
                    prefix = f"{os.path.splitext(os.path.basename(file_path))[0]}："
                else:
                    name = input(f"输入字幕前缀名, 默认Re: ").strip() or "Re"
                    prefix = f"{name}："
                add_char_to_srt(file_path, prefix)
            except Exception as e:
                print(f"❌ 处理失败：{file_path}\n错误: {e}")
        else:
            print(f"⚠️ 跳过非 SRT 文件：{file_path}")

    print("所有任务完成。")
    input("按 Enter 键退出...")