import sys
import json
import os
import re
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTreeWidget, QTreeWidgetItem, QPushButton, QFileDialog, QMessageBox,
    QMenu, QInputDialog, QLineEdit, QDialog, QFormLayout, QSpinBox,
    QCheckBox, QGroupBox, QDialogButtonBox, QListWidget, QHeaderView
)
from PyQt5.QtCore import Qt
from common import get_path
import logging

logger = logging.getLogger('str_editor_plugin')


# ---------- 对话框类 ----------
class RepeatRuleDialog(QDialog):
    def __init__(self, rule_data, parent=None):
        super().__init__(parent)
        self.rule_data = rule_data.copy()
        self.setWindowTitle("编辑重复规则")
        self.setModal(True)
        layout = QFormLayout(self)

        self.word_edit = QLineEdit(self.rule_data.get("word", ""))
        self.enabled_check = QCheckBox()
        self.enabled_check.setChecked(self.rule_data.get("enabled", True))
        self.max_times_spin = QSpinBox()
        self.max_times_spin.setRange(1, 99)
        self.max_times_spin.setValue(self.rule_data.get("max_times", 2))

        interval = self.rule_data.get("interval", {})
        self.interval_enabled = QCheckBox()
        self.interval_enabled.setChecked(interval.get("enabled", False))
        self.min_consecutive_spin = QSpinBox()
        self.min_consecutive_spin.setRange(2, 10)
        self.min_consecutive_spin.setValue(interval.get("min_consecutive", 3))
        self.separator_edit = QLineEdit(interval.get("separator", " "))

        layout.addRow("单词:", self.word_edit)
        layout.addRow("启用:", self.enabled_check)
        layout.addRow("最大重复次数:", self.max_times_spin)
        layout.addRow("间隔规则启用:", self.interval_enabled)
        layout.addRow("最小连续次数:", self.min_consecutive_spin)
        layout.addRow("分隔符:", self.separator_edit)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def get_data(self):
        return {
            "word": self.word_edit.text(),
            "enabled": self.enabled_check.isChecked(),
            "max_times": self.max_times_spin.value(),
            "interval": {
                "enabled": self.interval_enabled.isChecked(),
                "min_consecutive": self.min_consecutive_spin.value(),
                "separator": self.separator_edit.text()
            }
        }

class ReplaceItemDialog(QDialog):
    def __init__(self, item_data, parent=None):
        super().__init__(parent)
        self.item_data = item_data.copy()
        self.setWindowTitle("编辑替换项")
        self.setModal(True)
        layout = QVBoxLayout(self)

        form = QFormLayout()
        self.word_edit = QLineEdit(self.item_data.get("word", ""))
        self.enabled_check = QCheckBox()
        self.enabled_check.setChecked(self.item_data.get("enabled", True))
        form.addRow("目标词:", self.word_edit)
        form.addRow("启用:", self.enabled_check)
        layout.addLayout(form)

        source_group = QGroupBox("源词列表 (识别为当前词)")
        source_layout = QVBoxLayout(source_group)
        self.source_list = QListWidget()
        self.refresh_source_list()
        source_layout.addWidget(self.source_list)
        btn_layout = QHBoxLayout()
        add_btn = QPushButton("添加")
        add_btn.clicked.connect(self.add_source)
        remove_btn = QPushButton("删除")
        remove_btn.clicked.connect(self.remove_source)
        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(remove_btn)
        source_layout.addLayout(btn_layout)
        layout.addWidget(source_group)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def refresh_source_list(self):
        self.source_list.clear()
        sources = self.item_data.get("source", [])
        for s in sources:
            self.source_list.addItem(s)

    def add_source(self):
        text, ok = QInputDialog.getText(self, "添加源词", "输入源词:")
        if ok and text.strip():
            existing = [self.source_list.item(i).text() for i in range(self.source_list.count())]
            if text.strip() in existing:
                QMessageBox.warning(self, "重复", f"源词 '{text.strip()}' 已存在，不能重复添加。")
                return
            self.source_list.addItem(text.strip())

    def remove_source(self):
        cur = self.source_list.currentRow()
        if cur >= 0:
            self.source_list.takeItem(cur)

    def get_data(self):
        sources = [self.source_list.item(i).text() for i in range(self.source_list.count())]
        return {
            "word": self.word_edit.text(),
            "enabled": self.enabled_check.isChecked(),
            "source": sources
        }

class ReplaceGroupDialog(QDialog):
    def __init__(self, group_data, parent=None):
        super().__init__(parent)
        self.group_data = group_data.copy()
        self.setWindowTitle("编辑分组")
        self.setModal(True)
        layout = QFormLayout(self)
        self.word_edit = QLineEdit(self.group_data.get("word", ""))
        self.enabled_check = QCheckBox()
        self.enabled_check.setChecked(self.group_data.get("enabled", True))
        layout.addRow("分组名:", self.word_edit)
        layout.addRow("启用:", self.enabled_check)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def get_data(self):
        return {
            "word": self.word_edit.text(),
            "type": "group",
            "enabled": self.enabled_check.isChecked(),
            "items": self.group_data.get("items", [])
        }

# ---------- 主窗口 ----------
class SubtitleEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.current_file = None
        self.data = {
            "delete": {"profanity": [], "others": []},
            "repeat": [],
            "replace": []
        }
        self.load_default_and_set_working_file()
        self.init_ui()

    # ---------- 文件操作 ----------
    def load_default_and_set_working_file(self):
        
        default_path = get_path("default_subtitle_rules.json", use_program_dir=False)
        working_path = os.path.join(get_path(use_program_dir=True), "subtitle_rules.json")

        if os.path.exists(default_path):
            try:
                with open(default_path, 'r', encoding='utf-8') as f:
                    self.data = json.load(f)
            except Exception as e:
                QMessageBox.warning(self, "警告", f"加载默认文件失败：{str(e)}\n将使用空数据。")
                self.data = {"delete": {"profanity": [], "others": []}, "repeat": [], "replace": []}
        else:
            QMessageBox.information(self, "提示", f"未找到 default_subtitle_rules.json，将使用空数据。\n失败路径: {default_path}")

        self.current_file = working_path
        if os.path.exists(working_path):
            try:
                with open(working_path, 'r', encoding='utf-8') as f:
                    self.data = json.load(f)
            except Exception as e:
                QMessageBox.warning(self, "警告", f"加载工作文件失败：{str(e)}，将使用默认模板。")

    def save_to_file(self, filename):
        try:
            json_str = json.dumps(self.data, ensure_ascii=False, indent=4)
            json_str = self._compact_leaf_nodes(json_str)
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(json_str)
            QMessageBox.information(self, "成功", f"已保存至 {filename}")
            return True
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存失败: {str(e)}")
            return False

    def _compact_leaf_nodes(self, json_str):
        pattern = r'(\{[^{}]*"source"\s*:\s*\[[^\]]*\][^{}]*\})'
        def compress(match):
            block = match.group(0)
            compact = re.sub(r'\s+', ' ', block).strip()
            compact = compact.replace('[ ', '[').replace(' ]', ']')
            compact = re.sub(r'",\s*"', '", "', compact)
            return compact
        return re.sub(pattern, compress, json_str, flags=re.DOTALL)

    def new_file(self):
        self.data = {"delete": {"profanity": [], "others": []}, "repeat": [], "replace": []}
        self.current_file = os.path.join(os.path.dirname(__file__), "subtitle_rules.json")
        self.build_tree()
        QMessageBox.information(self, "新建", "已清空所有规则，保存将写入 subtitle_rules.json")

    def open_file(self):
        filename, _ = QFileDialog.getOpenFileName(self, "打开规则文件", "", "JSON Files (*.json)")
        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    self.data = json.load(f)
                self.current_file = filename
                self.build_tree()
                QMessageBox.information(self, "成功", f"已加载 {filename}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"加载失败: {str(e)}")

    def save_file(self):
        if self.current_file:
            self.save_to_file(self.current_file)
        else:
            self.save_as_file()

    def save_as_file(self):
        filename, _ = QFileDialog.getSaveFileName(self, "保存规则文件", "", "JSON Files (*.json)")
        if filename:
            if self.save_to_file(filename):
                self.current_file = filename

    # ---------- UI 初始化 ----------
    def init_ui(self):
        self.setWindowTitle("字幕规则编辑器")
        self.resize(900, 700)

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)

        toolbar = QHBoxLayout()
        self.new_btn = QPushButton("新建")
        self.open_btn = QPushButton("打开")
        self.save_btn = QPushButton("保存")
        self.save_as_btn = QPushButton("另存为")
        toolbar.addWidget(self.new_btn)
        toolbar.addWidget(self.open_btn)
        toolbar.addWidget(self.save_btn)
        toolbar.addWidget(self.save_as_btn)
        toolbar.addStretch()
        main_layout.addLayout(toolbar)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["名称", "附加信息"])
        self.tree.setAlternatingRowColors(True)
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.on_context_menu)
        main_layout.addWidget(self.tree)

        self.new_btn.clicked.connect(self.new_file)
        self.open_btn.clicked.connect(self.open_file)
        self.save_btn.clicked.connect(self.save_file)
        self.save_as_btn.clicked.connect(self.save_as_file)

        self.build_tree()

    # ---------- 树形构建 ----------
    def build_tree(self):
        self.tree.clear()
        delete_root = QTreeWidgetItem(self.tree)
        delete_root.setText(0, "Delete")
        self.build_delete_tree(delete_root)

        repeat_root = QTreeWidgetItem(self.tree)
        repeat_root.setText(0, "Repeat")
        self.build_repeat_tree(repeat_root)

        replace_root = QTreeWidgetItem(self.tree)
        replace_root.setText(0, "Replace")
        self.build_replace_tree(replace_root)

        header = self.tree.header()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)

        self.tree.collapseAll()

    def build_delete_tree(self, parent_item):
        profanity_item = QTreeWidgetItem(parent_item)
        profanity_item.setText(0, "profanity")
        for word in self.data["delete"]["profanity"]:
            child = QTreeWidgetItem(profanity_item)
            child.setText(0, word)
            child.setData(0, Qt.UserRole, word)
        others_item = QTreeWidgetItem(parent_item)
        others_item.setText(0, "others")
        for word in self.data["delete"]["others"]:
            child = QTreeWidgetItem(others_item)
            child.setText(0, word)
            child.setData(0, Qt.UserRole, word)

    def build_repeat_tree(self, parent_item):
        for rule in self.data["repeat"]:
            word = rule.get("word", "")
            enabled = rule.get("enabled", True)
            status = "✓" if enabled else "✗"
            rule_item = QTreeWidgetItem(parent_item)
            rule_item.setText(0, f"{word} [{status}]")
            rule_item.setData(0, Qt.UserRole, rule)
            detail1 = QTreeWidgetItem(rule_item)
            detail1.setText(0, f"max_times: {rule.get('max_times')}")
            interval = rule.get("interval", {})
            detail2 = QTreeWidgetItem(rule_item)
            detail2.setText(0, f"interval: enabled={interval.get('enabled')}, min_consecutive={interval.get('min_consecutive')}, separator='{interval.get('separator')}'")

    def build_replace_tree(self, parent_item, items=None):
        if items is None:
            items = self.data["replace"]
        for node in items:
            word = node.get("word", "?")
            typ = node.get("type", "item")
            enabled = node.get("enabled", True)
            status = "✓" if enabled else "✗"
            node_item = QTreeWidgetItem(parent_item)
            node_item.setText(0, f"[{typ}] {word} {status}")
            node_item.setData(0, Qt.UserRole, node)
            if typ == "group" and "items" in node:
                self.build_replace_tree(node_item, node["items"])
            elif "source" in node:
                src_list = node.get("source", [])
                src_text = ", ".join(src_list)
                node_item.setText(1, src_text)

    # ---------- 展开状态保存与恢复 ----------
    def get_expanded_paths(self, parent_item=None):
        expanded = []
        if parent_item is None:
            for i in range(self.tree.topLevelItemCount()):
                if self.tree.topLevelItem(i).text(0) == "Replace":
                    parent_item = self.tree.topLevelItem(i)
                    break
        if parent_item:
            self._collect_expanded_paths(parent_item, "", expanded)
        return expanded

    def _collect_expanded_paths(self, item, path, expanded_list):
        current_path = path + "/" + item.text(0) if path else item.text(0)
        if item.isExpanded():
            expanded_list.append(current_path)
        for i in range(item.childCount()):
            self._collect_expanded_paths(item.child(i), current_path, expanded_list)

    def restore_expanded_paths(self, expanded_paths):
        replace_root = None
        for i in range(self.tree.topLevelItemCount()):
            if self.tree.topLevelItem(i).text(0) == "Replace":
                replace_root = self.tree.topLevelItem(i)
                break
        if replace_root:
            self._restore_paths(replace_root, "", expanded_paths)

    def _restore_paths(self, item, current_path, expanded_paths):
        full_path = current_path + "/" + item.text(0) if current_path else item.text(0)
        if full_path in expanded_paths:
            item.setExpanded(True)
        for i in range(item.childCount()):
            self._restore_paths(item.child(i), full_path, expanded_paths)

    # ---------- 分类刷新 ----------
    def refresh_delete_tree(self):
        top = None
        for i in range(self.tree.topLevelItemCount()):
            if self.tree.topLevelItem(i).text(0) == "Delete":
                top = self.tree.topLevelItem(i)
                break
        if top:
            top.takeChildren()
            self.build_delete_tree(top)
            top.setExpanded(True)

    def refresh_repeat_tree(self):
        logger.info("[配置json模块] 进入")
        top = None
        for i in range(self.tree.topLevelItemCount()):
            if self.tree.topLevelItem(i).text(0) == "Repeat":
                top = self.tree.topLevelItem(i)
                break
        if top:
            logger.info("[配置json模块] 找到 Repeat 根节点，开始重建")
            top.takeChildren()
            self.build_repeat_tree(top)
            top.setExpanded(True)
            self.tree.viewport().update()
            logger.info("[配置json模块] 重建完成")
        else:
            logger.info("[配置json模块] 未找到 Repeat 根节点")

    def refresh_replace_tree(self, preserve_expanded=True):
        logger.info(f"[配置json模块] 进入, preserve_expanded={preserve_expanded}")
        expanded_paths = self.get_expanded_paths() if preserve_expanded else []
        logger.info(f"[配置json模块] 保存的展开路径: {expanded_paths}")
        top = None
        for i in range(self.tree.topLevelItemCount()):
            if self.tree.topLevelItem(i).text(0) == "Replace":
                top = self.tree.topLevelItem(i)
                break
        if top:
            logger.info("[配置json模块] 找到 Replace 根节点，开始重建")
            top.takeChildren()
            self.build_replace_tree(top)
            if preserve_expanded:
                logger.info("[配置json模块] 恢复展开路径")
                self.restore_expanded_paths(expanded_paths)
            top.setExpanded(True)
            logger.info("[配置json模块] 重建完成")
        else:
            logger.info("[配置json模块] 未找到 Replace 根节点")

    # ---------- 辅助方法 ----------
    def _get_path_from_item(self, item):
        """获取从 Replace 根节点到当前节点的 word 列表（不重复，顺序正确）"""
        path = []
        cur = item
        # 向上收集所有祖先节点（包括当前节点）
        ancestors = []
        while cur and cur.text(0) != "Replace":
            ancestors.append(cur)
            cur = cur.parent()
        # 反转得到从顶层到当前节点
        ancestors.reverse()
        # 提取每个节点的 word
        for node in ancestors:
            text = node.text(0)
            # 去掉末尾的状态符号
            if text.endswith(' ✓') or text.endswith(' ✗'):
                no_status = text[:-2]
            else:
                no_status = text
            # 去掉开头的类型标记
            if no_status.startswith("[group] "):
                word = no_status[8:]
            elif no_status.startswith("[item] "):
                word = no_status[7:]
            else:
                word = no_status
            path.append(word)
        return path

    def _update_data_by_path(self, path, new_word=None, new_enabled=None, new_source=None):
        def find_and_update(data_list, path_parts):
            if not path_parts:
                return False
            for d in data_list:
                if d.get("word") == path_parts[0]:
                    if len(path_parts) == 1:
                        if new_word is not None:
                            d["word"] = new_word
                        if new_enabled is not None:
                            d["enabled"] = new_enabled
                        if new_source is not None:
                            d["source"] = new_source
                        return True
                    elif "items" in d:
                        return find_and_update(d["items"], path_parts[1:])
            return False
        return find_and_update(self.data["replace"], path)

    # ---------- Delete 操作 ----------
    def add_delete_keyword(self, category):
        text, ok = QInputDialog.getText(self, "添加关键词", f"输入要添加到 {category} 的关键词:")
        if ok and text.strip():
            if text.strip() in self.data["delete"][category]:
                QMessageBox.warning(self, "重复", f"关键词 '{text.strip()}' 已存在，不能重复添加。")
                return
            self.data["delete"][category].append(text.strip())
            self.refresh_delete_tree()

    def edit_delete_keyword(self, item, category):
        old_word = item.text(0)
        new_word, ok = QInputDialog.getText(self, "编辑关键词", "修改关键词:", text=old_word)
        if ok and new_word.strip():
            if new_word.strip() != old_word and new_word.strip() in self.data["delete"][category]:
                QMessageBox.warning(self, "重复", f"关键词 '{new_word.strip()}' 已存在，不能重复。")
                return
            idx = self.data["delete"][category].index(old_word)
            self.data["delete"][category][idx] = new_word.strip()
            self.refresh_delete_tree()

    def delete_delete_keyword(self, item, category):
        word = item.text(0)
        self.data["delete"][category].remove(word)
        self.refresh_delete_tree()

    # ---------- Repeat 操作 ----------
    def add_repeat_rule(self):
        default = {"word": "新规则", "enabled": True, "max_times": 2,
                   "interval": {"enabled": False, "min_consecutive": 3, "separator": " "}}
        dialog = RepeatRuleDialog(default, self)
        if dialog.exec_() == QDialog.Accepted:
            self.data["repeat"].append(dialog.get_data())
            self.refresh_repeat_tree()

    def edit_repeat_rule(self, item):
        rule_data = item.data(0, Qt.UserRole)
        idx = self.data["repeat"].index(rule_data)
        dialog = RepeatRuleDialog(rule_data, self)
        if dialog.exec_() == QDialog.Accepted:
            self.data["repeat"][idx] = dialog.get_data()
            self.refresh_repeat_tree()

    def delete_repeat_rule(self, item):
        rule_data = item.data(0, Qt.UserRole)
        self.data["repeat"].remove(rule_data)
        self.refresh_repeat_tree()

    def toggle_repeat_rule(self, item):
        logger.info("[toggle_repeat_rule] 进入")
        text = item.text(0)
        if text.endswith(" [✓]") or text.endswith(" [✗]"):
            rule_word = text[:-4]
        else:
            rule_word = text
        logger.info(f"[toggle_repeat_rule] 规则名称: {rule_word}")
        found = False
        for rule in self.data["repeat"]:
            if rule.get("word") == rule_word:
                old = rule.get("enabled", True)
                new = not old
                rule["enabled"] = new
                logger.info(f"[toggle_repeat_rule] 找到规则 {rule_word}，旧状态: {old} -> 新状态: {new}")
                found = True
                break
        if not found:
            logger.info(f"[toggle_repeat_rule] 错误：未找到规则 {rule_word}")
            return
        self.refresh_repeat_tree()
        logger.info("[toggle_repeat_rule] 结束")

    # ---------- Replace 操作 ----------
    def add_replace_group(self, parent_list=None):
        default = {"word": "新分组", "type": "group", "enabled": True, "items": []}
        dialog = ReplaceGroupDialog(default, self)
        if dialog.exec_() == QDialog.Accepted:
            new_group = dialog.get_data()
            if parent_list is None:
                self.data["replace"].append(new_group)
            else:
                parent_list.append(new_group)
            self.refresh_replace_tree(preserve_expanded=True)

    def add_replace_child_group(self, item):
        logger.info("[add_replace_child_group] 进入")
        node_data = item.data(0, Qt.UserRole)
        if node_data is None or "items" not in node_data:
            logger.info("[add_replace_child_group] 无效的父节点")
            return
        path = self._get_path_from_item(item)
        logger.info(f"[add_replace_child_group] 父节点路径: {path}")
        default = {"word": "新分组", "type": "group", "enabled": True, "items": []}
        dialog = ReplaceGroupDialog(default, self)
        if dialog.exec_() == QDialog.Accepted:
            new_group = dialog.get_data()
            def find_and_add(data_list, path_parts):
                if not path_parts:
                    return False
                for d in data_list:
                    if d.get("word") == path_parts[0]:
                        if len(path_parts) == 1:
                            if "items" in d:
                                d["items"].append(new_group)
                                logger.info(f"[add_replace_child_group] 已将分组添加到 {d['word']}")
                                return True
                        elif "items" in d:
                            return find_and_add(d["items"], path_parts[1:])
                return False
            if find_and_add(self.data["replace"], path):
                self.refresh_replace_tree(preserve_expanded=True)
            else:
                logger.info("[add_replace_child_group] 未找到父节点，尝试直接修改 node_data")
                node_data["items"].append(new_group)
                self.refresh_replace_tree(preserve_expanded=True)
        logger.info("[add_replace_child_group] 结束")

    def add_replace_child_item(self, item):
        logger.info("[add_replace_child_item] 进入")
        node_data = item.data(0, Qt.UserRole)
        if node_data is None or "items" not in node_data:
            logger.info("[add_replace_child_item] 无效的父节点")
            return
        path = self._get_path_from_item(item)
        logger.info(f"[add_replace_child_item] 父节点路径: {path}")
        default_item = {"word": "新子项", "enabled": True, "source": []}
        dialog = ReplaceItemDialog(default_item, self)
        if dialog.exec_() == QDialog.Accepted:
            new_item = dialog.get_data()
            def find_and_add(data_list, path_parts):
                if not path_parts:
                    return False
                for d in data_list:
                    if d.get("word") == path_parts[0]:
                        if len(path_parts) == 1:
                            if "items" in d:
                                d["items"].append(new_item)
                                logger.info(f"[add_replace_child_item] 已将子项添加到 {d['word']}")
                                return True
                        elif "items" in d:
                            return find_and_add(d["items"], path_parts[1:])
                return False
            if find_and_add(self.data["replace"], path):
                self.refresh_replace_tree(preserve_expanded=True)
            else:
                logger.info("[add_replace_child_item] 未找到父节点，尝试直接修改 node_data")
                node_data["items"].append(new_item)
                self.refresh_replace_tree(preserve_expanded=True)
        logger.info("[add_replace_child_item] 结束")

    def edit_replace_node(self, item):
        logger.info("[edit_replace_node] 进入")
        node_data = item.data(0, Qt.UserRole)
        if node_data is None:
            logger.info("[edit_replace_node] node_data is None, 退出")
            return
        typ = node_data.get("type", "item")
        path = self._get_path_from_item(item)
        logger.info(f"[edit_replace_node] 路径: {path}, 类型: {typ}")

        if typ == "group":
            dialog = ReplaceGroupDialog(node_data, self)
            if dialog.exec_() == QDialog.Accepted:
                new_data = dialog.get_data()
                new_word = new_data.get("word")
                new_enabled = new_data.get("enabled")
                logger.info(f"[edit_replace_node] 分组编辑确认: new_word={new_word}, new_enabled={new_enabled}")
                if self._update_data_by_path(path, new_word, new_enabled):
                    logger.info("[edit_replace_node] self.data 更新成功")
                else:
                    logger.info("[edit_replace_node] 警告：未找到对应节点，尝试直接更新 node_data")
                    node_data["word"] = new_word
                    node_data["enabled"] = new_enabled
                self.refresh_replace_tree(preserve_expanded=True)
            else:
                logger.info("[edit_replace_node] 对话框取消")
        else:
            dialog = ReplaceItemDialog(node_data, self)
            if dialog.exec_() == QDialog.Accepted:
                new_data = dialog.get_data()
                new_word = new_data.get("word")
                new_enabled = new_data.get("enabled")
                new_source = new_data.get("source", [])
                logger.info(f"[edit_replace_node] item 编辑确认: new_word={new_word}, new_enabled={new_enabled}, source数量={len(new_source)}")
                if self._update_data_by_path(path, new_word, new_enabled, new_source):
                    logger.info("[edit_replace_node] self.data 更新成功")
                else:
                    logger.info("[edit_replace_node] 警告：未在 self.data 中找到对应节点，尝试直接更新 node_data")
                    node_data["word"] = new_word
                    node_data["enabled"] = new_enabled
                    node_data["source"] = new_source
                self.refresh_replace_tree(preserve_expanded=True)
            else:
                logger.info("[edit_replace_node] 对话框取消")
        logger.info("[edit_replace_node] 结束")

    def delete_replace_node(self, item):
        logger.info("[delete_replace_node] 进入")
        node_data = item.data(0, Qt.UserRole)
        if node_data is None:
            logger.info("[delete_replace_node] node_data is None, 退出")
            return
        path = self._get_path_from_item(item)
        logger.info(f"[delete_replace_node] 路径: {path}")
        def remove_from(data_list, path_parts):
            if not path_parts:
                return False
            for idx, d in enumerate(data_list):
                if d.get("word") == path_parts[0]:
                    if len(path_parts) == 1:
                        del data_list[idx]
                        logger.info(f"[delete_replace_node] 已删除节点 {path_parts[0]}")
                        return True
                    elif "items" in d:
                        if remove_from(d["items"], path_parts[1:]):
                            return True
            return False
        if remove_from(self.data["replace"], path):
            self.refresh_replace_tree(preserve_expanded=True)
        else:
            parent_item = item.parent()
            if parent_item and parent_item.text(0) != "Replace":
                parent_data = parent_item.data(0, Qt.UserRole)
                if parent_data and "items" in parent_data:
                    for idx, child in enumerate(parent_data["items"]):
                        if child is node_data:
                            del parent_data["items"][idx]
                            logger.info("[delete_replace_node] 通过父节点直接删除成功")
                            self.refresh_replace_tree(preserve_expanded=True)
                            return
            logger.info("[delete_replace_node] 删除失败，未找到对应节点")

    def toggle_replace_node(self, item):
        """切换启用状态：同时更新树节点和 self.data"""
        logger.info("[toggle_replace_node] 进入")
        node_data = item.data(0, Qt.UserRole)
        if node_data is None:
            logger.info("[toggle_replace_node] node_data is None, 退出")
            return
        old = node_data.get("enabled", True)
        new_enabled = not old
        # 更新树节点显示和数据
        node_data["enabled"] = new_enabled
        word = node_data.get("word", "?")
        typ = node_data.get("type", "item")
        status = "✓" if new_enabled else "✗"
        new_text = f"[{typ}] {word} {status}"
        item.setText(0, new_text)
        item.setData(0, Qt.UserRole, node_data)

        # 使用统一的方法获取路径
        path = self._get_path_from_item(item)
        logger.info(f"[toggle_replace_node] 路径: {path}")

        # 在 self.data 中查找并更新
        def find_and_update(data_list, path_parts):
            if not path_parts:
                return False
            for d in data_list:
                if d.get("word") == path_parts[0]:
                    if len(path_parts) == 1:
                        d["enabled"] = new_enabled
                        logger.info(f"[toggle_replace_node] 已更新 self.data 中 {d['word']} 的 enabled = {new_enabled}")
                        return True
                    elif "items" in d:
                        return find_and_update(d["items"], path_parts[1:])
            return False

        if find_and_update(self.data["replace"], path):
            logger.info("[toggle_replace_node] self.data 同步成功")
        else:
            logger.info("[toggle_replace_node] 警告：未在 self.data 中找到对应节点")

        self.tree.viewport().update()
        logger.info("[toggle_replace_node] 结束")

    # ---------- 右键菜单 ----------
    def on_context_menu(self, pos):
        item = self.tree.itemAt(pos)
        if not item:
            return
        parent = item.parent()
        if not parent:
            top_text = item.text(0)
            menu = QMenu()
            if top_text == "Delete":
                add_prof = menu.addAction("添加 profanity 关键词")
                add_oth = menu.addAction("添加 others 关键词")
                action = menu.exec_(self.tree.viewport().mapToGlobal(pos))
                if action == add_prof:
                    self.add_delete_keyword("profanity")
                elif action == add_oth:
                    self.add_delete_keyword("others")
            elif top_text == "Repeat":
                add_rule = menu.addAction("添加重复规则")
                if menu.exec_(self.tree.viewport().mapToGlobal(pos)) == add_rule:
                    self.add_repeat_rule()
            elif top_text == "Replace":
                add_group = menu.addAction("添加顶层分组")
                if menu.exec_(self.tree.viewport().mapToGlobal(pos)) == add_group:
                    self.add_replace_group()
            return

        top_node = self.get_top_level_item(item)
        if not top_node:
            return
        top_text = top_node.text(0)

        if top_text == "Delete":
            if parent.text(0) in ("profanity", "others"):
                menu = QMenu()
                edit_act = menu.addAction("编辑关键词")
                del_act = menu.addAction("删除关键词")
                action = menu.exec_(self.tree.viewport().mapToGlobal(pos))
                if action == edit_act:
                    self.edit_delete_keyword(item, parent.text(0))
                elif action == del_act:
                    self.delete_delete_keyword(item, parent.text(0))
            elif parent == top_node and item.text(0) in ("profanity", "others"):
                menu = QMenu()
                add_act = menu.addAction("添加关键词")
                if menu.exec_(self.tree.viewport().mapToGlobal(pos)) == add_act:
                    self.add_delete_keyword(item.text(0))

        elif top_text == "Repeat":
            if parent == top_node:
                menu = QMenu()
                edit_act = menu.addAction("编辑规则")
                del_act = menu.addAction("删除规则")
                toggle_act = menu.addAction("切换启用")
                action = menu.exec_(self.tree.viewport().mapToGlobal(pos))
                if action == edit_act:
                    self.edit_repeat_rule(item)
                elif action == del_act:
                    self.delete_repeat_rule(item)
                elif action == toggle_act:
                    self.toggle_repeat_rule(item)

        elif top_text == "Replace":
            node_data = item.data(0, Qt.UserRole)
            if node_data is None:
                return
            typ = node_data.get("type", "item")
            menu = QMenu()
            edit_act = menu.addAction("编辑")
            del_act = menu.addAction("删除")
            toggle_act = menu.addAction("切换启用")
            menu.addSeparator()
            if typ == "group":
                add_child_group = menu.addAction("添加子分组")
                add_child_item = menu.addAction("添加子项")
            else:
                add_child_group = add_child_item = None
            action = menu.exec_(self.tree.viewport().mapToGlobal(pos))
            logger.info(f"[右键菜单] Replace 节点, 选择 action: {action.text() if action else None}")
            if action == edit_act:
                self.edit_replace_node(item)
            elif action == del_act:
                self.delete_replace_node(item)
            elif action == toggle_act:
                self.toggle_replace_node(item)
            elif typ == "group" and action == add_child_group:
                self.add_replace_child_group(item)
            elif typ == "group" and action == add_child_item:
                self.add_replace_child_item(item)

    def get_top_level_item(self, item):
        while item.parent():
            item = item.parent()
        return item
    

def run():
    logger.info("规则配置已启动")
    app = QApplication(sys.argv)
    win = SubtitleEditor()
    win.show()
    sys.exit(app.exec_())



# ---------- 启动 ----------
if __name__ == "__main__":
    run()