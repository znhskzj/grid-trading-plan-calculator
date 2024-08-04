# scripts/update_readme.py

import re
from pathlib import Path
from version import VERSION, AUTHOR, DATE


def update_readme(filename):
    with open(filename, 'r', encoding='utf-8') as file:
        content = file.read()

    if filename.endswith('README.zh-CN.md'):
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
