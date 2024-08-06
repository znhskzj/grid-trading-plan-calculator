# Grid Trading Plan Calculator

Version: {VERSION}
Author: {AUTHOR}
Date: {DATE}

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

## Project Structure

### Directory and File Structure
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

### Main File Descriptions:
- `grid_trading_app.py`: Main entry point of the application.
- `src/`: Directory containing core application modules.
- `tests/`: Directory containing unit tests.
- `assets/`: Directory for static assets like icons.
- `logs/`: Directory for log files.
- `scripts/`: Directory for utility scripts like the build script.
- `config.ini`: Configuration file storing user's default settings.
- `CHANGELOG.md`: Detailed version history and updates.
- `version.py`: Central file for version management and update checking.
- `requirements.txt`: List of Python package dependencies.
- `LICENSE`: License file.
- `README.md`: Main project documentation.
- `README-zh-CN.md`: Chinese version of the documentation.

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
   - The right panel contains input fields and control buttons.

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

6. Click "Calculate Purchase Plan" to generate the grid trading plan.

7. View results in the text area below:
   - The plan will show each grid's price level and the amount to invest at that level.

8. Additional options:
   - "Calculate with 10% Reserve" or "Calculate with 20% Reserve": Generates a plan while keeping a portion of funds in reserve.
   - "Save as CSV": Exports the current plan to a CSV file for further analysis or record-keeping.
   - "Reset to Default Values": Resets all input fields to their default values from the configuration.

9. Automatic Updates:
   - The application will periodically check for updates.
   - If an update is available, you will be prompted to download and install it.

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

## Configuration

The `config.ini` file in the project root contains default settings and common stocks. You can modify this file to customize the application's default behavior and add or remove common stocks.

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