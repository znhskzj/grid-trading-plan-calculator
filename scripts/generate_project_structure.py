import os
import ast
import json
import argparse
from typing import Dict, List, Any
import fnmatch
import re
from datetime import datetime
import difflib
import codecs
from tqdm import tqdm

# 默认排除列表
DEFAULT_EXCLUDES = {
    '.vscode', '.idea',      # IDE 配置
    'node_modules',          # Node.js 模块
    'output',                # 输出目录
    'venv', 'env',           # 虚拟环境
    'build', 'dist',         # 构建目录
    '.git',                  # Git 目录
    '__pycache__',           # Python 缓存
    'site-packages',         # 第三方包
    'tests', 'test'          # 测试目录
}

# 要跳过的文件名列表
SKIP_FILES = {'__init__.py', '_init_.py', 'setup.py'}

def parse_gitignore(gitignore_path: str) -> List[str]:
    """解析.gitignore文件，返回排除模式列表"""
    if not os.path.exists(gitignore_path):
        return []
    
    with open(gitignore_path, 'r') as f:
        lines = f.readlines()
    
    patterns = []
    for line in lines:
        line = line.strip()
        if line and not line.startswith('#'):
            # 将.gitignore模式转换为正则表达式
            pattern = re.escape(line).replace(r'\*', '.*').replace(r'\?', '.')
            if not line.startswith('/'):
                pattern = f'.*{pattern}'
            patterns.append(f'^{pattern}$')
    
    return patterns

def should_exclude(path: str, exclude_patterns: List[str], default_excludes: set) -> bool:
    """检查给定路径是否应该被排除"""
    # 检查是否在默认排除列表中
    if any(exclude in path.split(os.sep) for exclude in default_excludes):
        return True
    
    # 检查是否匹配.gitignore模式
    for pattern in exclude_patterns:
        if re.match(pattern, path):
            return True
    return False

def parse_file(file_path: str) -> Dict[str, Any]:
    """解析单个Python文件，提取类和函数信息"""
    try:
        with codecs.open(file_path, 'r', 'utf-8-sig') as file:
            content = file.read()
    except UnicodeDecodeError:
        print(f"Warning: Unable to read file {file_path} with UTF-8 encoding. Skipping.")
        return {'classes': [], 'functions': []}
    
    try:
        tree = ast.parse(content)
    except SyntaxError as e:
        print(f"Warning: Syntax error in file {file_path}: {e}. Skipping.")
        return {'classes': [], 'functions': []}
    
    classes = []
    functions = []
    
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            methods = []
            for item in node.body:
                if isinstance(item, ast.FunctionDef):
                    methods.append({
                        'name': item.name,
                        'docstring': ast.get_docstring(item) or 'No description available',
                        'lineno': item.lineno,
                        'args': [arg.arg for arg in item.args.args if arg.arg != 'self']
                    })
            classes.append({
                'name': node.name,
                'docstring': ast.get_docstring(node) or 'No description available',
                'methods': methods,
                'lineno': node.lineno
            })
        elif isinstance(node, ast.FunctionDef) and node.name != '<lambda>':
            functions.append({
                'name': node.name,
                'docstring': ast.get_docstring(node) or 'No description available',
                'lineno': node.lineno,
                'args': [arg.arg for arg in node.args.args]
            })
    
    return {
        'classes': classes,
        'functions': functions
    }

def get_project_structure(project_root: str, exclude_patterns: List[str], default_excludes: set) -> Dict[str, Any]:
    """获取完整的项目目录结构"""
    structure = {"name": os.path.basename(project_root), "type": "directory", "children": []}
    
    for root, dirs, files in os.walk(project_root):
        # 修改 dirs 列表以跳过排除的目录
        dirs[:] = [d for d in dirs if not should_exclude(os.path.join(root, d), exclude_patterns, default_excludes)]
        
        rel_path = os.path.relpath(root, project_root)
        current = structure
        if rel_path != '.':
            for part in rel_path.split(os.sep):
                found = next((c for c in current["children"] if c["name"] == part), None)
                if not found:
                    new_dir = {"name": part, "type": "directory", "children": []}
                    current["children"].append(new_dir)
                    current = new_dir
                else:
                    current = found
        
        for file in files:
            if not should_exclude(os.path.join(rel_path, file), exclude_patterns, default_excludes):
                current["children"].append({"name": file, "type": "file"})
    
    return structure

def generate_structure_markdown(structure: Dict[str, Any], level: int = 0) -> str:
    """生成目录结构的Markdown表示"""
    result = ""
    indent = "  " * level
    if structure["type"] == "directory":
        result += f"{indent}- 📁 {structure['name']}/\n"
        for child in sorted(structure["children"], key=lambda x: (x["type"], x["name"])):
            result += generate_structure_markdown(child, level + 1)
    else:
        result += f"{indent}- 📄 {structure['name']}\n"
    return result

def analyze_project(project_root: str, exclude_patterns: List[str], default_excludes: set) -> Dict[str, Any]:
    """分析项目目录下的Python文件，跳过排除的文件和目录"""
    project_info = {}
    
    # 首先收集所有需要分析的文件
    files_to_analyze = []
    for root, dirs, files in os.walk(project_root):
        # 修改 dirs 列表以跳过排除的目录
        dirs[:] = [d for d in dirs if not should_exclude(os.path.join(root, d), exclude_patterns, default_excludes)]
        
        for file in files:
            if file.endswith('.py') and file not in SKIP_FILES:
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, project_root)
                if not should_exclude(rel_path, exclude_patterns, default_excludes):
                    files_to_analyze.append((rel_path, file_path))
    
    # 使用tqdm创建进度条
    for rel_path, file_path in tqdm(files_to_analyze, desc="Analyzing files", unit="file"):
        project_info[rel_path] = parse_file(file_path)
    
    return project_info

def generate_markdown_report(project_info: Dict[str, Any], project_structure: Dict[str, Any], output_file: str):
    """生成Markdown格式的报告，包括项目结构和Python文件分析"""
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# Project Structure Report\n\n")
        f.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("## Project Directory Structure\n\n")
        f.write("```\n")
        f.write(generate_structure_markdown(project_structure))
        f.write("```\n\n")
        
        f.write("## Python File Analysis\n\n")
        for file_path, file_info in project_info.items():
            f.write(f"### {file_path}\n\n")
            
            if file_info['classes']:
                f.write("#### Classes\n\n")
                for class_info in file_info['classes']:
                    f.write(f"##### {class_info['name']}\n\n")
                    f.write(f"- **Description**: {class_info['docstring']}\n")
                    f.write(f"- **Line**: {class_info['lineno']}\n\n")
                    
                    if class_info['methods']:
                        f.write("Methods:\n\n")
                        for method in class_info['methods']:
                            f.write(f"- **{method['name']}({', '.join(method['args'])})**\n")
                            f.write(f"  - Description: {method['docstring']}\n")
                            f.write(f"  - Line: {method['lineno']}\n\n")
            
            if file_info['functions']:
                f.write("#### Functions\n\n")
                for func in file_info['functions']:
                    f.write(f"##### {func['name']}({', '.join(func['args'])})\n\n")
                    f.write(f"- **Description**: {func['docstring']}\n")
                    f.write(f"- **Line**: {func['lineno']}\n\n")
            
            f.write("---\n\n")

def compare_reports(old_report: str, new_report: str, output_file: str):
    """比较两个Markdown报告并生成差异报告"""
    with open(old_report, 'r', encoding='utf-8') as f:
        old_content = f.readlines()
    with open(new_report, 'r', encoding='utf-8') as f:
        new_content = f.readlines()
    
    diff = difflib.unified_diff(old_content, new_content, fromfile=old_report, tofile=new_report)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# Project Structure Comparison Report\n\n")
        f.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("```diff\n")
        f.writelines(diff)
        f.write("```\n")

def main():
    parser = argparse.ArgumentParser(description="Analyze Python project structure")
    parser.add_argument("--exclude", nargs="*", help="Additional directories or files to exclude")
    parser.add_argument("--compare", help="Path to an old report to compare with")
    args = parser.parse_args()

    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    gitignore_path = os.path.join(project_root, '.gitignore')
    output_dir = os.path.join(project_root, 'output')
    os.makedirs(output_dir, exist_ok=True)
    
    # 解析 .gitignore 文件
    exclude_patterns = parse_gitignore(gitignore_path)
    
    # 合并默认排除和用户指定的排除
    default_excludes = DEFAULT_EXCLUDES.union(set(args.exclude or []))
    
    # 获取项目结构
    project_structure = get_project_structure(project_root, exclude_patterns, default_excludes)
    
    # 分析Python文件
    project_info = analyze_project(project_root, exclude_patterns, default_excludes)
    
    # 生成带时间戳的文件名
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 保存为 JSON 文件
    json_output = os.path.join(output_dir, f'project_structure_{timestamp}.json')
    with open(json_output, 'w', encoding='utf-8') as f:
        json.dump({"structure": project_structure, "analysis": project_info}, f, ensure_ascii=False, indent=2)
    
    # 生成 Markdown 报告
    markdown_output = os.path.join(output_dir, f'project_structure_report_{timestamp}.md')
    generate_markdown_report(project_info, project_structure, markdown_output)
    
    print(f"Project structure analysis complete.")
    print(f"JSON output saved to: {json_output}")
    print(f"Markdown report saved to: {markdown_output}")

    # 如果指定了比较选项，生成比较报告
    if args.compare:
        compare_output = os.path.join(output_dir, f'project_structure_comparison_{timestamp}.md')
        compare_reports(args.compare, markdown_output, compare_output)
        print(f"Comparison report saved to: {compare_output}")

if __name__ == "__main__":
    main()