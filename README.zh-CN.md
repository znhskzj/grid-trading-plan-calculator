# 网格交易计划计算器

版本：1.2.0
作者：Rong Zhu
日期：2024年7月31日

## 描述

网格交易计划计算器是一个用户友好的工具，具有图形界面，用于创建和可视化网格交易策略。用户可以输入总资金、初始价格、止损价格、网格数量和分配方式等参数，生成定制的网格交易计划。

## 功能特性

- 多种分配方式：等金额分配、等比例分配和线性加权
- 配置保存和加载
- 交易计划导出为CSV文件
- 日志记录，便于调试和审计

## 项目结构

- `grid_buying_plan_gui.py`：主程序文件，包含GUI实现和核心逻辑。
- `app_icon.ico`：应用程序图标文件。
- `config.json`：配置文件，存储用户的默认设置。
- `Grid Trading Plan Calculator.spec`：PyInstaller规格文件，用于构建可执行文件。
- `grid_trading.log`：日志文件，记录程序运行时的信息。
- `LICENSE`：项目许可证文件。
- `README.md`：项目说明文件（英文版）。
- `README-zh-CN.md`：项目说明文件（中文版）。
- `requirements.txt`：列出项目依赖的Python包。

### scripts 目录
- `build_exe.py`：用于构建独立可执行文件的脚本。

### dist 目录
- `Grid Trading Plan Calculator.exe`：构建后的可执行文件。

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

1. 前往[发布页面](https://github.com/yourusername/grid-trading-plan-calculator/releases)。
2. 下载最新的`.exe`文件。
3. 双击下载的文件即可运行应用程序。

### 开发者

如果您想从源代码运行脚本或为项目做出贡献：

1. 确保已安装 Python 3.7 或更高版本。
2. 克隆仓库：
git clone https://github.com/yourusername/grid-trading-plan-calculator.git
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

## 修订记录

### 版本 1.2.0 (2024年7月31日)
- 增加了保留资金功能，新增"保留10%计算"和"保留20%计算"按钮
- 优化了计算结果显示，增加了平均购买价格、最大潜在亏损等信息
- 改进了CSV导出功能，解决了中文乱码问题，并确保所有重要信息都被保存
- 修复了多个bug，提高了程序的稳定性
- 优化了用户界面，改善了按钮布局


### 版本 1.1.0 (2024年7月30日)
- 优化了基于总资金和初始价格的可购买股数计算
- 改进了"等比例分配"方法，确保每个网格至少分配1股
- 增加了对数值输入的更多验证
- 为结果显示区域添加了垂直滚动条，以适应大量网格的情况
- 设置了输入字段的 Tab 顺序，提升用户体验

### 版本 1.0.0 (2024年7月26日)
- 初始发布
- 实现了基本的网格交易计划计算
- 使用 tkinter 添加了图形用户界面
- 实现了多种分配方法：等金额分配、等比例分配和线性加权
- 添加了配置保存和加载功能
- 实现了将交易计划导出为 CSV 文件的功能
- 添加了日志记录，便于调试和审计