# Grid Trading Plan Calculator

Version: 1.3.3
Author: Rong Zhu
Date: August 1, 2024

## Description

The Grid Trading Plan Calculator is a user-friendly tool with a graphical interface for creating and visualizing grid trading strategies. It allows users to input parameters such as total funds, initial price, stop-loss price, number of grids, and allocation method to generate a customized grid trading plan.

## Features

- Multiple allocation methods: Equal amount, Proportional, and Linear weighted
- Configuration saving and loading
- CSV export of trading plans
- Logging for debugging and auditing

## Project Structure

- `grid_buying_plan_gui.py`: Main program file containing GUI implementation and core logic.
- `app_icon.ico`: Application icon file.
- `config.json`: Configuration file storing user's default settings.
- `Grid Trading Plan Calculator.spec`: PyInstaller specification file for building the executable.
- `grid_trading.log`: Log file recording program runtime information.
- `LICENSE`: Project license file.
- `README.md`: Project readme file (English version).
- `README-zh-CN.md`: Project readme file (Chinese version).
- `requirements.txt`: List of Python package dependencies.

### scripts directory
- `build_exe.py`: Script for building standalone executable.

### dist directory
- `Grid Trading Plan Calculator.exe`: Built executable file.

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

1. Go to the [Releases](https://github.com/yourusername/grid-trading-plan-calculator/releases) page.
2. Download the latest `.exe` file.
3. Double-click the downloaded file to run the application.

### For Developers

If you want to run the script from source or contribute to the project:

1. Ensure you have Python 3.7 or higher installed.
2. Clone the repository:
git clone https://github.com/yourusername/grid-trading-plan-calculator.git
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

## Changelog

### Version 1.3.3 (August 1, 2024)
- Enhanced calculation process stability
- Improved timeout handling mechanism
- Optimized state management for calculation threads
- Added more detailed logging for better troubleshooting
- Fixed an issue where the calculation would sometimes incorrectly report as timed out even after completion
- Resolved a problem with the GUI not updating properly after calculation
- Corrected the behavior of buttons during and after calculation

### Version 1.3.2 (August 1, 2024)
- Fixed a critical bug in the equal amount allocation method that could cause infinite loops
- Optimized the calculation logic for all allocation methods to ensure more accurate results
- Removed automatic recalculation when changing allocation methods to prevent unintended updates
- Enhanced error handling and logging for better debugging and user experience
- Simplified allocation method descriptions in the GUI for better clarity
- Retained detailed explanations of allocation methods in the results display
- Added more comprehensive logging throughout the calculation process

### Version 1.3.1 (July 31, 2024)
- Improved equal amount allocation algorithm for more uniform fund distribution across price points
- Enhanced descriptions for exponential and linear weighted allocations for better differentiation
- Added display of actual purchase amount for each grid to improve data accuracy
- Refined explanations of characteristics and effects for different allocation methods
- Minor bug fixes and performance improvements

### Version 1.3.0 (July 31, 2024)
- Improved input validation and error handling
- Added real-time input validation
- Implemented "Reset to Default" button
- Using StringVar for better input management
- Enhanced user experience with more informative error messages

### Version 1.2.0 (July 31, 2024)
- Added reserved funds feature with new "Calculate with 10% Reserve" and "Calculate with 20% Reserve" buttons
- Enhanced calculation result display, including average purchase price and maximum potential loss
- Improved CSV export functionality, resolving Chinese character encoding issues and ensuring all important information is saved
- Fixed multiple bugs, improving overall program stability
- Optimized user interface with improved button layout

### Version 1.1.0 (July 30, 2024)
- Enhanced calculation of purchasable shares based on total funds and initial price
- Improved "proportional allocation" method to ensure at least 1 share per grid
- Added more input validations for numerical values
- Added vertical scrollbar for result display when there are many grids
- Set tab order for input fields to improve user experience

### Version 1.0.0 (July 26, 2024)
- Initial release
- Implemented basic grid trading plan calculation
- Added GUI with tkinter
- Implemented multiple allocation methods: Equal amount, Proportional, and Linear weighted
- Added configuration saving and loading
- Implemented CSV export of trading plans
- Added logging for debugging and auditing