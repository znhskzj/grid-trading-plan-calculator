# 网格交易计划计算器

版本：1.0.0
作者：Rong Zhu
日期：2024年7月26日

## 描述

网格交易计划计算器是一个用户友好的工具，具有图形界面，用于创建和可视化网格交易策略。用户可以输入总资金、初始价格、止损价格、网格数量和分配方式等参数，生成定制的网格交易计划。

## 功能特性

- 多种分配方式：等金额分配、等比例分配和线性加权
- 配置保存和加载
- 交易计划导出为CSV文件
- 日志记录，便于调试和审计

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
