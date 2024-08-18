# Grid Trading Plan Calculator

## Description

The Grid Trading Plan Calculator is a powerful tool with a user-friendly graphical interface for creating, visualizing, and managing grid trading strategies. It enables users to input parameters such as total funds, initial price, stop-loss price, number of grids, and allocation method to generate a customized grid trading plan.

## Features

- Multiple allocation methods: Equal amount, Proportional, and Linear weighted
- Real-time stock price fetching for common stocks
- Dynamic common stock buttons in the left panel
- Live status bar for immediate feedback and error messages
- Configuration saving and loading
- CSV export of trading plans
- Comprehensive logging for debugging and auditing
- User-friendly GUI with intuitive layout
- Automatic update checking and installation
- Users can switch between Yahoo Finance and Alpha Vantage for stock data retrieval
- Trading instruction parsing for quick and flexible plan generation
- Automatic adjustment of stop-loss prices to ensure they are below current prices
- Price tolerance checking to warn users of significant price discrepancies
- User-specific configuration file for personalized settings
- Automatic saving and loading of user preferences
- Moomoo API integration for real-time trading capabilities
- Support for both real and simulated trading environments
- Market selection between US and HK stocks
- Enhanced fund allocation display showing total, reserved, and available funds
- Integration with Moomoo API for real-time account information and stock positions
- Detailed display of stock portfolio, including quantity, market value, and profit/loss for each position
- Support for both real and simulated trading environments in US and HK markets


## Project Structure

### Directory and File Structure
```plaintext
grid-trading-plan-calculator/
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
│   ├── test_moomoo_api.py
│   └── update_readme.py
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

### Main File Descriptions:

- `grid_trading_app.py`: Main entry point of the application.
- `src/`: Directory containing core application modules.
  - `__init__.py`: Initializes the src package.
  - `api_interface.py`: Defines interfaces for different APIs.
  - `api_manager.py`: Manages API connections and requests.
  - `calculations.py`: Contains core calculation logic for grid trading.
  - `config.py`: Handles configuration loading and saving.
  - `gui.py`: Implements the graphical user interface.
  - `status_manager.py`: Manages application status updates.
  - `utils.py`: Provides utility functions used across the application.
- `tests/`: Directory containing unit tests.
  - `test_calculations.py`: Unit tests for calculation functions.
- `assets/`: Directory for static assets.
  - `icons/`: Contains application icons.
- `build/`: Directory for build outputs.
- `dist/`: Directory for distribution files.
- `logs/`: Directory for log files.
- `output/`: Directory for generated output files.
- `scripts/`: Directory for utility scripts.
  - `build_exe.py`: Script for building executable.
  - `test_moomoo_api.py`: Script for testing Moomoo API integration.
  - `update_readme.py`: Script for updating README files.
- `.github/workflows/`: Contains GitHub Actions workflow configurations.
- `config.ini`: Configuration file storing application settings.
- `CHANGELOG.md`: Detailed version history and updates.
- `LICENSE`: License file for the project.
- `README.md`: Main project documentation in English.
- `README-zh-CN.md`: Chinese version of the project documentation.
- `userconfig.ini.template`: Template for user-specific configuration.
- `requirements.txt`: List of Python package dependencies.
- `version.py`: Central file for version management and update checking.

## Build Instructions

To build a standalone executable, follow these steps:

1. Ensure you have Python 3.7 or higher installed on your system.
2. Open a command prompt and navigate to the project root directory.
3. Run the following command:
```
python scripts/build_exe.py
```
4. Once the build is complete, the executable will be located in the `dist` directory.


## Installation

### For Windows Users

1. Go to the [Releases](https://github.com/znhskzj/grid-trading-plan-calculator/releases) page.
2. Download the latest `.exe` file.
3. Double-click the downloaded file to run the application.

### For Developers

If you want to run the script from source or contribute to the project:

1. Ensure you have Python 3.7 or higher installed.
2. Clone the repository:
git clone https://github.com/znhskzj/grid-trading-plan-calculator.git
3. Navigate to the project directory:
cd grid-trading-plan-calculator
4. Create a virtual environment:
python -m venv venv
5. Activate the virtual environment:
- On Windows: `venv\Scripts\activate`
- On macOS and Linux: `source venv/bin/activate`
6. Install required packages:
pip install -r requirements.txt
7. Run the script:
python grid_trading_plan.py

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

- The tool now supports both real and simulated trading environments.
- You can switch between US and HK markets in the Moomoo settings.
- Always test your API connection before performing any operations.
- Ensure your Moomoo account has the necessary permissions for the operations you wish to perform.

### Example Usage

Let's say you want to create a grid trading plan for Apple (AAPL) stock:

1. Launch the application.
2. Click "Common Stocks" and then click "AAPL".
3. The current price of AAPL will be fetched automatically (let's say it's $150).
4. Input the following:
   - Available Funds: 10000 (assuming you want to invest $10,000)
   - Initial Price: 150 (auto-filled from the fetched price)
   - Stop Loss Price: 140 (you decide to cut losses if the price drops to $140)
   - Number of Grids: 5 (you want 5 price levels in your grid)
5. Select "Proportional" as the allocation method.
6. Click "Calculate Purchase Plan".
7. The result will show you 5 price levels between $140 and $150, with more funds allocated to grids closer to $150.
8. If you're satisfied with the plan, click "Save as CSV" to export it.
9. API Selection: In the main window, you can now choose between Yahoo Finance and Alpha Vantage APIs for stock data retrieval.
10. Saving Preferences: Your API choice and frequently used stocks are now automatically saved for future sessions.

### Example Usage with Trading Instruction

Let's say you want to create a grid trading plan for SOXL stock based on a trading instruction:

1. Launch the application.
2. In the "Trading Instruction" field, enter: "日内SOXL 现价到30之间分批入，压力31.5，止损29.5"
3. Click "Calculate Purchase Plan".
4. The application will parse the instruction, fetch the current price if available, and generate a plan based on the instruction.
5. The result will show you the parsed information, including the stock symbol, price range, and stop-loss price.
6. If there are any discrepancies between the instruction and current market prices, you'll see a warning.
7. The grid trading plan will be generated based on this information.
8. If you're satisfied with the plan, click "Save as CSV" to export it.

## Configuration

The `config.ini` file in the project root contains default settings and common stocks. You can modify this file to customize the application's default behavior and add or remove common stocks.
The `config.ini` file now includes API settings. You can choose between Yahoo Finance and Alpha Vantage for stock price fetching. If you choose Alpha Vantage, you need to provide an API key.

### Example Configuration

Here's an example of what your `config.ini` might look like:

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
## Upcoming Features

- User-specific configuration file for personalized settings
- Customizable automatic update checks based on user preferences
- Integration with Moomoo trading platform for real-time trading capabilities

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

If you encounter any problems, please file an issue along with a detailed description.

For detailed release notes, please see the [Changelog](CHANGELOG.md).