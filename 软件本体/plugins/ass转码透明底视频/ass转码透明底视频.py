import io
import os
import sys
import json
import pyass
import subprocess
from datetime import timedelta

if sys.stdin is not None:
    sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding='utf-8')
if sys.stdout is not None:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
if sys.stderr is not None:
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


# 打包前后都可获取指定文件的绝对路径
def get_path(relative_path=None, use_program_dir=True):
    """获取程序目录或资源文件的绝对路径。
    
    参数:
        relative_path: 相对路径字符串。若为 None，返回程序所在目录。
        use_program_dir: 仅在打包后且 relative_path 非 None 时有效。
                         True  → 使用程序所在目录, 文件夹内路径（sys.executable 所在目录）
                         False → 使用资源临时目录, 文件被打包进exe（sys._MEIPASS，只读）
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

# 把时间字符串转为时间增量（timedelta）对象，适用于ASS字幕的时间格式（H:MM:SS.CS）
def parse_ass_time(time_input) -> timedelta:
    if isinstance(time_input, timedelta):
        return time_input

    if isinstance(time_input, str):
        parts = time_input.split(':')
        if len(parts) == 3:
            hours = int(parts[0])
            minutes = int(parts[1])
            seconds, centiseconds = map(int, parts[2].split('.'))
            return timedelta(hours=hours, minutes=minutes, seconds=seconds, milliseconds=centiseconds * 10)
        raise ValueError(f"Invalid ASS time string format: {time_input}")

    raise TypeError(f"Expected timedelta or str, got {type(time_input).__name__}")

class SubtitleProcessor:
    def __init__(self, ass_path=None, temp_path=None):
        self.ass_path = ass_path
        self.temp_path = temp_path
        self.max_end_time = None
        self.play_res_x = None
        self.play_res_y = None
        self.ffmpeg_path = get_path(os.path.join("ffmpeg", "bin", "ffmpeg" + (".exe" if sys.platform == "win32" else "")))

    def modify_ass_path(self, new_ass_path):
        self.ass_path = new_ass_path
        self.max_end_time = None
        self.play_res_x = None
        self.play_res_y = None

    def get_max_end_time(self):
        if self.max_end_time is not None:
            return self.max_end_time
        if not os.path.exists(self.ass_path):
            raise FileNotFoundError(f"ASS file not found: {self.ass_path}")
        with open(self.ass_path, encoding="utf-8-sig") as f:
            script = pyass.load(f)
        # 虽说不知道谁会用空ass做处理，但还是加个判断
        if not script.events:
            self.max_end_time = timedelta(0)
        else:
            # 将字符串转换为 timedelta 后再取最大值
            end_times = [parse_ass_time(event.end) for event in script.events]
            self.max_end_time = max(end_times)
        return self.max_end_time

    def _parse_play_res(self):
        """从ASS文件中解析 PlayResX 和 PlayResY。"""
        self.play_res_x = None
        self.play_res_y = None
        with open(self.ass_path, encoding='utf-8-sig') as f:
            for line in f:
                line = line.strip()
                if line.startswith('PlayResX:'):
                    self.play_res_x = line.split(':')[1].strip()
                elif line.startswith('PlayResY:'):
                    self.play_res_y = line.split(':')[1].strip()
            
            if not self.play_res_x or not self.play_res_y:
                self.play_res_x = 1920
                self.play_res_y = 1080
    
    def export_transparent_video(self, output_video_path, fps=60):
        if not os.path.exists(self.ffmpeg_path):
            raise FileNotFoundError(f"不是, 你 FFmpeg 呢: {self.ffmpeg_path}")

        import shutil

        # 1. 获取时长、尺寸
        duration_td = self.get_max_end_time()
        duration_sec = duration_td.total_seconds()
        if duration_sec <= 0:
            raise ValueError("字幕时长为0")

        self._parse_play_res()
        if not self.play_res_x or not self.play_res_y:
            raise ValueError("缺少 PlayRes")
        video_w, video_h = int(self.play_res_x), int(self.play_res_y)

        # 2. 确定临时目录：优先用 self.temp_path，否则用当前工作目录
        temp_dir = self.temp_path if self.temp_path else os.getcwd()
        os.makedirs(temp_dir, exist_ok=True)

        # 生成唯一的临时字幕文件
        temp_ass_name = f"_temp_sub_{os.getpid()}.ass"
        temp_ass_path = os.path.join(temp_dir, temp_ass_name)
        shutil.copy2(self.ass_path, temp_ass_path)

        try:
            # 关键修改：只传递文件名，不包含任何路径
            filter_input = f'color=color=black@0:size={video_w}x{video_h}:rate={fps},format=rgba,subtitles={temp_ass_name}:alpha=1'

            input_args = [
                self.ffmpeg_path,
                "-report",
                "-y",
                "-f", "lavfi",
                "-i", filter_input,
                "-t", str(duration_sec),
                "-c:v", "qtrle",
                "-pix_fmt", "argb",
                output_video_path
            ]

            print(f"正在生成透明字幕视频: {output_video_path}", file=sys.stderr)
            print(f"命令: {' '.join(input_args)}", file=sys.stderr)
            print(f"工作目录: {temp_dir}", file=sys.stderr)

            # 启动子进程，并切换到临时目录
            if sys.platform == "win32":
                process = subprocess.Popen(
                    input_args,
                    cwd=temp_dir,  # 关键！
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    creationflags=subprocess.CREATE_NEW_CONSOLE
                )
            else:
                process = subprocess.Popen(
                    input_args,
                    cwd=temp_dir,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
            stdout, stderr = process.communicate()

            # 打印 FFmpeg 的输出（便于调试）
            if stdout:
                print(stdout, file=sys.stderr)
            if stderr:
                print(stderr, file=sys.stderr)

            if process.returncode != 0:
                print(f"FFmpeg 执行失败，返回码 {process.returncode}", file=sys.stderr)
                return False
            print(f"视频生成成功: {output_video_path}", file=sys.stderr)
            return True

        finally:
            if os.path.exists(temp_ass_path):
                os.unlink(temp_ass_path)



def test():
    file_path = get_path("test.ass")
    processor = SubtitleProcessor(file_path)
    max_end_time = processor.get_max_end_time()
    print(f"字幕总时长: {max_end_time}", file=sys.stderr)
    processor.export_transparent_video("output.mov")

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
    temp_dir = params.get("temp_path")
    file_lists = params.get("pending_file_lists", [])
    completed_output_list = []
    os.makedirs(cache_dir, exist_ok=True)
    os.makedirs(temp_dir, exist_ok=True)
    try:
        processor = SubtitleProcessor(temp_path=temp_dir)
        for file_path in file_lists:
            if os.path.splitext(file_path)[1].lower() != ".ass":
                continue

            processor.modify_ass_path(file_path)
            max_end_time = processor.get_max_end_time()
            print(f"字幕总时长: {max_end_time}", file=sys.stderr)
            # 假设输出路径是基于输入文件路径生成的
            output_path = os.path.join(cache_dir, os.path.basename(file_path).replace(".ass", ".mov"))
            if processor.export_transparent_video(output_path):
                completed_output_list.append(output_path)
                print(f"处理完成: {output_path}", file=sys.stderr)
            else:
                print(f"处理失败: {file_path}", file=sys.stderr)
    except Exception as e:
        print(f"处理过程中发生错误: {e}", file=sys.stderr)

    if not completed_output_list:
        if not file_lists:
            print("没有成功处理任何文件", file=sys.stderr)
            str_text = "一个文件都不传, 处理个蛋啊"
        else:
            print("没有成功处理任何文件", file=sys.stderr)
            str_text = "处理失败。\n" \
            "插件名: ASS转码透明底视频\n" \
            f"传入了 {len(file_lists)} 个文件, 真离谱, 全失败了。\n"

        return_data = {
            "status": "error",
            "processed": len(completed_output_list),
            "completed_output_lists": [],
            "popup": {
                "title": "ass处理出错",
                "message": str_text
            }
        }
        print(json.dumps(return_data, ensure_ascii=False), file=sys.stdout)
        sys.exit(1)

    return_data = {
        "status": "ok",
        "processed": len(completed_output_list),
        "completed_output_lists": completed_output_list
    }
    print(json.dumps(return_data, ensure_ascii=False), file=sys.stdout)

if __name__ == "__main__":
    main()