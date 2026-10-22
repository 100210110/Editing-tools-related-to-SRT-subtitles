import zipfile
import json
import os
import re
import sys
import shutil
import PySimpleGUI as sg
from packaging.version import parse as parse_version


# 插件目录名白名单：字母、数字、下划线、连字符、中文
PLUGIN_ID_PATTERN = re.compile(r'^[\w\u4e00-\u9fff-]+$')


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
    
    # 检查安装包内插件与现有插件的版本关系
    # 返回值：True=安装成功；False=安装失败；None=用户取消重装（不算失败）
    def check_version_and_install(self):
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

    # 安装插件，解压到 plugins 目录
    def install(self):
        try:
            self.plugin_path = self._validate_install_path(self.plugin_path)
            # 目标存在时清理旧插件；清理失败会进入 except 并返回 False
            if os.path.exists(self.plugin_path):
                shutil.rmtree(self.plugin_path)
            with zipfile.ZipFile(self.zip_path, 'r', metadata_encoding='utf-8') as zf:
                for member in zf.namelist():
                    normalized = member.replace('\\', '/')
                    if normalized.startswith('/') or '..' in normalized.split('/') or os.path.isabs(member):
                        raise ValueError(f"不安全路径: {member}")
                # 将所有文件解压到 ./plugins/my_plugin/ 目录
                zf.extractall(path=self.plugin_path)
                print(f"成功安装: {self.name}")
        except Exception as e:
            print(f"安装插件出错: {e}", file=sys.stderr)
            sg.popup_error(f"安装插件出错: {e}")
            return False
        return True

 
def test_plugins_list(FILE_LIST=[]):
    for input_zip_path in FILE_LIST:
        plugin_zip = PluginInstaller(input_zip_path)
        if plugin_zip.load_zip_json():
            plugin_zip.test()
    if sg.popup_ok_cancel("测试完成，是否继续安装？", title="测试结果") == "OK":
        plugin_zip.check_version_and_install()
    else:
        print("已取消安装", file=sys.stdout)


def import_plugin_list(zip_path_list: list):
    success_list = []
    failed_list = []  # 安装失败的文件路径列表
    skipped_list = []  # 用户取消重装的文件路径列表，不计为失败
    for zip_path in zip_path_list:
        plugin_zip = PluginInstaller(zip_path)
        if not plugin_zip.load_zip_json():
            print("加载插件信息失败，安装中止", file=sys.stderr)
            failed_list.append(zip_path)
            continue
        install_result = plugin_zip.check_version_and_install()
        if install_result is True:
            success_list.append(zip_path)
        elif install_result is False:
            failed_list.append(zip_path)
        else:
            skipped_list.append(zip_path)

    return {
        "success_list": success_list,
        "failed_files": failed_list,
        "skipped_files": skipped_list
    }
    

if __name__ == "__main__":
    # 示例用法
    import_plugin_list(sys.argv[1:])


