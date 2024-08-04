# Grid Trading Plan Calculator

Version: {VERSION}
Author: {AUTHOR}
Date: {DATE}

## Description

The Grid Trading Plan Calculator is a powerful tool with a user-friendly graphical interface for creating, visualizing, and managing grid trading strategies. It enables users to input parameters such as total funds, initial price, stop-loss price, number of grids, and allocation method to generate a customized grid trading plan.

## Features

- Multiple allocation methods: Equal amount, Proportional, and Linear weighted
- Real-time stock price fetching for common stocks
- Dynamic status updates during calculations
- Configuration saving and loading
- CSV export of trading plans
- Comprehensive logging for debugging and auditing
- User-friendly GUI with intuitive layout

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
- `version.py`: Central file for version management.
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

1. Launch the application.
2. Input your trading parameters.
3. Click "Calculate" to generate the grid trading plan.
4. Use "Save as CSV" to export the results if needed.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

If you encounter any problems, please file an issue along with a detailed description.

For detailed release notes, please see the [Changelog](CHANGELOG.md).