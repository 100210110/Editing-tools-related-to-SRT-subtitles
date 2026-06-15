import sys
import json
import io
import PySimpleGUI as sg

# 强制所有标准流使用 UTF-8
sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding='utf-8')
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

def run(params=None):
    sg.popup(
        params,
        title="test弹窗_2",
        button_type=True,
        custom_text="test2"
    )



if __name__ == "__main__":
    run()
