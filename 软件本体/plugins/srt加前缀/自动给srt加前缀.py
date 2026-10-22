import sys
import os
import json
import io
import re
import hashlib

# 强制所有标准流使用 UTF-8
sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding='utf-8')
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 时间轴行：00:00:01,000 --> 00:00:03,000；毫秒分隔符 , 和 . 都接受
TIME_LINE_RE = re.compile(r"\d{1,2}:\d{2}:\d{2}[,.]\d{1,3}\s*-->\s*\d{1,2}:\d{2}:\d{2}[,.]\d{1,3}")

# ---------- 缓存输出命名（与 srt关键词替换/common.py 保持同一口径） ----------
# 两个插件都往同一个 cache/output 写，不同目录的同名 SRT 会互相覆盖。
# 统一用「12 位哈希前缀 + __ + 原文件名」区分来源，主程序导出时再把前缀剥掉。
CACHE_NAME_HASH_LEN = 12
CACHE_NAME_SEPARATOR = "__"
CACHE_NAME_PREFIX_RE = re.compile(r'^[0-9a-f]{%d}%s' % (CACHE_NAME_HASH_LEN, CACHE_NAME_SEPARATOR))


def cache_output_name(src_path):
    """生成 cache/output 下的文件名：`<12位哈希>__<原文件名>`。

    前缀取源文件绝对路径（`normcase` 后）的 SHA-1 前 12 位；已带前缀的沿用，不叠加。
    """
    base_name = os.path.basename(src_path)
    if CACHE_NAME_PREFIX_RE.match(base_name):
        return base_name
    normalized = os.path.normcase(os.path.abspath(src_path))
    digest = hashlib.sha1(normalized.encode('utf-8')).hexdigest()[:CACHE_NAME_HASH_LEN]
    return f"{digest}{CACHE_NAME_SEPARATOR}{base_name}"


def strip_cache_prefix(file_name):
    """剥掉哈希前缀，还原原始文件名（说话人前缀按原始文件名取）。"""
    return CACHE_NAME_PREFIX_RE.sub('', os.path.basename(file_name))



class SrtFormatError(ValueError):
    """文件里没有可识别的字幕块（空文件、纯文本，或缺少时间轴行）。"""


def split_blocks(lines):
    """按空行切块；连续多个空行只算一个分隔符。"""
    blocks = []
    current = []
    for line in lines:
        if line.strip():
            current.append(line)
        elif current:
            blocks.append(current)
            current = []
    if current:
        blocks.append(current)
    return blocks


def find_time_index(block):
    """返回块内时间轴行的下标；块内没有时间轴则返回 None（不算有效字幕块）。"""
    for index, line in enumerate(block):
        if TIME_LINE_RE.search(line):
            return index
    return None


def add_prefix_to_text(block, char):
    """给块内第一个文本行加前缀，返回是否真的改动了这一块。

    序号行可有可无，文本行取时间轴行的下一行；已带 char 前缀的块原样保留（幂等）。
    """
    time_index = find_time_index(block)
    if time_index is None:
        return False
    text_index = time_index + 1
    if text_index >= len(block):
        return False  # 时间轴后面没有文本行，空字幕，无需处理
    if block[text_index].startswith(char):
        return False  # 已经带当前文件名前缀，不重复叠加
    block[text_index] = char + block[text_index]
    return True


# 实际执行替换的函数
def add_char_to_srt(srt_path, char, output_path=None):
    """给每个字幕块的第一个文本行插入字符。

    返回 (block_count, prefixed)：block_count 是有效字幕块数，
    prefixed 为 False 表示所有有效块都无需改动（即已带 char 前缀）。
    没有有效字幕块时抛 SrtFormatError。
    """
    with open(srt_path, 'r', encoding='utf-8-sig') as f:
        lines = f.read().splitlines()

    blocks = split_blocks(lines)
    block_count = 0
    prefixed = False
    for block in blocks:
        if find_time_index(block) is None:
            print(f"⚠️ 跳过非字幕块（无时间轴）：{srt_path}", file=sys.stderr)
            continue
        block_count += 1
        if add_prefix_to_text(block, char):
            prefixed = True

    if block_count == 0:
        raise SrtFormatError("没有找到带时间轴的字幕块")

    out_lines = []
    for block in blocks:
        out_lines.extend(block)
        out_lines.append("")
    if out_lines:
        out_lines.pop()

    out_path = output_path if output_path else srt_path
    if output_path:
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    # encoding=utf-8 写出无 BOM；newline='\n' 保证输出行尾固定为 \n，不随平台变化
    with open(out_path, 'w', encoding='utf-8', newline='\n') as f:
        f.write("\n".join(out_lines) + "\n")

    print(f"已处理：{srt_path}（字幕块 {block_count}）", file=sys.stderr)
    return block_count, prefixed

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

    total = len(file_lists)
    processed = 0  # 真正写入 cache/output 的文件数（幂等跳过也算，因为文件已正确落地）
    skipped = 0    # 非 SRT 文件 + 幂等跳过的 SRT
    failed = 0     # 路径不可处理（不存在/不可读）、读取异常、写入异常、无有效字幕块

    os.makedirs(cache_dir, exist_ok=True)

    for file_path in file_lists:
        if not file_path.lower().endswith('.srt'):
            print(f"⚠️ 跳过非 SRT 文件：{file_path}", file=sys.stderr)
            skipped += 1
            continue

        # 扩展名对但路径不可处理，属于失败而不是"跳过"：用户以为它在处理队列里，实际拿不到文件
        if not os.path.isfile(file_path):
            print(f"❌ 文件不存在或不可读：{file_path}", file=sys.stderr)
            failed += 1
            continue

        # 说话人名取原始文件名（链式处理时输入可能已带哈希前缀）
        speaker = os.path.splitext(strip_cache_prefix(file_path))[0]
        prefix = f"{speaker}："

        # 构造输出文件完整路径：在 cache_dir 下用「哈希前缀 + 原文件名」，同名不互相覆盖
        output_file = os.path.join(cache_dir, cache_output_name(file_path))

        try:
            _, prefixed = add_char_to_srt(file_path, prefix, output_file)
        except SrtFormatError as e:
            print(f"❌ 无有效字幕块：{file_path}\n原因: {e}", file=sys.stderr)
            failed += 1
            continue
        except Exception as e:
            print(f"❌ 处理失败：{file_path}\n错误: {e}", file=sys.stderr)
            failed += 1
            continue

        processed += 1
        if not prefixed:
            skipped += 1
            print(f"⏭️ 已带当前文件名前缀，跳过重复叠加：{file_path}", file=sys.stderr)
        completed_output_list.append(output_file)

    return_data = {
    "status": "ok",
    "processed": processed,
    "total": total,
    "skipped": skipped,
    "failed": failed,
    "completed_output_lists": completed_output_list,
    "popup": False
    }
    print(json.dumps(return_data, ensure_ascii=False), file=sys.stdout)
    sys.exit(0)  # 成功


if __name__ == "__main__":
    print("插件已启动，等待输入...", file=sys.stderr)
    main()
