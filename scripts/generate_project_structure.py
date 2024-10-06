import os
import ast
import json
from typing import Dict, List, Any

def parse_file(file_path: str) -> Dict[str, Any]:
    """解析单个Python文件，提取类和函数信息"""
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    tree = ast.parse(content)
    
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
                        'lineno': item.lineno
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
                'lineno': node.lineno
            })
    
    return {
        'classes': classes,
        'functions': functions
    }

def analyze_project(project_root: str) -> Dict[str, Any]:
    """分析项目根目录和src目录下的Python文件"""
    project_info = {}
    
    # 分析根目录下的Python文件
    for file in os.listdir(project_root):
        if file.endswith('.py'):
            file_path = os.path.join(project_root, file)
            project_info[file] = parse_file(file_path)
    
    # 分析src目录下的Python文件
    src_dir = os.path.join(project_root, 'src')
    if os.path.exists(src_dir):
        for file in os.listdir(src_dir):
            if file.endswith('.py'):
                file_path = os.path.join(src_dir, file)
                project_info[os.path.join('src', file)] = parse_file(file_path)
    
    return project_info

def generate_markdown_report(project_info: Dict[str, Any], output_file: str):
    """生成Markdown格式的报告"""
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# Project Structure Report\n\n")
        
        for file_path, file_info in project_info.items():
            f.write(f"## {file_path}\n\n")
            
            if file_info['classes']:
                f.write("### Classes\n\n")
                for class_info in file_info['classes']:
                    f.write(f"#### {class_info['name']}\n\n")
                    f.write(f"- **Description**: {class_info['docstring']}\n")
                    f.write(f"- **Line**: {class_info['lineno']}\n\n")
                    
                    if class_info['methods']:
                        f.write("Methods:\n\n")
                        for method in class_info['methods']:
                            f.write(f"- **{method['name']}**\n")
                            f.write(f"  - Description: {method['docstring']}\n")
                            f.write(f"  - Line: {method['lineno']}\n\n")
            
            if file_info['functions']:
                f.write("### Functions\n\n")
                for func in file_info['functions']:
                    f.write(f"#### {func['name']}\n\n")
                    f.write(f"- **Description**: {func['docstring']}\n")
                    f.write(f"- **Line**: {func['lineno']}\n\n")
            
            f.write("---\n\n")

def main():
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    output_dir = os.path.join(project_root, 'output')
    os.makedirs(output_dir, exist_ok=True)
    
    project_info = analyze_project(project_root)
    
    # 保存为 JSON 文件
    json_output = os.path.join(output_dir, 'project_structure.json')
    with open(json_output, 'w', encoding='utf-8') as f:
        json.dump(project_info, f, ensure_ascii=False, indent=2)
    
    # 生成 Markdown 报告
    markdown_output = os.path.join(output_dir, 'project_structure_report.md')
    generate_markdown_report(project_info, markdown_output)
    
    print(f"Project structure analysis complete.")
    print(f"JSON output saved to: {json_output}")
    print(f"Markdown report saved to: {markdown_output}")

if __name__ == "__main__":
    main()