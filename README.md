# Grid Trading Tool

## Description

The Grid Trading Tool is a powerful application with a user-friendly graphical interface for creating, visualizing, and managing grid trading strategies. It enables users to input parameters such as total funds, initial price, stop-loss price, number of grids, and allocation method to generate a customized grid trading plan.

## Disclaimer

IMPORTANT: This software is provided for educational and informational purposes only. It is not intended to be used as financial advice or as a recommendation to make any specific investment decisions.

The use of this tool involves significant financial risk. Grid trading and other investment strategies can result in substantial losses, especially in volatile market conditions. The author of this software is not responsible for any financial losses or damages incurred as a result of using this tool.

By using this software, you acknowledge that:

1. You are solely responsible for any investment decisions you make.
2. You understand the risks involved in trading and investing.
3. You will not hold the author liable for any losses or damages resulting from the use of this software.
4. You are encouraged to seek advice from licensed financial professionals before making any investment decisions.

The author makes no guarantees about the accuracy, reliability, or completeness of the information provided by this tool. Market conditions can change rapidly, and past performance does not guarantee future results.

USE THIS SOFTWARE AT YOUR OWN RISK.

## Features

- Multiple allocation methods: Equal amount, Proportional, and Linear weighted
- Real-time stock price fetching for common stocks
- Dynamic common stock buttons and live status bar for immediate feedback
- Configuration saving/loading and CSV export of trading plans
- User-friendly GUI with intuitive layout
- Automatic update checking and installation
- Support for both Yahoo Finance and Alpha Vantage APIs for stock data retrieval
- Trading instruction parsing for quick and flexible plan generation
- Price tolerance checking and automatic adjustment of stop-loss prices
- User-specific configuration file for personalized settings
- Moomoo API integration for real-time trading capabilities and account information
- Support for US and HK stock markets in both real and simulated trading environments

## Project Structure

```plaintext
grid-trading-tool/
├── src/
│   ├── __init__.py
│   ├── api_interface.py
│   ├── api_manager.py
│   ├── calculations.py
│   ├── config.py
│   ├── gui.py
│   ├── status_manager.py
│   └── utils.py
├── tests/
│   ├── test_calculations.py
│   └── test_instruction_parsing.py
├── assets/
│   └── icons/
│       └── app_icon.ico
├── logs/
├── output/
├── scripts/
│   ├── build_exe.py
│   └── test_moomoo_api.py
├── .github/
│   └── workflows/
│       └── python-app.yml
├── grid_trading_app.py
├── config.ini
├── CHANGELOG.md
├── LICENSE
├── README.md
├── README-zh-CN.md
├── userconfig.ini.template
├── requirements.txt
└── version.py
```

## Installation

### For Windows Users

1. Go to the [Releases](https://github.com/znhskzj/grid-trading-tool/releases) page.
2. Download the latest `.exe` file.
3. Double-click the downloaded file to run the application.

### For Developers

If you want to run the script from source or contribute to the project:

1. Ensure you have Python 3.7 or higher installed.
2. Clone the repository:
   ```
   git clone https://github.com/znhskzj/grid-trading-tool.git
   ```
3. Navigate to the project directory:
   ```
   cd grid-trading-tool
   ```
4. Create a virtual environment:
   ```
   python -m venv venv
   ```
5. Activate the virtual environment:
   - On Windows: `venv\Scripts\activate`
   - On macOS and Linux: `source venv/bin/activate`
6. Install required packages:
   ```
   pip install -r requirements.txt
   ```
7. Run the script:
   ```
   python grid_trading_app.py
   ```

## Usage

1. Launch the application by double-clicking the executable or running `python grid_trading_app.py` if using the source code.

2. In the main window:
   - The left panel displays common stock buttons.
   - The right panel contains input fields, control buttons, and settings.

3. Click "Common Stocks" to view and select predefined stocks:
   - Clicking on a stock symbol (e.g., AAPL, GOOGL) will automatically fetch its current price.

4. Input trading parameters:
   - Available Funds: Enter the total amount you want to invest.
   - Initial Price: This is auto-filled if you selected a stock, or you can manually enter a value.
   - Stop Loss Price: Enter the price at which you want to exit the trade to limit losses.
   - Number of Grids: Enter the number of price levels for your grid strategy.

5. Choose an allocation method:
   - Equal Amount: Distributes funds equally across all grids.
   - Proportional: Allocates more funds to grids closer to the current price.
   - Linear Weighted: Gradually increases allocation as price moves away from the initial price.

6. Select API source:
   - Choose between Yahoo Finance and Alpha Vantage for stock data retrieval.

7. Configure Moomoo settings:
   - Select between real and simulated trading environments.
   - Choose between US and HK stock markets.
   - Click "Test Connection" to verify Moomoo API connectivity.

8. Click "Calculate Purchase Plan" to generate the grid trading plan.

9. View results in the text area below:
   - The plan will show total funds, reserved funds (if any), available funds, and the allocation for each grid.

10. Additional options:
    - "Calculate with 10% Reserve" or "Calculate with 20% Reserve": Generates a plan while keeping a portion of funds in reserve.
    - "Save as CSV": Exports the current plan to a CSV file for further analysis or record-keeping.
    - "Reset to Default Values": Resets input fields while preserving common stocks and Moomoo settings.

11. Trading Instruction Parsing:
    - Enter a trading instruction in the designated field to generate a plan based on the instruction.
    - The application will parse the instruction and generate a plan accordingly.

12. Automatic Updates:
    - The application will periodically check for updates.
    - If an update is available, you will be prompted to download and install it.

13. Querying Account Information
    - Ensure you have set up your Moomoo API connection in the settings.
    - Click on the "Query Available Funds" button to view your current account balance and available funds.
    - Use the "Query Stock Positions" button to see a detailed breakdown of your current stock holdings, including:
      - Stock code
      - Quantity
      - Current market value
      - Profit/Loss percentage

### Moomoo API Integration

- The tool supports both real and simulated trading environments.
- You can switch between US and HK markets in the Moomoo settings.
- Always test your API connection before performing any operations.
- Ensure your Moomoo account has the necessary permissions for the operations you wish to perform.

## Configuration

The `config.ini` file in the project root contains default settings and common stocks. You can modify this file to customize the application's default behavior and add or remove common stocks.

The `config.ini` file includes API settings. You can choose between Yahoo Finance and Alpha Vantage for stock price fetching. If you choose Alpha Vantage, you need to provide an API key.

### Example Configuration

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

[API]
choice = yahoo
alpha_vantage_key = your_alpha_vantage_key_here
```

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

If you encounter any problems, please file an issue along with a detailed description.

For detailed release notes, please see the [Changelog](CHANGELOG.md).