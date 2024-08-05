# scripts/update_readme.py

import re
import sys
from pathlib import Path

# 获取项目根目录并添加到 Python 路径
root_dir = Path(__file__).parent.parent
sys.path.append(str(root_dir))

from version import VERSION, AUTHOR, DATE  # 在添加路径之后再导入

def update_readme(filename):
    with open(filename, 'r', encoding='utf-8') as file:
        content = file.read()

    filename_str = str(filename)  # 将 Path 对象转换为字符串

    if filename_str.endswith('README.zh-CN.md'):
        content = re.sub(r'版本：.*', f'版本：{VERSION}', content)
        content = re.sub(r'作者：.*', f'作者：{AUTHOR}', content)
        content = re.sub(r'日期：.*', f'日期：{DATE}', content)
    else:
        content = re.sub(r'Version: .*', f'Version: {VERSION}', content)
        content = re.sub(r'Author: .*', f'Author: {AUTHOR}', content)
        content = re.sub(r'Date: .*', f'Date: {DATE}', content)

    with open(filename, 'w', encoding='utf-8') as file:
        file.write(content)

if __name__ == "__main__":
    root_dir = Path(__file__).parent.parent  # 获取项目根目录
    update_readme(root_dir / 'README.md')
    update_readme(root_dir / 'README.zh-CN.md')
