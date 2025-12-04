import os
import subprocess
import sys
import time
import threading
import platform
# NOTE: The core modules (cv2, numpy, pyautogui, keyboard, etc.) 
# are imported dynamically within the install_and_import_dependencies() function.


# --- INSTRUCTIONS ---

INSTRUCTIONS = """
*******************************************************************************
                 SMART DESKTOP AI CONTROLS & MODES
*******************************************************************************
The AI runs in the background, constantly monitoring the screen.

Mode Hotkeys (F-Keys):
---------------------
F8: TOGGLE QUIET MODE
    - Hides non-critical prints (including FORBIDDEN APP WARNINGS).
    - ALWAYS prints: Clicks, Confidence increases, and Mode changes.

F9: LEARNING_ONLY Mode 
    - AI does NOT click anything.
    - AI ONLY learns by monitoring your mouse clicks.

F10: CLICK_ONLY Mode (Default)
    - AI ONLY clicks templates from 'user_priority' and 'learned' folders.

F11: BOTH Mode 
    - AI clicks AND monitors your clicks for learning.

F12: FORCE STOP
    - Halts the AI script and exits the program cleanly.

Ctrl + F9: CLEANUP LEARNED FOLDER
    - Manually triggers a scan of the 'learned/' folder to remove duplicates and forbidden templates.

Ctrl + F10: FORCE CLICK ACTION
    - Immediately triggers one scan/click cycle, prioritizing 'user_priority'.
    
Template Folders:
-----------------
templates/user_priority: Highest confidence templates. Always checked first.
templates/learned: Automatically generated templates (after 3 similar clicks).
templates/no_click: Templates the AI should detect but explicitly avoid clicking.
templates/temp_observed: Temporary storage for templates under review (deleted on exit).
*******************************************************************************
"""

# --- GLOBAL STATE AND CONFIGURATION ---

# Modules required for the AI core
REQUIRED_PACKAGES = [
    'opencv-python',
    'numpy',
    'mss',
    'pyautogui',
    'keyboard',
    'pynput',
    'psutil',
    'pywin32'
]

# State variables
CURRENT_MODE = 'CLICK_ONLY'
AI_RUNNING = True          
QUIET_MODE = False 

# Template folder paths
TEMPLATE_FOLDERS = {
    'user_priority': 'templates/user_priority', 
    'learned': 'templates/learned',             
    'no_click': 'templates/no_click'           
}

# New configuration for Confidence Learning
TEMP_OBSERVED_FOLDER = 'templates/temp_observed'
OBSERVED_TEMPLATES = {}
CONFIDENCE_THRESHOLD = 3 
HASH_TOLERANCE = 10      # Standard tolerance for learned-vs-learned duplicates
FORBIDDEN_HASH_TOLERANCE = 5 # Strict tolerance for learned-vs-no_click check

# Application Blacklist (Add your critical app executable names here, all lowercase)
FORBIDDEN_APPS = [
    'explorer.exe',
    'cmd.exe',
    'powershell.exe',
    'code.exe',          # Visual Studio Code
    'devenv.exe',        # Visual Studio
    'pycharm64.exe',     # PyCharm
    'steam.exe',         # Steam
    'notepad++.exe',
    'spotify.exe',       
    'update.exe',        
    'discord.exe'        
]


# --- 1. DEPENDENCY INSTALLER ---

def install_and_import_dependencies():
    """Attempts to import necessary modules and installs missing ones."""
    print("Starting dependency check and imports...")
    while True:
        try:
            # ATTEMPT IMPORTS (Assigning to global variables for broader use)
            global cv2, np, mss, pyautogui, keyboard, psutil, mouse, win32process, win32gui
            
            import cv2
            import numpy as np
            import mss
            import pyautogui
            import keyboard         
            import psutil
            from pynput import mouse 
            
            # --- Windows-specific Blacklist Imports ---
            try:
                import win32process, win32gui
            except ImportError:
                 # Install pywin32
                print("   Installing missing Windows API modules (pywin32)...")
                subprocess.check_call([sys.executable, "-m", "pip", "install", "pywin32"])
                # Re-import after successful installation
                import win32process, win32gui
                print("   Windows API modules successfully imported.")

            _ = cv2.img_hash.pHash # Check for pHash functionality

            print("✅ All dependencies successfully imported.")
            # Ensure all required folders exist
            for folder in TEMPLATE_FOLDERS.values():
                os.makedirs(folder, exist_ok=True)
            os.makedirs(TEMP_OBSERVED_FOLDER, exist_ok=True)
            
            return True 
            
        except ImportError as e:
            module_name = str(e).split()[-1].strip("'")
            print("-" * 50)
            print(f"🚨 Missing dependency detected: {module_name}")
            print("   Attempting automatic installation...")
            
            package_to_install = next((pkg for pkg in REQUIRED_PACKAGES if module_name in pkg or module_name == pkg.split('-')[0]), None)
            
            if package_to_install:
                try:
                    subprocess.check_call([sys.executable, "-m", "pip", "install", package_to_install])
                    print(f"   Successfully installed {package_to_install}.")
                    print("-" * 50)
                    time.sleep(2) 
                    
                except Exception as install_e:
                    print(f"\n❌ ERROR: Failed to install {package_to_install}. Please try running as Administrator.")
                    sys.exit(1)
            else:
                print(f"\n❌ CRITICAL ERROR: An unexpected import error occurred: {e}")
                sys.exit(1)
        except AttributeError:
             # Handle missing pHash
            print("\n🚨 cv2.img_hash.pHash not found. Reinstalling opencv-contrib-python...")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", "opencv-contrib-python", "--upgrade"])
                print("   Successfully installed opencv-contrib-python. Retrying imports...")
                time.sleep(2)
            except Exception as install_e:
                 print(f"\n❌ ERROR: Failed to install opencv-contrib-python. Details: {install_e}")
                 print("\n*** If this is an 'Access Denied' error, you must run your terminal/command prompt as Administrator. ***")
                 sys.exit(1)

# Perform initial dependency check and import modules
if not install_and_import_dependencies():
    sys.exit(1)


# --- 2. CORE VISION AND UTILITY FUNCTIONS ---

def capture_screen():
    """Captures the current primary monitor screenshot using mss."""
    with mss.mss() as sct:
        monitor = sct.monitors[1]
        sct_img = np.array(sct.grab(monitor))
        return cv2.cvtColor(sct_img, cv2.COLOR_BGRA2BGR)

def find_best_match(screenshot, folder_path, threshold=0.8):
    """Scans the screenshot against all templates in a given folder."""
    img_gray = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)
    best_match = (None, None, 0.0)

    for filename in os.listdir(folder_path):
        if not filename.endswith(('.png', '.jpg')):
            continue
        template_path = os.path.join(folder_path, filename)
        template = cv2.imread(template_path, 0)
        if template is None: continue

        w, h = template.shape[::-1]
        result = cv2.matchTemplate(img_gray, template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

        if max_val > best_match[2] and max_val >= threshold:
            center_x = max_loc[0] + w // 2
            center_y = max_loc[1] + h // 2
            best_match = ((center_x, center_y), filename, max_val)

    return best_match[0], best_match[1]

def click_at_center(center_coords):
    """Performs a mouse click at the given coordinates."""
    if center_coords:
        x, y = center_coords
        pyautogui.click(x, y)
        print(f"-> CLICKED at ({x}, {y})")
        return True
    return False

# --- 3. HASHING AND CONFIDENCE FUNCTIONS ---

def hash_image(image):
    """Generates a perceptual hash for an image."""
    # Ensure image is grayscale for hash calculation
    if len(image.shape) == 3:
        image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
    resized = cv2.resize(image, (64, 64))
    image_hash = cv2.img_hash.pHash(resized)
    return tuple(image_hash[0])

def compare_hashes(hash1, hash2, tolerance=HASH_TOLERANCE):
    """Compares two perceptual hashes using Hamming distance."""
    if len(hash1) != len(hash2):
        return False
    distance = 0
    for byte1, byte2 in zip(hash1, hash2):
        distance += bin(byte1 ^ byte2).count('1')
    return distance <= tolerance

# --- 4. APPLICATION BLACKLIST CHECK ---

def get_active_window_process():
    """Determines the executable name of the currently focused application (Windows-optimized)."""
    try:
        # Get the PID of the foreground window
        pid = win32process.GetWindowThreadProcessId(win32gui.GetForegroundWindow())[1]
        
        # Use psutil to get the process name from the PID
        process = psutil.Process(pid)
        return process.name().lower()
    except Exception:
        return None

def is_forbidden_app():
    """Checks if the active application is on the FORBIDDEN_APPS list."""
    active_process_name = get_active_window_process()
    if active_process_name and active_process_name in FORBIDDEN_APPS:
        return True
    return False

# --- 5. MODE AND KEYBOARD CONTROL ---

def set_mode(mode_name):
    """Updates the global mode and prints a status message."""
    global CURRENT_MODE
    global AI_RUNNING
    global QUIET_MODE
    
    if mode_name == 'TOGGLE_QUIET':
        QUIET_MODE = not QUIET_MODE
        print(f"\n*** QUIET MODE {'ENABLED' if QUIET_MODE else 'DISABLED'} ***")
        return

    if mode_name == 'FORCE_STOP':
        AI_RUNNING = False
        print("\n*** AI SYSTEM HALTED. EXITING... ***")
    else:
        CURRENT_MODE = mode_name
        print(f"\n*** AI MODE CHANGED TO: {mode_name} ***")
        
keyboard.add_hotkey('f8', set_mode, args=('TOGGLE_QUIET',), suppress=True) 
keyboard.add_hotkey('f9', set_mode, args=('LEARNING_ONLY',), suppress=True) 
keyboard.add_hotkey('f10', set_mode, args=('CLICK_ONLY',), suppress=True)  
keyboard.add_hotkey('f11', set_mode, args=('BOTH',), suppress=True)        
keyboard.add_hotkey('f12', set_mode, args=('FORCE_STOP',), suppress=True)  

def force_click_action():
    """Immediately scans for the highest priority button and clicks it."""
    if is_forbidden_app():
        # Suppress in Quiet Mode
        if not QUIET_MODE:
            print("FORCE CLICK blocked: Forbidden app is active.")
        return

    screenshot = capture_screen()
    
    target_center, target_template = find_best_match(screenshot, TEMPLATE_FOLDERS['user_priority'], threshold=0.9)
    
    if not target_center:
        target_center, target_template = find_best_match(screenshot, TEMPLATE_FOLDERS['learned'], threshold=0.85)

    if target_center:
        print(f"\n*** FORCE CLICK: Found {target_template} with high confidence! ***")
        click_at_center(target_center)
    else:
        print("\n*** FORCE CLICK: No high-priority target found. ***")

keyboard.add_hotkey('ctrl+f10', force_click_action, suppress=True)


# --- 6. CONFIDENCE-BASED LEARNING LOGIC ---

def on_click(x, y, button, pressed):
    """Handles click events for learning templates based on confidence."""
    global OBSERVED_TEMPLATES
    
    if pressed and CURRENT_MODE in ['LEARNING_ONLY', 'BOTH']:
        # If forbidden, return silently
        if is_forbidden_app(): 
            return

        # 1. Capture the Template (100x40 area around the click)
        w, h = 100, 40
        x1, y1 = max(0, x - w // 2), max(0, y - h // 2)
        x2, y2 = x1 + w, y1 + h
        
        with mss.mss() as sct:
            monitor_area = {'top': y1, 'left': x1, 'width': w, 'height': h}
            sct_img = np.array(sct.grab(monitor_area))
            template_img = cv2.cvtColor(sct_img, cv2.COLOR_BGRA2BGR)
            
        # 2. Get the Perceptual Hash
        current_hash = hash_image(template_img)
        found_match = False
        
        # 3. Check for Similarity in Temporary Templates
        for temp_hash, data in list(OBSERVED_TEMPLATES.items()):
            if compare_hashes(current_hash, temp_hash):
                # Found a similar match!
                data['count'] += 1
                OBSERVED_TEMPLATES[temp_hash] = data
                found_match = True
                
                # ALWAYS PRINT CONFIDENCE INCREASE
                print(f"Confidence increased for '{data['name']}': {data['count']}/{CONFIDENCE_THRESHOLD}")
                
                # CONFIDENCE REACHED
                if data['count'] >= CONFIDENCE_THRESHOLD:
                    # Promote the Template to 'learned' folder
                    temp_path = os.path.join(TEMP_OBSERVED_FOLDER, data['name'])
                    final_path = os.path.join(TEMPLATE_FOLDERS['learned'], data['name'])
                    os.rename(temp_path, final_path)
                    del OBSERVED_TEMPLATES[temp_hash]
                    
                    # ALWAYS PRINT PROMOTION
                    print(f"🎉 **CONFIDENCE REACHED!** Promoted '{data['name']}' to 'learned/' folder.")
                    
                    # Targeted Cleanup
                    clean_learned_templates()
                break 
        
        # 4. If No Match Found, Create New Temporary Entry
        if not found_match:
            timestamp = int(time.time())
            filename = f"learned_click_{timestamp}.png"
            save_path = os.path.join(TEMP_OBSERVED_FOLDER, filename)
            
            cv2.imwrite(save_path, template_img)
            
            OBSERVED_TEMPLATES[current_hash] = {
                'name': filename,
                'count': 1,
                'path': save_path 
            }
            # SUPPRESS THIS PRINT IN QUIET MODE
            if not QUIET_MODE:
                print(f"New observation recorded: {filename}")


# --- 7. CLEANUP LOGIC ---

def clean_learned_templates():
    """Scans the 'learned' folder and deletes older duplicates AND templates matching a 'no_click' item."""
    print("\n--- Starting Template Cleanup ---")
    deleted_count = 0
    learned_data = []
    
    # 1. Pre-load No-Click hashes for the forbidden check
    no_click_hashes = []
    for filename in os.listdir(TEMPLATE_FOLDERS['no_click']):
        path = os.path.join(TEMPLATE_FOLDERS['no_click'], filename)
        img = cv2.imread(path, 0)
        if img is not None:
            no_click_hashes.append(hash_image(img))
            
    # 2. Iterate Learned templates, checking against forbidden list first
    folder = TEMPLATE_FOLDERS['learned']
    
    for filename in os.listdir(folder):
        if not filename.endswith(('.png', '.jpg')): continue
        
        path = os.path.join(folder, filename)
        img = cv2.imread(path, 0) 
        if img is None: continue
        
        current_hash = hash_image(img)
        
        # Extract timestamp
        timestamp = 0 
        try:
            timestamp_str = filename.split('_')[-1].split('.')[0]
            timestamp = int(timestamp_str)
        except:
            pass 

        # --- FORBIDDEN CHECK (STRICT HASH COMPARISON) ---
        is_forbidden = False
        for forbidden_hash in no_click_hashes:
            # Use strict tolerance (5) for critical forbidden check
            if compare_hashes(current_hash, forbidden_hash, tolerance=FORBIDDEN_HASH_TOLERANCE):
                is_forbidden = True
                break
        
        if is_forbidden:
            try:
                os.remove(path)
                deleted_count += 1
                if not QUIET_MODE:
                    print(f"CLEANUP: Deleted forbidden learned template '{filename}' (Identical to a No-Click template).")
            except Exception as e:
                print(f"CLEANUP ERROR: Could not delete forbidden template {filename}. {e}")
            continue # Skip adding this template to the learned_data list if deleted
            
        # If not forbidden, add to the list for duplicate checking
        learned_data.append({
            'name': filename,
            'path': path,
            'hash': current_hash,
            'timestamp': timestamp,
            'deleted': False
        })


    # 3. Duplicate Cleanup (Learned-vs-Learned)
    original_deleted_count = deleted_count
    for i in range(len(learned_data)):
        if learned_data[i]['deleted']: continue
            
        for j in range(i + 1, len(learned_data)):
            if learned_data[j]['deleted']: continue
                
            hash1 = learned_data[i]['hash']
            hash2 = learned_data[j]['hash']
            
            # Standard tolerance (10) for duplicate removal
            if compare_hashes(hash1, hash2, tolerance=HASH_TOLERANCE):
                # Keep the newer one, delete the older one.
                
                file_to_keep_index = i if learned_data[i]['timestamp'] >= learned_data[j]['timestamp'] else j
                file_to_delete_index = j if learned_data[i]['timestamp'] >= learned_data[j]['timestamp'] else i
                
                file_to_delete = learned_data[file_to_delete_index]
                learned_data[file_to_delete_index]['deleted'] = True
                    
                try:
                    os.remove(file_to_delete['path'])
                    deleted_count += 1
                    # SUPPRESS IN QUIET MODE
                    if not QUIET_MODE:
                        print(f"CLEANUP: Removed older duplicate '{file_to_delete['name']}' (Similar to '{learned_data[file_to_keep_index]['name']}').")
                except Exception as e:
                    print(f"CLEANUP ERROR: Could not delete {file_to_delete['name']}. {e}")
                        
    if deleted_count > 0:
        print(f"✅ CLEANUP COMPLETE: Removed {deleted_count} templates in total.")
    elif not QUIET_MODE:
        print("CLEANUP: No redundant or forbidden templates found.")
    print("---------------------------------")


keyboard.add_hotkey('ctrl+f9', clean_learned_templates, suppress=True)


# --- 8. THE MAIN AI LOOP ---

def main_ai_loop():
    """The core decision-making and loop control."""
    global AI_RUNNING
    
    mouse_listener = mouse.Listener(on_click=on_click)
    mouse_listener.start()

    print(f"\nSmart Desktop AI is running. Mode: {CURRENT_MODE}")

    while AI_RUNNING:
        
        
        # --- APPLICATION BLACKLIST CHECK ---
        if is_forbidden_app():
            # SUPPRESS THIS PRINT IN QUIET MODE
            if not QUIET_MODE:
                print(f"Disabled: Active app ({get_active_window_process()}) is forbidden.")
            continue 

        if CURRENT_MODE in ['CLICK_ONLY', 'BOTH']:
            screenshot = capture_screen()

            # A. ANTI-PRIORITY CHECK: NO-CLICK 
            no_click_center, no_click_name = find_best_match(screenshot, TEMPLATE_FOLDERS['no_click'], threshold=0.75)
            if no_click_center:
                # FIX APPLIED: Removed 'continue' here to prevent the check from 
                # blocking ALL clicking. It now acts as a non-fatal warning filter.
                if not QUIET_MODE:
                    print(f"Skipping click: Detected NO-CLICK item ({no_click_name}).")
                # Removed 'continue'

            # B. HIGHEST PRIORITY CLICK: USER TEMPLATES 
            target_center, target_template = find_best_match(screenshot, TEMPLATE_FOLDERS['user_priority'], threshold=0.9)
            
            if target_center:
                click_at_center(target_center)
                
                continue # Continues the loop ONLY if a successful click happens

            # C. LEARNED PRIORITY CLICK: LEARNED TEMPLATES 
            target_center, target_template = find_best_match(screenshot, TEMPLATE_FOLDERS['learned'], threshold=0.8)
            
            if target_center:
                click_at_center(target_center)
                
                continue # Continues the loop ONLY if a successful click happens
                
    # Cleanup after F12 is pressed
    mouse_listener.stop()
    
    # Attempt to clean up temporary files
    for temp_file in os.listdir(TEMP_OBSERVED_FOLDER):
        try:
            os.remove(os.path.join(TEMP_OBSERVED_FOLDER, temp_file))
        except:
            pass 
            
    print("Desktop AI Shutdown complete.")

if __name__ == "__main__":
    print(INSTRUCTIONS)
    print(f"Smart Desktop AI V2.8 starting on {platform.system()}")
    try:
        main_ai_loop()
    except Exception as e:
        print(f"An unexpected error occurred in the main loop: {e}")
    finally:
        keyboard.unhook_all()
        sys.exit(0)