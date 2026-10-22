import zipfile
import json
import os
import re
import sys
import shutil
import time
import zlib
import PySimpleGUI as sg
from packaging.version import parse as parse_version


# 插件目录名白名单：字母、数字、下划线、连字符、中文
PLUGIN_ID_PATTERN = re.compile(r'^[\w\u4e00-\u9fff-]+$')

# 安装前自动备份的被覆盖文件存放处（相对程序目录），刻意放在插件目录之外：
# 既不会被 rmtree 删掉，也不会被主程序当成插件目录扫描。
PLUGIN_BACKUP_ROOT = os.path.join("cache", "plugin_backup")


def get_path(relative_path=None, use_program_dir=True):
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

class PluginInstaller:
    def __init__(self, zip_path):
        self.zip_path = zip_path
        self.name = None
        self.version = None
        self.description = None
        self.plugin_path = None
        # 包完整性校验失败的原因（单行文本），供批量导入汇总提示使用
        self.rejection_reason = None
        # 本次安装前备份了哪些将被覆盖的文件（相对路径列表）与备份目录
        self.backed_up = []
        self.backup_dir = None

    # 校验 plugin_id，防止拼出 plugins/ 之外的安装路径
    @staticmethod
    def _validate_plugin_id(plugin_id):
        if not isinstance(plugin_id, str):
            raise ValueError("plugin_id 必须是字符串")
        if not plugin_id or plugin_id != plugin_id.strip():
            raise ValueError("plugin_id 不能为空，首尾不能有空格")
        if plugin_id in (".", ".."):
            raise ValueError("plugin_id 不能是 . 或 ..")
        if os.path.isabs(plugin_id) or os.path.splitdrive(plugin_id)[0]:
            raise ValueError("plugin_id 不能是绝对路径或盘符路径")
        if "/" in plugin_id or "\\" in plugin_id:
            raise ValueError("plugin_id 不能包含路径分隔符")
        if not PLUGIN_ID_PATTERN.fullmatch(plugin_id):
            raise ValueError("plugin_id 仅允许字母、数字、下划线、连字符和中文")
        return plugin_id

    # 校验安装路径必须位于 plugins/ 下，并返回 realpath 后的路径
    @staticmethod
    def _validate_install_path(plugin_path):
        if not plugin_path:
            raise ValueError("插件安装路径为空")
        plugins_root = os.path.realpath(get_path("plugins"))
        target_path = os.path.realpath(plugin_path)
        try:
            common_path = os.path.commonpath([plugins_root, target_path])
        except ValueError:
            raise ValueError(f"插件安装路径不在 plugins 目录下: {plugin_path}") from None
        if (os.path.normcase(common_path) != os.path.normcase(plugins_root)
                or os.path.normcase(target_path) == os.path.normcase(plugins_root)):
            raise ValueError(f"插件安装路径不在 plugins 目录下: {plugin_path}")
        return target_path

    # 测试函数
    def test(self):
        
        try:
            with open(os.path.join(self.plugin_path, 'manifest.json'), 'r', encoding='utf-8') as f:
                data = json.load(f)
                print("压缩包信息: ")
                print(f"插件路径: {self.plugin_path}")
                print(f"名称: {self.name}")
                print(f"版本: {self.version}")
                print(f"描述: {self.description}")
                print(f"安装路径: {self.plugin_path}")
                print("\n已安装插件信息: ")
                print(f"名称: {data.get('name', '未知')}")
                print(f"版本: {data.get('version', '未知')}")
                print(f"描述: {data.get('description', '无描述')}")
        except Exception as e:
            print(f"读取已安装插件信息出错: {e}", file=sys.stderr)
    
    # 加载zip文件内的manifest.json来更新插件信息
    def load_zip_json(self):
        try:
            with zipfile.ZipFile(self.zip_path, 'r') as zf:
                with zf.open('manifest.json') as f:
                    data = json.load(f)
                    self.name = data["name"]
                    self.version = data["version"]
                    self.description = data.get("description", "这个插件没写描述")
                    plugin_id = data.get("plugin_id", self.name)
                    try:
                        plugin_id = self._validate_plugin_id(plugin_id)
                        plugin_path = os.path.join(get_path("plugins"), plugin_id)
                        self.plugin_path = self._validate_install_path(plugin_path)
                    except ValueError as e:
                        print(f"拒绝安装插件 {self.zip_path}: {e}", file=sys.stderr)
                        sg.popup_error(f"插件安装被拒绝:\n{e}")
                        return False
        except Exception as e:
            print(f"加载压缩包 {self.zip_path} 出错: {e}", file=sys.stderr)
            return False
        return True
    
    # 在 zip 成员列表里解析可执行文件名，语义与 插件调度主程序.py 的 _resolve_executable 一致
    @staticmethod
    def _resolve_member(names, executable):
        """把 manifest 里的 executable 解析成压缩包内的成员名；解析不到返回 None。

        允许省略扩展名（__init__ → __init__.py / __init__.exe），
        与运行时 _resolve_executable 保持一致，避免“装的时候判有、用时判无”。
        """
        if not executable:
            return None
        normalized = executable.replace("\\", "/")
        if normalized in names:
            return normalized
        base = os.path.splitext(normalized)[0]
        for ext in (".py", ".exe"):
            candidate = base + ext
            if candidate in names:
                return candidate
        return None

    # 把 manifest 归一化成 [(按钮名, executable)]，兼容旧式单按钮格式
    @staticmethod
    def _manifest_buttons(info):
        """返回 manifest 声明的按钮列表；结构非法时抛 ValueError。

        校验规则与主程序 _build_buttons 保持一致，否则会出现“装得上但加载不了”。
        """
        if "buttons" in info:
            buttons = info.get("buttons")
            if not isinstance(buttons, list) or not buttons:
                raise ValueError("buttons 为空或不是列表")
            result = []
            for index, button in enumerate(buttons, 1):
                if not isinstance(button, dict):
                    raise ValueError(f"buttons 第 {index} 项不是对象")
                label = button.get("label")
                executable = button.get("executable")
                if not label or not executable:
                    raise ValueError(f"buttons 第 {index} 项缺少 label 或 executable")
                result.append((label, executable))
            return result

        executable = info.get("executable")
        if not executable:
            raise ValueError("manifest 缺少 executable")
        return [(info.get("name", "插件"), executable)]

    def validate_package(self, show_error=True):
        """安装前静态校验压缩包：每个按钮声明的可执行文件都必须真的在包内。

        只读 zip 成员列表，不解压、不触碰已安装目录，因此校验失败时旧插件保持原样。
        失败原因写入 self.rejection_reason，并可在批量导入时由调用方统一提示：
        show_error=False 时不弹窗，避免与“以下文件未导入”的汇总提示重复弹两次。
        返回 True=可安装；False=已拒绝（调用方不得继续安装）。
        """
        self.rejection_reason = None
        try:
            with zipfile.ZipFile(self.zip_path, "r") as zf:
                names = {member.replace("\\", "/") for member in zf.namelist()}
                if "manifest.json" not in names:
                    raise ValueError("压缩包内缺少 manifest.json")
                with zf.open("manifest.json") as f:
                    info = json.load(f)
                if not isinstance(info, dict):
                    raise ValueError("manifest.json 顶层不是对象")
                buttons = self._manifest_buttons(info)
        except Exception as e:
            print(f"校验压缩包 {self.zip_path} 失败: {e}", file=sys.stderr)
            self.rejection_reason = f"插件包校验失败：{e}"
            if show_error:
                sg.popup_error(
                    f"插件包校验失败，已中止安装（现有插件未改动）：\n{e}",
                    title="导入插件失败",
                )
            return False

        missing = [
            (label, executable)
            for label, executable in buttons
            if self._resolve_member(names, executable) is None
        ]
        if missing:
            detail = "\n".join(f"  · 按钮「{label}」→ {executable}" for label, executable in missing)
            print(f"压缩包 {self.zip_path} 不完整，缺少可执行文件:\n{detail}", file=sys.stderr)
            self.rejection_reason = "压缩包里找不到以下可执行文件：" + "；".join(
                f"按钮「{label}」→ {executable}" for label, executable in missing
            )
            if show_error:
                sg.popup_error(
                    "插件包不完整，已中止安装（现有插件未改动）。\n"
                    f"压缩包里找不到以下可执行文件：\n{detail}\n"
                    "请重新获取完整的插件包。",
                    title="导入插件失败",
                )
            return False
        return True

    # 检查安装包内插件与现有插件的版本关系
    # 返回值：True=安装成功；False=安装失败；None=用户取消重装（不算失败）
    # show_error=False 时校验失败不弹窗，由 import_plugin_list 统一汇总提示
    def check_version_and_install(self, show_error=True):
        # 先静态校验包完整性：坏包不得删除任何已安装内容
        if not self.validate_package(show_error=show_error):
            return False
        try:
            with open(os.path.join(self.plugin_path, 'manifest.json'), 'r', encoding='utf-8') as f:
                data = json.load(f)
                # print("开始读取已安装插件信息以检查版本...")
                plugin_version = data.get("version", None)
        except Exception :
            plugin_version = None  # 没有安装过或插件出错
            

        if plugin_version is None:
            print(f"\"{self.name}\" 为新插件，正在安装...", file=sys.stdout)
           
        elif parse_version(self.version) > parse_version(plugin_version):
            print(f"\"{self.name}\" 已安装版本较旧，正在安装新版本...", file=sys.stdout)
        
        elif parse_version(self.version) == parse_version(plugin_version):
            if sg.popup_yes_no(f"\"{self.name}\" 已安装版本与当前版本相同，是否重装？") == "Yes":
                print("正在重装插件...", file=sys.stdout)
            else:
                print("已取消安装", file=sys.stdout)
                return None

        else:
            if sg.popup_yes_no("已安装版本高于当前版本，确定要重装吗？\n" \
            f"插件名称: {self.name}\n" \
            f"已安装版本: {plugin_version}\n" \
            f"当前版本: {self.version}") == "Yes":
                print("正在重装插件...", file=sys.stdout)
            else:
                print("已取消安装", file=sys.stdout)
                return None

        return self.install()  # 返回真实安装结果

    # 计算磁盘文件的 CRC32，用于判断"覆盖前后内容是否真的不一样"
    @staticmethod
    def _file_crc32(path):
        crc = 0
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b""):
                crc = zlib.crc32(chunk, crc)
        return crc & 0xFFFFFFFF

    # 找出 zip 会覆盖掉的现有文件，只保留内容确有差异的
    def _collect_overwrites(self, zf):
        """返回 [(zip 内相对路径, 磁盘绝对路径)]。

        只读 ZipInfo 的 file_size / CRC，不读 zip 内容；大小不同直接判定为不同，
        大小相同再算磁盘文件 CRC32。内容一致的文件不备份——用户没改过的东西
        备份出来只会堆垃圾，也会让"已备份 N 个文件"的提示失真。
        """
        overwrites = []
        for info in zf.infolist():
            member = info.filename.replace("\\", "/")
            if not member or member.endswith("/") or info.is_dir():
                continue
            target = os.path.join(self.plugin_path, *member.split("/"))
            if not os.path.isfile(target):
                continue
            if (os.path.getsize(target) == info.file_size
                    and self._file_crc32(target) == info.CRC):
                continue
            overwrites.append((member, target))
        return overwrites

    # 把将被覆盖的旧文件复制到 cache/plugin_backup/<插件>/<时间戳>/
    def _backup_overwrites(self, overwrites):
        """备份完成后才允许调用方 rmtree；本方法抛异常即代表安装必须中止。

        备份失败时上游会直接返回，旧插件目录保持原样——宁可装不上，
        也不能出现"旧文件删了、新文件没解出来"的空窗。
        """
        plugin_id = os.path.basename(self.plugin_path)
        stamp = time.strftime("%Y%m%d_%H%M%S")
        root = get_path(PLUGIN_BACKUP_ROOT)
        backup_dir = os.path.join(root, plugin_id, stamp)
        index = 1
        while os.path.exists(backup_dir):
            backup_dir = os.path.join(root, plugin_id, f"{stamp}_{index}")
            index += 1
        for member, target in overwrites:
            dest = os.path.join(backup_dir, *member.split("/"))
            parent = os.path.dirname(dest)
            if parent:
                os.makedirs(parent, exist_ok=True)
            shutil.copy2(target, dest)
        self.backup_dir = backup_dir
        self.backed_up = [member for member, _ in overwrites]
        print(f"已备份 {len(overwrites)} 个将被覆盖的文件到: {backup_dir}", file=sys.stderr)
        return backup_dir

    # 安装插件，解压到 plugins 目录
    def install(self):
        """解压安装。顺序：成员路径校验 → 备份被覆盖文件 → 清理旧目录 → 解压。

        前三步任一失败都不会走到 rmtree，已安装插件保持可用。
        """
        self.backed_up = []
        self.backup_dir = None
        try:
            self.plugin_path = self._validate_install_path(self.plugin_path)
            with zipfile.ZipFile(self.zip_path, 'r', metadata_encoding='utf-8') as zf:
                # 先校验成员路径：坏包必须在动磁盘之前被拦下
                for member in zf.namelist():
                    normalized = member.replace('\\', '/')
                    if normalized.startswith('/') or '..' in normalized.split('/') or os.path.isabs(member):
                        raise ValueError(f"不安全路径: {member}")
                overwrites = self._collect_overwrites(zf)
                if overwrites:
                    self._backup_overwrites(overwrites)
                # 目标存在时清理旧插件；清理失败会进入 except 并返回 False
                if os.path.exists(self.plugin_path):
                    shutil.rmtree(self.plugin_path)
                # 将所有文件解压到 ./plugins/my_plugin/ 目录
                zf.extractall(path=self.plugin_path)
                print(f"成功安装: {self.name}")
        except Exception as e:
            print(f"安装插件出错: {e}", file=sys.stderr)
            hint = f"\n\n原有文件已备份到：\n{self.backup_dir}" if self.backup_dir else ""
            sg.popup_error(f"安装插件出错: {e}{hint}")
            return False
        return True

 
def import_plugin_list(zip_path_list: list):
    success_list = []
    failed_list = []  # 安装失败的文件路径列表
    skipped_list = []  # 用户取消重装的文件路径列表，不计为失败
    failed_reasons = {}  # 失败原因（仅包完整性校验失败时记录），供调用方汇总展示
    backups = {}  # 安装时覆盖了插件目录内已有文件的记录，供调用方统一提示
    for zip_path in zip_path_list:
        plugin_zip = PluginInstaller(zip_path)
        if not plugin_zip.load_zip_json():
            print("加载插件信息失败，安装中止", file=sys.stderr)
            failed_list.append(zip_path)
            continue
        # 单包失败的原因交给汇总提示，避免“校验失败”与“未导入”连弹两次
        install_result = plugin_zip.check_version_and_install(show_error=False)
        if install_result is True:
            success_list.append(zip_path)
            if plugin_zip.backup_dir:
                backups[zip_path] = {
                    "name": plugin_zip.name,
                    "dir": plugin_zip.backup_dir,
                    "files": list(plugin_zip.backed_up),
                }
        elif install_result is False:
            failed_list.append(zip_path)
            if plugin_zip.rejection_reason:
                failed_reasons[zip_path] = plugin_zip.rejection_reason
        else:
            skipped_list.append(zip_path)

    return {
        "success_list": success_list,
        "failed_files": failed_list,
        "failed_reasons": failed_reasons,
        "skipped_files": skipped_list,
        "backups": backups
    }
    

if __name__ == "__main__":
    # 示例用法
    import_plugin_list(sys.argv[1:])


