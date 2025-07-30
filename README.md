# OpenAutomate

## Table of Contents
1.  [About OpenAutomate](#about-openautomate)
2.  [Why This Script?](#why-this-script)
3.  [Features](#features)
4.  [Data Privacy & Security Disclaimer](#data-privacy--security-disclaimer)
5.  [Getting Started](#getting-started)
    * [Prerequisites](#prerequisites)
    * [Installation](#installation)
    * [Initial Setup](#initial-setup)
6.  [Usage](#usage)
    * [Running the Script](#running-the-script)
    * [Operation Modes & Hotkeys](#operation-modes--hotkeys)
    * [Reactive Refinement](#reactive-refinement)
    * [Template Management](#template-samples)
7.  [Configuration](#configuration)
8.  [Troubleshooting](#troubleshooting)
9.  [Contributing](#contributing)
10. [License](#license)
11. [Acknowledgements](#acknowledgements)

## 1. About OpenAutomate

OpenAutomate is a powerful, free, and open-source Python script designed to automate repetitive on-screen interactions using advanced image recognition. It intelligently identifies and clicks elements based on visual templates, making it exceptionally useful for tasks like automatically declining cookie banners, dismissing pop-ups, or navigating repetitive UI elements.

Re-written from the ground up to be more accurate and reliable than many proprietary alternatives, this script aims to provide a robust, transparent, and malware-free automation solution for your daily digital tasks.

## 2. Why This Script?

Many commercial "automation" tools come with hefty price tags and often hide malicious components or collect user data without consent. This script was created to directly address these issues, offering a superior alternative:

* **Completely Free & Open-Source:** No hidden costs, no subscriptions. The entire codebase is transparent and auditable.
* **Malware-Free:** Developed with security in mind. You can inspect every line of code to ensure it's clean and safe.
* **High Accuracy:** Leveraging modern image processing techniques, OpenAutomate boasts improved accuracy in recognizing target elements on your screen.
* **Community-Driven:** Built to empower users and encourage collaborative improvements.

Say goodbye to expensive, untrustworthy software and take control of your automation needs!

## 3. Features

* **Image-Based Recognition:** Locates and interacts with on-screen elements using user-defined image templates.
* **Auto-Training Mode (F12):** Automatically refines existing templates based on your manual clicks, improving their accuracy over time.
* **New Template Training Mode (F9):** Quickly create new templates by performing a series of clicks on the desired element. The script intelligently groups similar clicks and generates a new template.
* **Reactive Refinement:** If the auto-clicker nearly matches a template but doesn't click, and you manually click that exact spot shortly after, the script will prompt you to refine the template using the current screen image.
* **Customizable Settings:** Adjust various parameters like confidence thresholds, click delays, and training counts through a convenient in-app settings menu or by editing `config.json`.
* **Local Operation:** All data (templates, screenshots, recordings) is stored only on your local machine.
* **Cross-Platform Compatibility:** Works on Windows, macOS, and Linux (requires X11 for Linux).

## 4. Data Privacy & Security Disclaimer

**IMPORTANT: This script operates entirely locally on your computer.**

**NO** data (templates, screenshots, click recordings, or any other personal information) is ever collected, transmitted, or shared online with anyone. All files generated and used by this script are stored only on your local disk within the script's directory structure. Your privacy and security are paramount.

## 5. Getting Started

### Prerequisites

* **Python 3.x:** Download and install Python from [python.org](https://www.python.org/downloads/).
* **Operating System-Specific Dependencies:**
    * **Windows:** No additional OS-level dependencies are typically required for `pyautogui` or `pynput`.
    * **macOS:** `pyautogui` and `pynput` may require **Accessibility** and **Input Monitoring** permissions in your System Settings > Security & Privacy > Privacy. You will usually be prompted by macOS when the script tries to control your mouse/keyboard or take screenshots for the first time. Grant these permissions to your terminal application (e.g., Terminal, iTerm2) or Python IDE.
    * **Linux:**
        * **Python Tkinter:** Often needed for `pyautogui`'s screenshot capabilities and other GUI interactions. Install using your distribution's package manager (e.g., `sudo apt-get install python3-tk` on Debian/Ubuntu, `sudo yum install python3-tkinter` on Fedora/RHEL, `sudo pacman -S tk` on Arch Linux).
        * **Screenshot Tool:** `pyautogui` relies on a screenshot utility. Install either `scrot` (recommended for speed) or `gnome-screenshot`.
            * For `scrot`: `sudo apt-get install scrot` (Debian/Ubuntu), `sudo pacman -S scrot` (Arch), `sudo dnf install scrot` (Fedora).
            * For `gnome-screenshot`: `sudo apt-get install gnome-screenshot` (Debian/Ubuntu).

### Installation

1.  **Clone the repository (or download the script):**
    ```bash
    git clone [https://github.com/MrCookie-for-Programmers/openautomate.git](https://github.com/MrCookie-for-Programmers/openautomate.git)
    cd openautomate
    ```

2.  **Create a virtual environment (Highly Recommended for All OSes):**
    A virtual environment creates an isolated space for this project's Python dependencies, preventing conflicts with other Python projects or your system's Python installation. This is a best practice regardless of your operating system.
    ```bash
    python -m venv venv
    ```

3.  **Activate the virtual environment:**
    * **Windows (Command Prompt/PowerShell):**
        ```bash
        .\venv\Scripts\activate
        ```
    * **macOS/Linux (Bash/Zsh):**
        ```bash
        source venv/bin/activate
        ```

4.  **Install the required Python packages:**
    ```bash
    pip install pyautogui Pillow pynput
    ```

### Initial Setup

Upon the first run, the script will automatically create the following directories in the same location as the script file:
* `templates/`: Store your `.png` image templates here.
* `screenshots/`: Debug screenshots of successful matches will be saved here.
* `recordings/`: Temporary images captured during training modes are stored here.
* `config.json`: A configuration file will be generated with default settings. You can modify this file directly or use the in-app settings menu.

## 6. Usage

### Running the Script

Navigate to the script's directory in your terminal (with your virtual environment activated) and run:
```bash
python thing.py
Operation Modes & Hotkeys
The script provides several modes to enhance its functionality:

Auto-Click Mode (Default):

Continuously scans the screen for loaded templates and performs clicks when a match is found.

New Template Training Mode (Press F9 to toggle):

When enabled, your manual left-clicks will be recorded.

Click on the same visual element 5 times. The script will then automatically create a new .png template from the first recorded click of that group and save it to the templates/ folder.

Useful for quickly adding new elements you want to automate.

Auto-Train Mode (Press F12 to toggle):

When enabled, your manual left-clicks will be analyzed.

If a manual click is sufficiently similar to an existing template (default: 2 hits), that template will be automatically refined/updated using a new screenshot from the clicked area.

This helps keep your templates up-to-date with minor UI changes.

This mode runs alongside the default Auto-Click Mode.

Settings Menu (Press F11 to enter):

Pauses automation and allows you to view and modify various script parameters (e.g., PYAUTOGUI_CONFIDENCE_INITIAL, CHECK_INTERVAL_SECONDS, etc.).

Changes are saved to config.json. Press e or ESC to exit the menu and resume automation.

Exit Script (ESC or Mouse to Top-Left):

Press the ESC key at any time to gracefully stop the script.

Alternatively, move your mouse cursor to the absolute top-left corner of your screen (coordinates 0,0) to trigger PyAutoGUI's failsafe and terminate the script.

Reactive Refinement
This is a smart feature to help maintain template accuracy:

If the auto-clicker finds a "near-miss" match for a template (i.e., it's quite similar but not confident enough to click), it will remember this location.

If you then manually click within that near-miss region shortly after the scan, the script will prompt you whether you want to use your manual click's context to refine and update the corresponding template. This helps quickly correct templates that might be slightly outdated.

Template Management
Adding Templates: Place new .png image files representing the elements you want to click into the templates/ directory. The script will load them automatically on startup.

Updating Templates: Use the Auto-Train mode or Reactive Refinement. You can also manually replace the .png file in the templates/ folder.

Removing Templates: Simply delete the .png file from the templates/ directory.

7. Configuration
All configurable parameters are stored in config.json. This file is automatically created with default values on the first run. You can modify these values through the in-app settings menu (F11) or by directly editing the config.json file with a text editor.

Key configurable parameters include:

RESIZE_DIMENSIONS_WIDTH, RESIZE_DIMENSIONS_HEIGHT: Dimensions templates are resized to for comparison.

MAX_COLOR_DISTANCE: Threshold for color similarity in block comparisons.

MATCH_BLOCK_THRESHOLD: Percentage of matching color blocks required for a full match.

PYAUTOGUI_CONFIDENCE_INITIAL: Initial confidence level for PyAutoGUI's locateOnScreen.

CHECK_INTERVAL_SECONDS: How long the script waits between screen scans.

NEW_TEMPLATE_TRAINING_CLICK_COUNT_THRESHOLD: Number of clicks needed to create a new template.

And more, all detailed within the config.json file.

8. Troubleshooting
Script not starting/PyAutoGUI errors:

Ensure all prerequisites are met, especially Python 3.x and the required packages (pip install pyautogui Pillow pynput).

Linux Specific: Ensure python3-tk and a screenshot tool (scrot or gnome-screenshot) are installed. Refer to Prerequisites for installation commands.

Ensure your virtual environment is activated.

Templates not being found:

Verify that your .png templates are placed directly in the templates/ directory.

Ensure the images are clear and distinct representations of what you want to click.

Try adjusting PYAUTOGUI_CONFIDENCE_INITIAL or MATCH_BLOCK_THRESHOLD in the settings menu.

Script stopping unexpectedly:

Check for PyAutoGUI Fail-Safe messages (mouse to top-left corner).

Review the console output for any error messages (e.g., ImageNotFoundException, TypeError).

Mouse/Keyboard Listener issues (pynput related):

macOS Specific: pynput requires Accessibility and Input Monitoring permissions. Go to your System Settings > Security & Privacy > Privacy (or System Preferences on older macOS versions), find Accessibility and Input Monitoring, and ensure your terminal application (e.g., Terminal, iTerm2) or the Python IDE you are using is checked. You might need to restart your terminal/IDE after granting permissions.

Linux Specific: On some Wayland compositors, pynput might have limitations with global listeners. X11 is generally more compatible and recommended for full functionality.

General: Ensure no other applications are interfering with global input hooks.

9. Contributing
Contributions are highly welcome! Whether it's bug reports, feature suggestions, code improvements, or new templates, your help makes this project better.

Fork the repository.

Create your feature branch (git checkout -b feature/AmazingFeature).

Commit your changes (git commit -m 'Add some AmazingFeature').

Push to the branch (git push origin feature/AmazingFeature).

Open a Pull Request.

10. License
This project is licensed under the MIT License - see the LICENSE file for details. (You will need to create a LICENSE file in your repository's root, typically with the MIT license text.)

11. Acknowledgements
PyAutoGUI for GUI automation.

Pillow for image processing.

Pynput for keyboard and mouse listening.

The open-source community for inspiration and collaboration.
