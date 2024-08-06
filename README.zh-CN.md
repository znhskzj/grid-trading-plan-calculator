# 网格交易计划计算器

版本：1.5.0
作者：Rong Zhu
日期：August 5, 2024

## 描述

网格交易计划计算器是一个用户友好的工具，具有图形界面，用于创建和可视化网格交易策略。用户可以输入总资金、初始价格、止损价格、网格数量和分配方式等参数，生成定制的网格交易计划。

## 功能特性

- 多种资金分配方法：等额分配、比例分配和线性加权分配
- 常用股票的实时价格获取
- 左侧面板的动态常用股票按钮
- 实时状态栏，提供即时反馈和错误信息
- 配置保存和加载
- 交易计划的CSV导出
- 全面的日志记录，用于调试和审计
- 用户友好的图形界面，布局直观
- 自动更新检查和安装

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
- version.py：版本管理和更新检查的中心文件。
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

1. 启动应用程序：双击可执行文件，或如果使用源代码，运行 `python grid_trading_app.py`。

2. 在主窗口中：
   - 左侧面板显示常用股票按钮。
   - 右侧面板包含输入字段和控制按钮。

3. 点击"常用标的"查看和选择预定义的股票：
   - 点击股票代码（如 AAPL、GOOGL）将自动获取其当前价格。

4. 输入交易参数：
   - 可用资金：输入您想投资的总金额。
   - 初始价格：如果您选择了股票，此项会自动填充，或者您可以手动输入。
   - 止损价格：输入您想退出交易以限制损失的价格。
   - 网格数量：输入您的网格策略中的价格级别数量。

5. 选择分配方式：
   - 等金额分配：在所有网格中平均分配资金。
   - 等比例分配：为靠近当前价格的网格分配更多资金。
   - 线性加权：随着价格远离初始价格，逐渐增加分配。

6. 点击"计算购买计划"生成网格交易计划。

7. 在下方的文本区域查看结果：
   - 计划将显示每个网格的价格水平和在该水平应投资的金额。

8. 其他选项：
   - "保留10%计算"或"保留20%计算"：生成计划时保留部分资金作为储备。
   - "保存为CSV"：将当前计划导出为 CSV 文件，以便进一步分析或记录。
   - "重置为默认值"：将所有输入字段重置为配置中的默认值。

9. 自动更新：
   - 应用程序将定期检查更新。
   - 如果有可用更新，系统会提示您下载并安装。

### 使用示例

假设您想为苹果（AAPL）股票创建一个网格交易计划：

1. 启动应用程序。
2. 点击"常用标的"，然后点击"AAPL"。
3. AAPL 的当前价格将自动获取（假设是150元）。
4. 输入以下内容：
   - 可用资金：10000（假设您想投资10,000元）
   - 初始价格：150（从获取的价格自动填充）
   - 止损价格：140（您决定如果价格降到140元就止损）
   - 网格数量：5（您想要5个价格级别的网格）
5. 选择"等比例分配"作为分配方式。
6. 点击"计算购买计划"。
7. 结果将显示140元到150元之间的5个价格级别，靠近150元的网格分配更多资金。
8. 如果您对计划满意，点击"保存为CSV"导出它。

## 配置

项目根目录中的 `config.ini` 文件包含默认设置和常用股票。您可以修改此文件来自定义应用程序的默认行为并添加或删除常用股票。

### 配置示例

以下是 `config.ini` 的一个示例：

```ini
[General]
funds = 50000.0
initial_price = 50.0
stop_loss_price = 30.0
num_grids = 10
allocation_method = 1

[CommonStocks]
stock1 = AAPL
stock2 = GOOGL
stock3 = MSFT
stock4 = AMZN
stock5 = TSLA
```

### 自定义方法：

* 在文本编辑器中打开 config.ini。
* 在 [General] 下，根据需要修改默认值：

funds：默认可用资金
initial_price：默认初始价格
stop_loss_price：默认止损价格
num_grids：默认网格数量
allocation_method：默认分配方式（0 为等金额，1 为等比例，2 为线性加权）


* 在 [CommonStocks] 下，添加或删除股票：

要添加新股票，添加新行：stockX = 股票代码（将 X 替换为下一个数字，股票代码替换为实际的股票代码）
要删除股票，删除相应的行

修改后保存文件。下次启动应用程序时，将使用这些新的默认值和常用股票列表。

## 即将推出的功能

- 用户特定的配置文件，用于个性化设置
- 基于用户偏好的可自定义自动更新检查
- Moomoo 交易平台集成，实现实时交易功能

## 许可证

本项目采用 MIT 许可证。详情请见 [LICENSE](LICENSE) 文件。

## 贡献

欢迎贡献！请随时提交 Pull Request。

## 支持

如果您遇到任何问题，请提交 issue 并附上详细描述。

有关详细的发布说明，请查看[更新日志](CHANGELOG.md)。
