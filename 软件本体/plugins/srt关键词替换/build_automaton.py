import os, sys, json
from typing import Dict, List, Set
import ahocorasick
import pickle
from pathlib import Path
import time
from functools import wraps

# 默认配置
default_config = {"delete":{"profanity":["傻逼","傻波","卧槽","哎呦我草","我操","我草","我靠","我去","哦李现","what's up","what the fuck","我的妈","我的fuck","fuck","你他妈的","你他喵的","ntmd","你妈的","nmd","他妈的","他喵的","TMD","tmd","妈的","喵的","md","你妈","nm","他妈","他喵","tm","oh shit"],"others":["呃","huh","uh"]},"repeat":[{"word":"完了","enabled":True,"max_times":2,"interval":{"enabled":True,"min_consecutive":3,"separator":" "}},{"word":"哈","enabled":True,"max_times":3,"interval":{"enabled":False,"min_consecutive":3,"separator":" "}},{"word":"不行","enabled":True,"max_times":3,"interval":{"enabled":True,"min_consecutive":3,"separator":" "}},{"word":"我知道","enabled":True,"max_times":2,"interval":{"enabled":True,"min_consecutive":2,"separator":" "}},{"word":"别","enabled":True,"max_times":3,"interval":{"enabled":False,"min_consecutive":3,"separator":" "}}],"replace":[{"word":"我的世界","type":"group","enabled":True,"items":[{"word":"MCUP名字","type":"group","enabled":True,"items":[{"word":"卡慕","enabled":True,"source":["卡布","卡莫","卡木","卡不","卡姆","Kamu","karm","come","卡慕 on","扛我","Kobe","carm","Kame","蛤蟆","Carmore","Carmel","考不"]},{"word":"卡慕SaMa","enabled":True,"source":["卡慕sama","卡慕Sama","卡慕沙发","卡慕沙吧","砍不上吗","卡慕萨巴","卡慕沙吗","卡穆萨玛"]},{"word":"谭俊峰","enabled":True,"source":["传进风"]},{"word":"米洛","enabled":True,"source":["米诺","米罗","笔落","余姚","比洛","米拉","米露","米勒","明总"]},{"word":"萝卜吃米洛","enabled":True,"source":["萝卜吃鱼了","罗旭罗","罗旭"]},{"word":"宁宇航","enabled":True,"source":["李宇航"]},{"word":"碧月狐","enabled":True,"source":["碧月湖","闭月狐","毕业胡","b月湖","b月会","B2胡","月壶","夜壶","壁虎","鳖胡","别胡","憋活","别活"]},{"word":"曹某","enabled":True,"source":["Tom"]},{"word":"曹小龙","enabled":True,"source":["草药龙","张小龙","操小龙","超小龙","曹勇","沙拉龙","条龙"]},{"word":"qiqi","enabled":True,"source":["KIKI","KI KI","KKI","QIQI","QI QI","KIQI"]},{"word":"Q3","enabled":True,"source":["q3"]},{"word":"贺子鹏","enabled":True,"source":["蔡子鹏","鹤头","赫德王","赫兹峰"]},{"word":"药儿","enabled":True,"source":["幺儿"]},{"word":"流赫","enabled":True,"source":["流贺","刘贺","刘赫","刘河","刘恒"]},{"word":"死睿","enabled":True,"source":["sweet","Siri","THREE"]},{"word":"烦华","enabled":True,"source":["芳芳"]},{"word":"鸽一品","enabled":True,"source":["葛一平","GEP","隔一天","割一瓢"]},{"word":"幕川北","enabled":True,"source":["木川北","莫川北"]}]},{"word":"操作","type":"group","enabled":True,"items":[{"word":"控距","enabled":True,"source":["控狙"]},{"word":"TP","enabled":True,"source":["TV"]},{"word":"跳劈","enabled":True,"source":["跳p"]}]},{"word":"游戏内事物","type":"group","enabled":True,"items":[{"word":"掉落物","enabled":True,"source":["掉了物"]},{"word":"附魔金","enabled":True,"source":["复活金"]},{"word":"蘑菇牛","enabled":True,"source":["蘑菇流"]},{"word":"猪灵","enabled":True,"source":["朱玲"]},{"word":"坚守者","enabled":True,"source":["接受者","监视者"]},{"word":"烈焰人","enabled":True,"source":["猎人"]},{"word":"末影人","enabled":True,"source":["梦人"]},{"word":"末影龙","enabled":True,"source":["莫云龙"]},{"word":"龙息","enabled":True,"source":["浓稀"]},{"word":"细雪","enabled":True,"source":["气血"]},{"word":"煤炭","enabled":True,"source":["没炭"]},{"word":"岩浆湖","enabled":True,"source":["人江湖"]},{"word":"岩浆","enabled":True,"source":["岩尖"]},{"word":"刷怪笼","enabled":True,"source":["创二龙"]},{"word":"猪灵堡垒","enabled":True,"source":["珠林堡垒","朱宁堡垒"]},{"word":"末影水晶","enabled":True,"source":["魔女水晶"]},{"word":"主世界","enabled":True,"source":["主界"]}]}]},{"word":"口语","type":"group","enabled":True,"items":[{"word":"OK","enabled":True,"source":["okay"]},{"word":"厉害","enabled":True,"source":["牛逼"]},{"word":"懂你意思","enabled":True,"source":["don't listen"]},{"word":"好枪","enabled":True,"source":["烤箱"]}]},{"word":"误识别英语","type":"group","enabled":True,"items":[{"word":"这","enabled":True,"source":["this"]}]},{"word":"三角洲","type":"group","enabled":True,"items":[{"word":"地点","type":"group","enabled":True,"items":[{"word":"巴克什","enabled":True,"source":["8个10","挖个10","BUG10","巴克斯"]},{"word":"普坝","enabled":True,"source":["普巴"]},{"word":"大坝","enabled":True,"source":["大巴"]},{"word":"坝顶","enabled":True,"source":["霸顶"]},{"word":"蓝汀","enabled":True,"source":["蓝厅"]},{"word":"水泥厂","enabled":True,"source":["水泥铲"]},{"word":"牢区","enabled":True,"source":["老区"]},{"word":"西楼","enabled":True,"source":["西路"]},{"word":"蓝数","enabled":True,"source":["蓝树"]},{"word":"蓝核","enabled":True,"source":["蓝盒"]}]},{"word":"干员","type":"group","enabled":True,"items":[{"word":"麦晓雯","enabled":True,"source":["麦小文"]},{"word":"威龙","enabled":True,"source":["维鲁"]},{"word":"蜂医","enabled":True,"source":["风衣"]},{"word":"乌鲁鲁","enabled":True,"source":["乌噜噜","咕噜噜"]}]},{"word":"操作","type":"group","enabled":True,"items":[{"word":"报点","enabled":True,"source":["爆点"]},{"word":"破译","enabled":True,"source":["破夜"]},{"word":"卡战备","enabled":True,"source":["卡站位"]},{"word":"护航","enabled":True,"source":["护盘"]},{"word":"精标","enabled":True,"source":["金标"]}]},{"word":"物品","type":"group","enabled":True,"items":[{"word":"武器","type":"group","enabled":True,"items":[{"word":"AUG","enabled":True,"source":["AOG"]}]},{"word":"装备","type":"group","enabled":True,"items":[{"word":"弹挂","enabled":True,"source":["半挂"]},{"word":"六套","enabled":True,"source":["刘涛","6炮"]}]},{"word":"物资","type":"group","enabled":True,"items":[{"word":"本地特色首饰","enabled":True,"source":["本地特色手势"]},{"word":"希望之钥","enabled":True,"source":["希望之药"]}]}]}]}]}
logs = "记录日志"


def timer(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        end = time.perf_counter()
        elapsed = (end - start) * 1000  # 毫秒
        print(f"[TIMER] {func.__name__} 耗时: {elapsed:.2f} ms")
        return result
    return wrapper


# 获取资源的绝对路径, 打包后默认返回只读目录, 容开发环境和 PyInstaller 打包后
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

# 读取并处理json配置
class SubtitleRuleProcessor:
    def __init__(self):
        self.json_path = get_path("subtitle_rules.json", use_program_dir=True)
        self.cache_path = get_path("subtitle_rules.pkl", use_program_dir=True)
        self.default_config = default_config
        self.raw_config = None
        self.all_keywords: List[str] = []
        self.delete_words: List[str] = []
        self.profanity_set: Set[str] = set()
        self.repeat_rule_map: Dict[str, dict] = {}
        self.replace_word_to_sources: Dict[str, List[str]] = {}
        self.replace_source_to_word: Dict[str, str] = {}
        self.automaton = None
        self._profanity_count = 0

    def _get_json(self):
        if self.raw_config:
            return
        # 先尝试从 EXE 目录读取
        if os.path.exists(self.json_path):
            try:
                with open(self.json_path, 'r', encoding='utf-8') as f:
                    self.raw_config = json.load(f)
                return
            except Exception as e:
                print(f"读取配置文件失败: {e}", file=sys.stderr)
        # 若不存在或读取失败，尝试从资源目录复制默认配置
        default_src = get_path("default_subtitle_rules.json", use_program_dir=False)
        if os.path.exists(default_src):
            import shutil
            try:
                shutil.copy2(default_src, self.json_path)
                print(f"已从资源目录复制默认配置到 {self.json_path}", file=sys.stderr)
                with open(self.json_path, 'r', encoding='utf-8') as f:
                    self.raw_config = json.load(f)
                return
            except Exception as e:
                print(f"复制默认配置失败: {e}", file=sys.stderr)
        # 最后使用内嵌的默认配置（硬编码）
        self.raw_config = self.default_config
        # 并尝试写入到 EXE 目录
        try:
            with open(self.json_path, 'w', encoding='utf-8') as f:
                json.dump(self.default_config, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"写入默认配置失败: {e}", file=sys.stderr)

    def _parse_delete_config(self):
        """解析 delete 部分，构建删除词列表和敏感词集合"""
        delete_cfg = self.raw_config.get("delete", {})
        for category, words in delete_cfg.items():
            self.delete_words.extend(words)   # 列表用 extend
            if category == "profanity":
                self.profanity_set.update(words)   # set 用 update
        # 去重
        self.delete_words = list(set(self.delete_words))

    def reset_profanity_count(self):
        """重置当前敏感词计数器（处理新文件前调用）"""
        self._profanity_count = 0

    def get_profanity_count(self) -> int:
        """获取当前文件累积的敏感词删除次数"""
        return self._profanity_count

    def _parse_repeat_config(self):
        """解析 repeat 部分（暂未实现，预留）"""
        pass

    def _process_node(self, node: dict):
        """递归处理 replace 节点，构建映射表"""
        if not node.get("enabled", True):
            return
        match node.get("type", "correction"):
            case "group":
                for child in node.get("items", []):
                    self._process_node(child)
            case "correction":
                correct = node["word"]
                sources = node.get("source", [])
                self.replace_word_to_sources[correct] = sources
                for src in sources:
                    self.replace_source_to_word[src] = correct
            case "regex":
                # 未来处理正则
                pass
            case _:
                pass

    def _parse_replace_config(self):
        """解析 replace 部分，从顶层数组开始递归"""
        for group_node in self.raw_config.get("replace", []):
            self._process_node(group_node)

    def _build_all_keywords(self):
        """收集所有需要匹配的关键词（用于自动机）"""
        keywords = set()
        # delete 词
        keywords.update(self.delete_words)
        # repeat 词（键就是重复词本身）
        keywords.update(self.repeat_rule_map.keys())
        # replace 源词
        keywords.update(self.replace_source_to_word.keys())
        self.all_keywords = list(keywords)

    def _build_automaton(self):
        """构建 Aho-Corasick 自动机，包含 delete 和 replace 的所有关键词"""
        automaton = ahocorasick.Automaton()
        
        # 添加 delete 词
        for word in self.delete_words:
            automaton.add_word(word, ("delete", word))   # 动作：删除
        # 添加 replace 源词
        for src, correct in self.replace_source_to_word.items():
            automaton.add_word(src, ("replace", src, correct))   # 动作：替换为 correct
        
        automaton.make_automaton()
        self.automaton = automaton

    def _resolve_overlaps(self, matches):
        """
        输入匹配列表，每个元素为 (start, end, action)
        返回过滤后不重叠的匹配列表（保留长词优先）
        """
        if not matches:
            return []
        # 按开始升序，结束降序（使长词排在前面）
        matches.sort(key=lambda x: (x[0], -x[1]))
        resolved = []
        last_end = -1
        for start, end, action in matches:
            if start < last_end:   # 重叠或包含，跳过
                continue
            resolved.append((start, end, action))
            last_end = end
        return resolved

    def _apply_operations(self, text: str, matches: list) -> str:
        """根据匹配列表，从后往前删除或替换文本，并统计敏感词删除次数"""
        if not matches:
            return text
        # 按结束位置降序排序（从右向左处理）
        matches_sorted = sorted(matches, key=lambda x: -x[1])
        chars = list(text)
        for start, end, action in matches_sorted:
            if action[0] == "delete":
                # 如果删除的词属于敏感词集，增加计数
                deleted_word = action[1]
                if deleted_word in self.profanity_set:
                    self._profanity_count += 1
                del chars[start:end]
            elif action[0] == "replace":
                correct = action[2]
                chars[start:end] = list(correct)
        return "".join(chars)

    def process_text(self, text: str) -> str:
        if self.automaton is None:
            raise RuntimeError("请先调用 load_rules() 加载规则")
        matches = []
        for end, value in self.automaton.iter(text):
            # 根据 value 的长度和第一个元素判断类型
            if isinstance(value, tuple) and len(value) >= 2:
                if value[0] == "delete":
                    word = value[1]
                    start = end - len(word) + 1
                    matches.append((start, end+1, ("delete", word)))
                elif value[0] == "replace" and len(value) >= 3:
                    src, correct = value[1], value[2]
                    start = end - len(src) + 1
                    matches.append((start, end+1, ("replace", src, correct)))
            else:
                # 异常情况，打印警告并跳过
                print(f"警告：未知的自动机值格式 {value}", file=sys.stderr)
                global logs
                logs += f"警告：未知的自动机值格式 {value}"
        matches = self._resolve_overlaps(matches)
        return self._apply_operations(text, matches)
    
    def _is_cache_valid(self) -> bool:
        """检查缓存文件是否比 JSON 配置文件新"""
        if not os.path.exists(self.cache_path):
            return False
        if not os.path.exists(self.json_path):
            return False
        json_mtime = os.path.getmtime(self.json_path)
        cache_mtime = os.path.getmtime(self.cache_path)
        return cache_mtime > json_mtime
    
    def _load_from_cache(self) -> bool:
        """尝试从缓存文件加载自动机及相关数据"""
        try:
            with open(self.cache_path, 'rb') as f:
                data = pickle.load(f)
            # 恢复所有必要属性
            self.automaton = data['automaton']
            self.delete_words = data['delete_words']
            self.profanity_set = data['profanity_set']
            self.replace_word_to_sources = data['replace_word_to_sources']
            self.replace_source_to_word = data['replace_source_to_word']
            self.all_keywords = data['all_keywords']
            self.raw_config = data.get('raw_config')  # 可选
            return True
        except Exception as e:
            print(f"加载缓存失败: {e}", file=sys.stderr)
            return False
    
    def _save_to_cache(self):
        """将当前自动机及相关数据保存到缓存文件"""
        data = {
            'automaton': self.automaton,
            'delete_words': self.delete_words,
            'profanity_set': self.profanity_set,
            'replace_word_to_sources': self.replace_word_to_sources,
            'replace_source_to_word': self.replace_source_to_word,
            'all_keywords': self.all_keywords,
            'raw_config': self.raw_config,
        }
        try:
            with open(self.cache_path, 'wb') as f:
                pickle.dump(data, f, protocol=pickle.HIGHEST_PROTOCOL)
        except Exception as e:
            print(f"保存缓存失败: {e}", file=sys.stderr)

    def load_rules(self, force_rebuild: bool = False):
        """统一加载规则（外部调用入口）"""
        if force_rebuild or not self._is_cache_valid():
            print("构建自动机并缓存...", file=sys.stderr)
            self._get_json()
            self._parse_delete_config()
            self._parse_replace_config()
            self._build_all_keywords()
            self._build_automaton()
            self._save_to_cache()
        else:
            if not self._load_from_cache():
                # 缓存加载失败，回退到构建
                print("缓存无效，重新构建...", file=sys.stderr)
                self.load_rules(force_rebuild=True)
    
    def rebuild_cache(self):
        """手动强制重建缓存（配置修改后调用）"""
        self.load_rules(force_rebuild=True)
        


def test():
    test_text = """测试测试傻逼卡慕米诺米诺傻逼"""
    processor = SubtitleRuleProcessor()
    processor.load_rules()
    def process_srt_file(original_text):
        processor.reset_profanity_count()
        cleaned_text = processor.process_text(original_text)
        return cleaned_text, processor.get_profanity_count()
    
    cleaned_text, profanity_count = process_srt_file(test_text)
    print(f"cleaned_text: 1\n" \
    f"profanity_count: {profanity_count}")


if __name__ == "__main__":
    test()





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