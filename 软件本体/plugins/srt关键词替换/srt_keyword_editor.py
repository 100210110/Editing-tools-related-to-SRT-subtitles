import sys, os, re, io, json
from build_automaton import SubtitleRuleProcessor
import time
from functools import wraps
from common import get_path
import logging

sys.stdin.reconfigure(encoding='utf-8')
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

logger = logging.getLogger('str_editor_plugin')
logs = "流程计时"

class Timer:
    def __init__(self, name: str, output=sys.stderr):
        self.name = name
        self.output = output
    def __enter__(self):
        self.start = time.perf_counter()
        return self
    def __exit__(self, *args):
        self.end = time.perf_counter()
        elapsed = (self.end - self.start) * 1000
        global logs
        logs += f"\n[TIMER] {self.name} 耗时: {elapsed:.2f} ms"




# 文明用语小助手
def print_times(count_dict):
    if not count_dict:
        str_text = "count_dict 内部为空\n" \
        "无实际处理文件"
        global logs
        logs += f"\n{str_text}"
        return str_text

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
def main(params):
    total_start = time.perf_counter()
    t0 = time.perf_counter()
    # 读取所有输入
    if not params:
        print("没有收到数据", file=sys.stderr)
        sys.exit(1)
    
    logger.info("params: {str(params)}")
            
    cache_dir = params.get("output_path")
    file_lists = params.get("pending_file_lists", [])
    # 确保输出路径存在
    os.makedirs(cache_dir, exist_ok=True)
    t1 = time.perf_counter()
    global logs
    logs += f"\n读取输入耗时: {(t1-t0)*1000:.2f} ms"

    deleted_counts = {}
    completed_output_list = []
    
    t2 = time.perf_counter()
    # 构件自动机、加载规则
    processor = SubtitleRuleProcessor()
    processor.load_rules()
    t3 = time.perf_counter()
    logs += f"\n加载规则（含构建自动机）耗时: {(t3-t2)*1000:.2f} ms"
    def process_srt_file(file_path):
        processor.reset_profanity_count()
        with open(file_path, 'r', encoding='utf-8') as f:
            original_text = f.read()
        cleaned_text = processor.process_text(original_text)
        return cleaned_text, processor.get_profanity_count()
    
    logs += "\n单独文件计时"
    for file_path in file_lists:    
        with Timer(f"处理{os.path.splitext(os.path.basename(file_path))[0]}"):
            if file_path.lower().endswith('.srt'):
                try:

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
            else:
                text = f"跳过非 SRT 文件：{file_path}"
                print(text, file=sys.stderr)
            

                
    str_text = print_times(deleted_counts)  # 输出删除统计
    total_end = time.perf_counter()
    logs += f"\n总耗时: {(total_end-total_start)*1000:.2f} ms"

    return_data = {
        "status": "ok",
        "processed": len(completed_output_list),
        "completed_output_lists": completed_output_list,
        "popup": {
            "title": "文明小助手",
            "message": str_text
        }
    }

    logger.info(f"{str(logs)}")
    logger.info(f"return_data: {return_data}")
    print(json.dumps(return_data, ensure_ascii=False), file=sys.stdout)

def run(params):
    logger.info(f"json传入run函数: {str(params)}")
    return main(params)


if __name__ == "__main__":
    run()