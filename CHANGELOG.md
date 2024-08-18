# Changelog.md

All notable changes to this project will be documented in this file.

## [1.5.6] - 2024-08-18

### Added
- Implemented functionality to query available funds and stock positions using Moomoo API.
- Added detailed display of stock positions, including quantity, market value, and profit/loss percentage.

### Changed
- Refined the display format for stock positions to improve readability and information clarity.
- Updated the `query_positions` method to provide a more comprehensive overview of the portfolio.

### Improved
- Enhanced the layout of stock position information, including right-aligned numerical data and appropriate decimal precision.
- Optimized the display of large numbers with thousand separators for better readability.

### Fixed
- Resolved issues with displaying incomplete stock position information.
- Fixed formatting inconsistencies in the results display area.

### Others
- Updated error handling and logging for Moomoo API-related functions.
- Refined user feedback messages for API queries and connection status.

## [1.5.5] - 2024-08-17

### Added
- Integrated Moomoo API settings and connection test functionality in the GUI.
- Implemented new fund allocation display, showing total funds, reserved funds, and available funds.
- Added support for different trading environments (real and simulated) and markets (US and HK) in Moomoo settings.

### Changed
- Refactored calculation logic to accommodate reserved funds functionality.
- Updated GUI layout to include Moomoo settings alongside allocation method and API choice.
- Modified the reset to default function to preserve common stocks and Moomoo settings.

### Improved
- Enhanced error handling in API connection tests and configuration management.
- Optimized the display of calculation results with more detailed fund breakdowns.
- Improved user feedback for Moomoo API connection status, including specific environment and market information.

### Fixed
- Resolved encoding issues when saving and loading user configuration files.
- Fixed bugs related to resetting default values and handling of user preferences.

### Others
- Updated error logging to provide more detailed information for troubleshooting.
- Refined the structure of the user configuration file to include Moomoo settings.
- Updated documentation to reflect new Moomoo API integration and usage instructions.

## [1.5.4] - 2024-08-14

### Added
- Integrated Moomoo API for real-time trading capabilities.
- Added user-specific configuration file (userconfig.ini) for personalized settings.
- Implemented automatic saving and loading of user preferences.
- Added a new UserConfigWindow for easier configuration of API settings and allocation methods.

### Changed
- Refactored API management to support both Yahoo Finance and Alpha Vantage APIs.
- Updated GUI to dynamically adjust based on user's screen resolution.
- Modified common stocks display to use user-specific settings.
- Improved error handling and user feedback for API-related operations.

### Fixed
- Resolved issues with API switching and key management.
- Fixed a bug where the API choice was not properly updated after switching.
- Corrected the display of multiple Alpha Vantage options in the API selection.

### Improved
- Enhanced the robustness of configuration loading and saving processes.
- Optimized the layout of the main application window for better user experience.
- Improved error logging and status updates for better troubleshooting.

### Others
- Updated documentation to reflect new features and changes.
- Removed unused gen_md5.py script from the scripts directory.
- Updated requirements.txt to include new dependencies for Moomoo API integration.

## [1.5.3] - 2024-08-07

### Added
- Implemented trade instruction parsing functionality, supporting multiple formats of instruction input.
- Added a new trade instruction input field in the GUI for easier input of trading instructions.
- Added price tolerance checks, providing warnings when there is a significant difference between instruction price and actual price.
- Introduced automatic stop-loss price adjustment, ensuring the stop-loss price is always below the current price.
- Added a fallback solution using the instruction price when the API price is unavailable.

### Changed
- Refactored the `parse_trading_instruction` function, improving the accuracy and flexibility of instruction parsing.
- Optimized the `process_instruction` method, enhancing error handling and user feedback.
- Adjusted the price display format to clearly indicate the source of the price and the stop-loss price calculation method.
- Improved the instruction input handling logic in the GUI, enhancing user experience.
- Updated `config.py` to optimize configuration loading and saving processes.

### Fixed
- Resolved an issue where the stop-loss price being higher than the initial price caused validation failure in some cases.
- Fixed a crash issue when the program could not retrieve the price of specific stocks (e.g., SOXL).
- Addressed the issue of instruction parsing not matching the actual price.
- Fixed the problem of duplicate display of common stocks in the GUI.

### Improved
- Enhanced error logging, providing more detailed fault diagnostic information.
- Optimized the exception handling process when API price retrieval fails.
- Improved user interface feedback, providing clearer information when processing complex instructions.
- Enhanced `build_exe.py` script to include version number in the executable file name.

### Others
- Updated test cases to cover more instruction parsing scenarios.
- Improved code comments, enhancing code readability and maintainability.
- Updated user documentation, adding instructions for the new trade instruction features.
- Updated GitHub Actions workflow to ensure consistency with local build process.
- Updated `requirements.txt` to include all necessary dependencies for the project.


## [1.5.2] - 2024-08-06

### Added
- Integrated multi-API support, allowing switching between Yahoo Finance and Alpha Vantage
- Implemented automatic fallback to alternative APIs, improving the success rate of stock price retrieval
- Added functionality to save user API preferences and frequently used stock lists
- Introduced automatic display of selected stock during calculations

### Changed
- Refactored the API management module, enhancing extensibility and stability
- Optimized configuration loading and saving mechanisms, adding support for user-specific settings
- Improved the layout for allocation method display, enhancing UI aesthetics
- Enhanced information display in status bar and result area, providing clearer operational feedback
- Restructured the project to better align with standard Python package structures

### Fixed
- Resolved issues with "Calculate with 10% Reserve" and "Calculate with 20% Reserve" functions
- Fixed import errors when running calculations.py directly
- Addressed potential Tkinter object access errors during program exit

### Improved
- Optimized the code structure of the calculation module, improving readability and maintainability
- Enhanced error handling and logging capabilities for better issue diagnosis
- Improved exception handling mechanisms, providing more detailed and useful error information
- Optimized data processing and calculation procedures, increasing overall operational efficiency

### Others
- Updated code comments and docstrings, improving code readability
- Added type hints to major functions and classes, enhancing code maintainability
- Prepared foundational infrastructure for future feature expansions, such as real-time notifications and automatic order placement
- Updated README documentation to reflect new features and improvements


## [1.5.1] - 2024-08-06

### Added
- Implemented automatic update checking mechanism
- Added functionality to download and install updates automatically
- Introduced version comparison utility for update management
- Created centralized version.py file for improved version control

### Changed
- Updated GitHub Actions workflow to align with new version management approach
- Enhanced error handling and logging in utility functions
- Refactored version management to use the new version.py file
- Improved configuration handling to support future user-specific settings

### Fixed
- Resolved issues with version comparison logic in GitHub Actions workflow
- Corrected update URL construction for more reliable update downloads
- Fixed potential conflicts between project and user configurations

### Others
- Improved exception handling in utility functions for better error tracking
- Updated documentation (README.md and README-zh-CN.md) to reflect new automatic update feature and upcoming features
- Enhanced modularity of version-related functions for easier maintenance
- Prepared groundwork for future separation of project and user configurations

## [1.5.0] - 2024-08-05

### Added
- Implemented dynamic common stock buttons in the left panel
- Added real-time stock price fetching for selected stocks
- Introduced a status bar for live feedback and error messages

### Changed
- Enhanced GUI layout with better organization of widgets
- Improved error handling and user feedback throughout the application
- Optimized the process of displaying and hiding common stocks

### Fixed
- Resolved issues with repeated stock button creation
- Fixed status bar update mechanism
- Corrected stock price display in the input field

### Others
- Refactored code for better modularity and maintainability
- Updated error logging for more comprehensive debugging
- Improved configuration handling for common stocks
- Enhanced unit tests for better coverage and reliability
- Optimized mock objects in test environment for more accurate simulation of GUI behavior
- Resolved warnings related to mock objects in testing scenarios

## [1.4.3] - 2024-08-04

### Added
- Implemented a status bar for real-time feedback during calculations
- Added common stocks feature for quick stock selection and price fetching

### Changed
- Enhanced error handling and logging in the main application
- Optimized GUI layout for better user experience
- Implemented StatusManager for centralized status updates
- Resolved circular import issues for improved code structure

### Fixed
- Fixed issues with stock price fetching from Yahoo Finance
- Corrected calculation status updates in various functions

### Others
- Refactored code to use StatusManager, improving modularity
- Updated configuration handling to be more robust
- Improved exception handling throughout the application

## [1.4.2] - 2024-08-04

### Added
- Version number to the application title
- "Common Stocks" feature for quick stock selection
- Prepared for future integration with trading APIs

### Changed
- Improved UI layout with better alignment and spacing
- Centralized version management in a single file
- Enhanced GitHub Actions workflow for automated releases

### Fixed
- Minor UI alignment issues
- Error handling in stock price fetching

## [1.4.1] - 2024-08-04
- Fixed: Resolved an issue with locale settings in the version comparison step, improving workflow stability.
- Minor Version Updates: Implemented logic to trigger releases only for minor version updates (e.g., 1.4.0 to 1.5.0) rather than patch updates (e.g., 1.4.0 to 1.4.1).
- Directory Display in README: Updated the README to display the directory and file structure in plaintext for better clarity on GitHub.

## [1.4.0] - 2024-08-04
- Major code refactoring: Implemented modular structure with src directory
- Introduced pytest framework with comprehensive unit tests
- Upgraded configuration management from JSON to INI format
- Enhanced error handling and logging system
- Optimized project directory structure
- Updated build script to accommodate new project layout
- Improved code organization and maintainability

## [1.3.5] - 2024-08-03
- Major code refactoring for improved modularity and maintainability
- Separated GUI, calculation logic, and configuration management into distinct modules
- Enhanced error handling and logging throughout the application
- Improved type hinting for better code readability and IDE support
- Prepared structure for future API integrations
- Updated build process to accommodate new modular structure

## [1.3.4] - 2024-08-02
- Code Structure Optimization: Reorganized function order for improved clarity and logical structure.
- PEP 8 Compliance: Adjusted code formatting to adhere to Python's PEP 8 coding standards.
- Logging System Improvement: Replaced most print statements with the logging module for better control over log output levels and formats.
- Enhanced Error Handling: Added more exception handling and user-friendly error messages.
- Performance Optimization: Optimized calculation processes and added timeout mechanisms.
- Improved Code Readability: Added more comments to make the code easier to understand and maintain.
- Configuration Management Improvement: Optimized the loading and saving of configurations.
- GUI Interaction Enhancement: Improved button state management for a better user interaction experience.
- Optimized proportional allocation algorithm for more pronounced exponential growth.

## [1.3.3] - 2024-08-01
- Enhanced calculation process stability
- Improved timeout handling mechanism
- Optimized state management for calculation threads
- Added more detailed logging for better troubleshooting
- Fixed an issue where the calculation would sometimes incorrectly report as timed out even after completion
- Resolved a problem with the GUI not updating properly after calculation
- Corrected the behavior of buttons during and after calculation

## [1.3.2] - 2024-08-01
- Fixed a critical bug in the equal amount allocation method that could cause infinite loops
- Optimized the calculation logic for all allocation methods to ensure more accurate results
- Removed automatic recalculation when changing allocation methods to prevent unintended updates
- Enhanced error handling and logging for better debugging and user experience
- Simplified allocation method descriptions in the GUI for better clarity
- Retained detailed explanations of allocation methods in the results display
- Added more comprehensive logging throughout the calculation process

## [1.3.1] - 2024-07-31
- Improved equal amount allocation algorithm for more uniform fund distribution across price points
- Enhanced descriptions for exponential and linear weighted allocations for better differentiation
- Added display of actual purchase amount for each grid to improve data accuracy
- Refined explanations of characteristics and effects for different allocation methods
- Minor bug fixes and performance improvements

## [1.3.0] - 2024-07-31
- Improved input validation and error handling
- Added real-time input validation
- Implemented "Reset to Default" button
- Using StringVar for better input management
- Enhanced user experience with more informative error messages

## [1.2.0] - 2024-07-31
- Added reserved funds feature with new "Calculate with 10% Reserve" and "Calculate with 20% Reserve" buttons
- Enhanced calculation result display, including average purchase price and maximum potential loss
- Improved CSV export functionality, resolving Chinese character encoding issues and ensuring all important information is saved
- Fixed multiple bugs, improving overall program stability
- Optimized user interface with improved button layout

## [1.1.0] - 2024-07-30
- Enhanced calculation of purchasable shares based on total funds and initial price
- Improved "proportional allocation" method to ensure at least 1 share per grid
- Added more input validations for numerical values
- Added vertical scrollbar for result display when there are many grids
- Set tab order for input fields to improve user experience

## [1.0.0] - 2024-07-26
- Initial release
- Implemented basic grid trading plan calculation
- Added GUI with tkinter
- Implemented multiple allocation methods: Equal amount, Proportional, and Linear weighted
- Added configuration saving and loading
- Implemented CSV export of trading plans
- Added logging for debugging and auditing

