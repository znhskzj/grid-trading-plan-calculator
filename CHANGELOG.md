# Changelog

All notable changes to this project will be documented in this file.

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

