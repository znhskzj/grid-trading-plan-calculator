# 网格交易计划计算器

版本：1.5.0
作者：Rong Zhu
日期：August 5, 2024

## 描述

网格交易计划计算器是一个用户友好的工具，具有图形界面，用于创建和可视化网格交易策略。用户可以输入总资金、初始价格、止损价格、网格数量和分配方式等参数，生成定制的网格交易计划。

## 功能特性

- 多种分配方法：等额分配、比例分配和线性加权分配
- 实时获取常见股票的股价
- 计算过程中动态状态更新
- 配置保存和加载功能
- 交易计划的CSV导出
- 全面的日志记录用于调试和审计
- 用户友好的GUI，布局直观

## 项目结构

### 目录及文件结构
```plaintext
grid-trading-plan-calculator/
├── src/
│   ├── __init__.py
│   ├── calculations.py
│   ├── config.py
│   ├── gui.py
│   ├── utils.py
│   └── status_manager.py
├── tests/
│   ├── __pycache__/
│   └── test_calculations.py
├── assets/
│   └── icons/
│       └── app_icon.ico
├── build/
├── dist/
├── logs/
├── output/
├── scripts/
│   ├── build_exe.py
│   └── update_readme.py
├── .github/
│   └── workflows/
│       └── python-app.yml
├── grid_trading_app.py
├── config.ini
├── CHANGELOG.md
├── Grid Trading Plan Calculator.spec
├── Grid Trading Tool.spec
├── LICENSE
├── project_requirements.md
├── pytest.ini
├── README.md
├── README-zh-CN.md
├── requirements.txt
└── version.py
```

### 主要文件说明：
- grid_trading_app.py：应用程序的主入口。
- src/：包含核心应用模块的目录。
- tests/：包含单元测试的目录。
- assets/：存放图标等静态资源的目录。
- logs/：存放日志文件的目录。
- scripts/：包含实用脚本（如构建脚本）的目录。
- config.ini：存储用户默认设置的配置文件。
- CHANGELOG.md：详细的版本历史和更新。
- version.py：管理版本的中心文件。
- requirements.txt：Python包依赖列表。
- LICENSE：许可证文件。
- README.md：项目主文档。
- README-zh-CN.md：中文版本的文档。

## 构建说明

要构建独立的可执行文件，请按以下步骤操作：

1. 确保您的系统已安装Python 3.7或更高版本。
2. 打开命令提示符，导航到项目根目录。
3. 运行以下命令：
```
python scripts/build_exe.py
```
4. 构建完成后，可执行文件将位于 `dist` 目录中。


## 安装

### Windows用户

1. 前往[发布页面](https://github.com/znhskzj/grid-trading-plan-calculator/releases)。
2. 下载最新的`.exe`文件。
3. 双击下载的文件即可运行应用程序。

### 开发者

如果您想从源代码运行脚本或为项目做出贡献：

1. 确保已安装 Python 3.7 或更高版本。
2. 克隆仓库：
git clone https://github.com/znhskzj/grid-trading-plan-calculator.git
3. 进入项目目录：
cd grid-trading-plan-calculator
4. 创建虚拟环境：
python -m venv venv
5. 激活虚拟环境：
- Windows: `venv\Scripts\activate`
- macOS 和 Linux: `source venv/bin/activate`
6. 安装所需包：
pip install -r requirements.txt
7. 运行脚本：
python grid_trading_plan.py

## 使用方法

1. 启动应用程序。
2. 输入您的交易参数。
3. 点击"计算"生成网格交易计划。
4. 如需导出结果，使用"保存为CSV"功能。

## 许可证

本项目采用 MIT 许可证。详情请见 [LICENSE](LICENSE) 文件。

## 贡献

欢迎贡献！请随时提交 Pull Request。

## 支持

如果您遇到任何问题，请提交 issue 并附上详细描述。

有关详细的发布说明，请查看[更新日志](CHANGELOG.md)。
