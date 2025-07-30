import pyautogui
from PIL import Image
import time
import os
import sys
import math
from pynput import mouse, keyboard
import threading
import json
import uuid # Import the uuid module

# --- Configuration File ---
CONFIG_FILE = 'config.json'

# --- Default Configuration Values ---
DEFAULT_CONFIG = {
    'RESIZE_DIMENSIONS_WIDTH': 32,
    'RESIZE_DIMENSIONS_HEIGHT': 32,
    'MAX_COLOR_DISTANCE': 50.0,
    'MATCH_BLOCK_THRESHOLD': 0.8,
    'PYAUTOGUI_CONFIDENCE_INITIAL': 0.7,
    'CHECK_INTERVAL_SECONDS': 1.0,
    'CLICK_DELAY_SECONDS': 0.1,
    'NEW_TEMPLATE_TRAINING_CLICK_COUNT_THRESHOLD': 5,
    'RECORDING_REGION_SIZE_WIDTH': 64,
    'RECORDING_REGION_SIZE_HEIGHT': 64,
    'AUTO_TRAIN_MATCH_THRESHOLD': 0.5,
    'AUTO_TRAIN_PIXEL_DISTANCE_THRESHOLD': 30,
    'AUTO_TRAIN_HIT_THRESHOLD': 2,
    'REFINEMENT_MIN_CONFIDENCE': 0.6,
    'REFINEMENT_CLICK_WINDOW_SECONDS': 1.0,
}

# --- Global Configuration (will be loaded from config.json) ---
config = {}
RESIZE_DIMENSIONS = (DEFAULT_CONFIG['RESIZE_DIMENSIONS_WIDTH'], DEFAULT_CONFIG['RESIZE_DIMENSIONS_HEIGHT'])
MAX_COLOR_DISTANCE = DEFAULT_CONFIG['MAX_COLOR_DISTANCE']
MATCH_BLOCK_THRESHOLD = DEFAULT_CONFIG['MATCH_BLOCK_THRESHOLD']
PYAUTOGUI_CONFIDENCE_INITIAL = DEFAULT_CONFIG['PYAUTOGUI_CONFIDENCE_INITIAL']
CHECK_INTERVAL_SECONDS = DEFAULT_CONFIG['CHECK_INTERVAL_SECONDS']
CLICK_DELAY_SECONDS = DEFAULT_CONFIG['CLICK_DELAY_SECONDS']
NEW_TEMPLATE_TRAINING_CLICK_COUNT_THRESHOLD = DEFAULT_CONFIG['NEW_TEMPLATE_TRAINING_CLICK_COUNT_THRESHOLD']
RECORDING_REGION_SIZE = (DEFAULT_CONFIG['RECORDING_REGION_SIZE_WIDTH'], DEFAULT_CONFIG['RECORDING_REGION_SIZE_HEIGHT'])
AUTO_TRAIN_MATCH_THRESHOLD = DEFAULT_CONFIG['AUTO_TRAIN_MATCH_THRESHOLD']
AUTO_TRAIN_PIXEL_DISTANCE_THRESHOLD = DEFAULT_CONFIG['AUTO_TRAIN_PIXEL_DISTANCE_THRESHOLD']
AUTO_TRAIN_HIT_THRESHOLD = DEFAULT_CONFIG['AUTO_TRAIN_HIT_THRESHOLD']
REFINEMENT_MIN_CONFIDENCE = DEFAULT_CONFIG['REFINEMENT_MIN_CONFIDENCE']
REFINEMENT_CLICK_WINDOW_SECONDS = DEFAULT_CONFIG['REFINEMENT_CLICK_WINDOW_SECONDS']


# --- Global State for Modes ---
is_new_template_training_mode = False
is_auto_train_mode = False
is_settings_menu_active = False

# --- Global State for Training & Refinement ---
recorded_clicks_data = []
recording_group_counter = {}
last_scan_near_misses = []
last_scan_completion_time = 0
auto_train_refinement_counters = {}

# --- Setup Directories ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_FULL_PATH = os.path.join(SCRIPT_DIR, 'templates')
SCREENSHOTS_FULL_PATH = os.path.join(SCRIPT_DIR, 'screenshots')
RECORDINGS_FULL_PATH = os.path.join(SCRIPT_DIR, 'recordings')

# Create directories if they don't exist
os.makedirs(TEMPLATES_FULL_PATH, exist_ok=True)
os.makedirs(SCREENSHOTS_FULL_PATH, exist_ok=True)
os.makedirs(RECORDINGS_FULL_PATH, exist_ok=True)


# --- Configuration Management Functions ---

def load_config():
    global config, RESIZE_DIMENSIONS, MAX_COLOR_DISTANCE, MATCH_BLOCK_THRESHOLD, \
           PYAUTOGUI_CONFIDENCE_INITIAL, CHECK_INTERVAL_SECONDS, CLICK_DELAY_SECONDS, \
           NEW_TEMPLATE_TRAINING_CLICK_COUNT_THRESHOLD, RECORDING_REGION_SIZE, \
           AUTO_TRAIN_MATCH_THRESHOLD, AUTO_TRAIN_PIXEL_DISTANCE_THRESHOLD, AUTO_TRAIN_HIT_THRESHOLD, \
           REFINEMENT_MIN_CONFIDENCE, REFINEMENT_CLICK_WINDOW_SECONDS

    try:
        with open(CONFIG_FILE, 'r') as f:
            loaded_config = json.load(f)

        config = {**DEFAULT_CONFIG, **loaded_config}
        print(f"Configuration loaded from {CONFIG_FILE}.")

    except FileNotFoundError:
        print(f"No {CONFIG_FILE} found. Creating with default values.")
        config = DEFAULT_CONFIG.copy()
        save_config()
    except json.JSONDecodeError:
        print(f"Error decoding {CONFIG_FILE}. Using default values and overwriting the file.")
        config = DEFAULT_CONFIG.copy()
        save_config()
    except Exception as e:
        print(f"An unexpected error occurred loading config: {e}. Using default values.")
        config = DEFAULT_CONFIG.copy()
        save_config()

    RESIZE_DIMENSIONS = (config['RESIZE_DIMENSIONS_WIDTH'], config['RESIZE_DIMENSIONS_HEIGHT'])
    MAX_COLOR_DISTANCE = config['MAX_COLOR_DISTANCE']
    MATCH_BLOCK_THRESHOLD = config['MATCH_BLOCK_THRESHOLD']
    PYAUTOGUI_CONFIDENCE_INITIAL = config['PYAUTOGUI_CONFIDENCE_INITIAL']
    CHECK_INTERVAL_SECONDS = config['CHECK_INTERVAL_SECONDS']
    CLICK_DELAY_SECONDS = config['CLICK_DELAY_SECONDS']
    NEW_TEMPLATE_TRAINING_CLICK_COUNT_THRESHOLD = config['NEW_TEMPLATE_TRAINING_CLICK_COUNT_THRESHOLD']
    RECORDING_REGION_SIZE = (config['RECORDING_REGION_SIZE_WIDTH'], config['RECORDING_REGION_SIZE_HEIGHT'])
    AUTO_TRAIN_MATCH_THRESHOLD = config['AUTO_TRAIN_MATCH_THRESHOLD']
    AUTO_TRAIN_PIXEL_DISTANCE_THRESHOLD = config['AUTO_TRAIN_PIXEL_DISTANCE_THRESHOLD']
    AUTO_TRAIN_HIT_THRESHOLD = config['AUTO_TRAIN_HIT_THRESHOLD']
    REFINEMENT_MIN_CONFIDENCE = config['REFINEMENT_MIN_CONFIDENCE']
    REFINEMENT_CLICK_WINDOW_SECONDS = config['REFINEMENT_CLICK_WINDOW_SECONDS']

def save_config():
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=4)
        print(f"Configuration saved to {CONFIG_FILE}.")
    except Exception as e:
        print(f"Error saving configuration: {e}")

def update_config_value(key, value):
    global config, RESIZE_DIMENSIONS, MAX_COLOR_DISTANCE, MATCH_BLOCK_THRESHOLD, \
           PYAUTOGUI_CONFIDENCE_INITIAL, CHECK_INTERVAL_SECONDS, CLICK_DELAY_SECONDS, \
           NEW_TEMPLATE_TRAINING_CLICK_COUNT_THRESHOLD, RECORDING_REGION_SIZE, \
           AUTO_TRAIN_MATCH_THRESHOLD, AUTO_TRAIN_PIXEL_DISTANCE_THRESHOLD, AUTO_TRAIN_HIT_THRESHOLD, \
           REFINEMENT_MIN_CONFIDENCE, REFINEMENT_CLICK_WINDOW_SECONDS

    if key in config:
        try:
            if isinstance(DEFAULT_CONFIG[key], int):
                value = int(value)
            elif isinstance(DEFAULT_CONFIG[key], float):
                value = float(value)

            if key == 'RESIZE_DIMENSIONS_WIDTH':
                config['RESIZE_DIMENSIONS_WIDTH'] = value
                RESIZE_DIMENSIONS = (value, config['RESIZE_DIMENSIONS_HEIGHT'])
                print("Note: RESIZE_DIMENSIONS change might require script restart for templates to be reloaded correctly.")
            elif key == 'RESIZE_DIMENSIONS_HEIGHT':
                config['RESIZE_DIMENSIONS_HEIGHT'] = value
                RESIZE_DIMENSIONS = (config['RESIZE_DIMENSIONS_WIDTH'], value)
                print("Note: RESIZE_DIMENSIONS change might require script restart for templates to be reloaded correctly.")
            elif key == 'RECORDING_REGION_SIZE_WIDTH':
                config['RECORDING_REGION_SIZE_WIDTH'] = value
                RECORDING_REGION_SIZE = (value, config['RECORDING_REGION_SIZE_HEIGHT'])
                print("Note: RECORDING_REGION_SIZE change might require script restart for new template captures.")
            elif key == 'RECORDING_REGION_SIZE_HEIGHT':
                config['RECORDING_REGION_SIZE_HEIGHT'] = value
                RECORDING_REGION_SIZE = (config['RECORDING_REGION_SIZE_WIDTH'], value)
                print("Note: RECORDING_REGION_SIZE change might require script restart for new template captures.")
            else:
                config[key] = value
                globals()[key] = value

            save_config()
            print(f"Setting '{key}' updated to {value}.")
        except ValueError:
            print(f"Invalid value for '{key}'. Please enter a valid number.")
        except Exception as e:
            print(f"An error occurred while updating '{key}': {e}")
    else:
        print(f"Setting '{key}' not found.")

def show_settings_menu():
    global is_settings_menu_active
    is_settings_menu_active = True
    print("\n--- Settings Menu (Press 'e' or unrecognized input to exit) ---")

    while is_settings_menu_active:
        print("\nCurrent Configuration:")
        for key, value in config.items():
            print(f"  {key}: {value}")

        setting_to_change = input("\nEnter setting name to change (or 'e' to exit): ").strip()
        if setting_to_change.lower() == 'e':
            is_settings_menu_active = False
            break

        if setting_to_change not in config:
            print("Invalid setting name. Please try again.")
            continue

        new_value_str = input(f"Enter new value for '{setting_to_change}': ").strip()
        update_config_value(setting_to_change, new_value_str)


# --- Helper Functions ---

def get_average_color_blocks(pil_image, grid_size=(4, 4)):
    if pil_image.size != RESIZE_DIMENSIONS:
        pil_image = pil_image.resize(RESIZE_DIMENSIONS, Image.Resampling.LANCZOS)

    pil_image = pil_image.convert('RGB')
    width, height = pil_image.size

    block_width = width // grid_size[0]
    block_height = height // grid_size[1]

    if block_width == 0: block_width = 1
    if block_height == 0: block_height = 1

    avg_colors = []
    for row in range(grid_size[1]):
        for col in range(grid_size[0]):
            left = col * block_width
            top = row * block_height
            right = left + block_width
            bottom = top + block_height

            left = min(left, width -1)
            top = min(top, height -1)
            right = min(right, width)
            bottom = min(bottom, height)

            if right <= left or bottom <= top:
                avg_colors.append((0, 0, 0))
                continue

            block = pil_image.crop((left, top, right, bottom))
            pixels = list(block.getdata())
            if not pixels:
                avg_colors.append((0, 0, 0))
                continue

            r_sum, g_sum, b_sum = 0, 0, 0
            for r, g, b in pixels:
                r_sum += r
                g_sum += g
                b_sum += b

            num_pixels = len(pixels)
            avg_colors.append((r_sum // num_pixels, g_sum // num_pixels, b_sum // num_pixels))
    return avg_colors

def compare_color_blocks(blocks1, blocks2, max_distance):
    if len(blocks1) != len(blocks2):
        return 0.0

    matching_blocks = 0
    total_blocks = len(blocks1)

    for i in range(total_blocks):
        r1, g1, b1 = blocks1[i]
        r2, g2, b2 = blocks2[i]

        distance = math.sqrt((r1 - r2)**2 + (g1 - g2)**2 + (b1 - b2)**2)

        if distance <= max_distance:
            matching_blocks += 1

    return matching_blocks / total_blocks

def load_templates(templates_dir_path):
    templates = []
    print(f"\nLoading templates from: {templates_dir_path}")
    if not os.path.exists(templates_dir_path):
        print(f"Error: Templates directory '{templates_dir_path}' not found.")
        print("Please create it and place your .png template images inside.")
        return templates

    for filename in os.listdir(templates_dir_path):
        if filename.lower().endswith('.png'):
            template_path = os.path.join(templates_dir_path, filename)
            try:
                img = Image.open(template_path)
                resized_img = img.resize(RESIZE_DIMENSIONS, Image.Resampling.LANCZOS)
                color_blocks = get_average_color_blocks(resized_img)
                templates.append((filename, img, color_blocks))
                print(f" - Loaded template: {filename} (Original size: {img.size})")
            except Image.UnidentifiedImageError:
                print(f"Warning: Could not identify '{filename}' as a valid image. Skipping.")
            except Exception as e:
                print(f"Error loading '{filename}': {e}. Skipping.")

    if not templates:
        print(f"No .png templates found in '{templates_dir_path}'.")
    return templates


# --- Training & Refinement Functions ---

def on_click(x, y, button, pressed):
    global is_new_template_training_mode, recorded_clicks_data, recording_group_counter
    global is_auto_train_mode, last_scan_near_misses, last_scan_completion_time
    global templates_data, auto_train_refinement_counters

    if pressed and button == mouse.Button.left and not is_settings_menu_active:

        # --- 1. Reactive Refinement Check ---
        if time.time() - last_scan_completion_time < REFINEMENT_CLICK_WINDOW_SECONDS:
            for template_name, location_box in last_scan_near_misses:
                if location_box.left <= x <= location_box.left + location_box.width and \
                   location_box.top <= y <= location_box.top + location_box.height:

                    print(f"\n*** Manual click at ({x}, {y}) detected within a 'near-miss' region for '{template_name}'. ***")
                    print(f"    Do you want to update/refine '{template_name}' using this current image? (y/n)")

                    response = input().strip().lower()
                    if response == 'y':
                        refine_existing_template(template_name, location_box)
                        last_scan_near_misses = []
                        return
                    else:
                        print("    Template refinement skipped.")
                        last_scan_near_misses = []

        # --- 2. Auto-Train Mode (F12) ---
        if is_auto_train_mode:
            print(f"Manual click detected at ({x}, {y}). Auto-training active.")

            screen_width, screen_height = pyautogui.size()
            region_left = int(max(0, x - RECORDING_REGION_SIZE[0] // 2))
            region_top = int(max(0, y - RECORDING_REGION_SIZE[1] // 2))
            region_width = RECORDING_REGION_SIZE[0]
            region_height = RECORDING_REGION_SIZE[1]

            if region_left + region_width > screen_width: region_left = screen_width - region_width
            if region_top + region_height > screen_height: region_top = screen_height - region_height
            region_left = max(0, region_left)
            region_top = max(0, region_top)
            if region_width <= 0: region_width = 1
            if region_height <= 0: region_height = 1

            try:
                clicked_region_img = pyautogui.screenshot(region=(region_left, region_top, region_width, region_height))
                resized_clicked_img = clicked_region_img.resize(RESIZE_DIMENSIONS, Image.Resampling.LANCZOS)
                clicked_blocks = get_average_color_blocks(resized_clicked_img)

                best_match_template_name = None
                highest_similarity = 0.0
                best_match_location = None

                for template_name, original_template_pil, template_blocks in templates_data:
                    similarity = compare_color_blocks(clicked_blocks, template_blocks, MAX_COLOR_DISTANCE)

                    template_pyautogui_path = os.path.join(TEMPLATES_FULL_PATH, template_name)
                    try:
                        location_on_screen = pyautogui.locateOnScreen(
                            template_pyautogui_path,
                            confidence=PYAUTOGUI_CONFIDENCE_INITIAL,
                            grayscale=False
                        )
                        if location_on_screen:
                            template_center_x = location_on_screen.left + location_on_screen.width // 2
                            template_center_y = location_on_screen.top + location_on_screen.height // 2
                            pixel_distance = math.sqrt((x - template_center_x)**2 + (y - template_center_y)**2)

                            if pixel_distance <= AUTO_TRAIN_PIXEL_DISTANCE_THRESHOLD and similarity > highest_similarity:
                                highest_similarity = similarity
                                best_match_template_name = template_name
                                best_match_location = location_on_screen

                    except pyautogui.ImageNotFoundException:
                        pass
                    except Exception as e:
                        print(f"Warning: Error during pyautogui.locateOnScreen for '{template_name}' during auto-train: {e}")

                if best_match_template_name and highest_similarity >= AUTO_TRAIN_MATCH_THRESHOLD:
                    auto_train_refinement_counters[best_match_template_name] = \
                        auto_train_refinement_counters.get(best_match_template_name, 0) + 1
                    current_auto_train_count = auto_train_refinement_counters[best_match_template_name]

                    print(f"  --> Auto-training: Click similar to '{best_match_template_name}'. Count: {current_auto_train_count}/{AUTO_TRAIN_HIT_THRESHOLD}")

                    if current_auto_train_count >= AUTO_TRAIN_HIT_THRESHOLD:
                        print(f"\n*** Auto-Train: {AUTO_TRAIN_HIT_THRESHOLD} similar clicks for '{best_match_template_name}' detected. Refining template! ***")
                        if best_match_location:
                            refine_existing_template(best_match_template_name, best_match_location)
                        else:
                            refine_existing_template(best_match_template_name, pyautogui.Box(region_left, region_top, region_width, region_height))

                        auto_train_refinement_counters[best_match_template_name] = 0
                else:
                    print(f"  --> Auto-training: No sufficiently similar existing template found (Similarity: {highest_similarity:.2f}).")

            except Exception as e:
                print(f"Error during auto-train click processing: {e}")
                import traceback; traceback.print_exc()

        # --- 3. New Template Training Mode (F9) ---
        if is_new_template_training_mode:
            screen_width, screen_height = pyautogui.size()
            region_left = int(max(0, x - RECORDING_REGION_SIZE[0] // 2))
            region_top = int(max(0, y - RECORDING_REGION_SIZE[1] // 2))
            region_width = RECORDING_REGION_SIZE[0]
            region_height = RECORDING_REGION_SIZE[1]

            if region_left + region_width > screen_width: region_left = screen_width - region_width
            if region_top + region_height > screen_height: region_top = screen_height - region_height
            region_left = max(0, region_left)
            region_top = max(0, region_top)
            if region_width <= 0: region_width = 1
            if region_height <= 0: region_height = 1

            try:
                clicked_region_img = pyautogui.screenshot(region=(region_left, region_top, region_width, region_height))
                resized_clicked_img = clicked_region_img.resize(RESIZE_DIMENSIONS, Image.Resampling.LANCZOS)
                clicked_blocks = get_average_color_blocks(resized_clicked_img)

                found_similar_group = False
                for group_id, count in list(recording_group_counter.items()):
                    representative_click_items = [item for item in recorded_clicks_data if item[0] == group_id]
                    if not representative_click_items: continue

                    representative_img_path = representative_click_items[0][4]
                    if not os.path.exists(representative_img_path): continue

                    representative_img = Image.open(representative_img_path).resize(RESIZE_DIMENSIONS, Image.Resampling.LANCZOS)
                    representative_blocks = get_average_color_blocks(representative_img)

                    similarity = compare_color_blocks(clicked_blocks, representative_blocks, MAX_COLOR_DISTANCE)

                    if similarity >= 0.7:
                        recording_group_counter[group_id] += 1
                        current_count = recording_group_counter[group_id]
                        print(f"  --> Click is similar to group '{group_id}'. Count: {current_count}/{NEW_TEMPLATE_TRAINING_CLICK_COUNT_THRESHOLD}")

                        timestamp = int(time.time())
                        click_img_filename = f"click_{timestamp}_{group_id}.png"
                        click_img_path = os.path.join(RECORDINGS_FULL_PATH, click_img_filename)
                        clicked_region_img.save(click_img_path)
                        recorded_clicks_data.append((group_id, timestamp, x, y, click_img_path, clicked_blocks))

                        found_similar_group = True

                        if current_count >= NEW_TEMPLATE_TRAINING_CLICK_COUNT_THRESHOLD:
                            print(f"\n*** New Template Training: {NEW_TEMPLATE_TRAINING_CLICK_COUNT_THRESHOLD} similar clicks detected. Auto-creating new template! ***")
                            create_new_template_from_group(group_id)
                            recorded_clicks_data = [item for item in recorded_clicks_data if item[0] != group_id]
                            del recording_group_counter[group_id]
                        break

                if not found_similar_group:
                    # MODIFIED: Use uuid for consistently unique group IDs
                    group_id = uuid.uuid4().hex
                    recording_group_counter[group_id] = 1

                    timestamp = int(time.time())
                    click_img_filename = f"click_{timestamp}_{group_id}.png"
                    click_img_path = os.path.join(RECORDINGS_FULL_PATH, click_img_filename)
                    clicked_region_img.save(click_img_path)
                    recorded_clicks_data.append((group_id, timestamp, x, y, click_img_path, clicked_blocks))
                    print(f"  New click group '{group_id}' started. Count: 1/{NEW_TEMPLATE_TRAINING_CLICK_COUNT_THRESHOLD}")

            except Exception as e:
                print(f"Error during new template training click processing: {e}")
                import traceback; traceback.print_exc()


def create_new_template_from_group(group_id):
    global templates_data
    group_clicks = [item for item in recorded_clicks_data if item[0] == group_id]
    if not group_clicks:
        print(f"No clicks found for group '{group_id}' to create a template.")
        return

    representative_click_path = group_clicks[0][4]

    try:
        if not os.path.exists(representative_click_path):
            print(f"Error: Representative image '{representative_click_path}' not found for template creation.")
            return

        template_img = Image.open(representative_click_path)

        # --- MODIFIED: Auto-generate template name ---
        template_name = uuid.uuid4().hex # Generate a unique random string

        final_template_filename = f"{template_name}.png"
        final_template_path = os.path.join(TEMPLATES_FULL_PATH, final_template_filename)

        template_img.save(final_template_path)
        print(f"Successfully created new template: {final_template_path}")

        templates_data = load_templates(TEMPLATES_FULL_PATH)

    except Exception as e:
        print(f"Error creating template from group '{group_id}': {e}")
        import traceback; traceback.print_exc()


def refine_existing_template(template_name, location_box=None):
    global templates_data
    template_filename = template_name
    template_path = os.path.join(TEMPLATES_FULL_PATH, template_filename)

    try:
        current_image = None
        if location_box:
            screen_width, screen_height = pyautogui.size()

            x1 = int(max(0, location_box.left))
            y1 = int(max(0, location_box.top))
            x2 = int(min(screen_width, location_box.left + location_box.width))
            y2 = int(min(screen_height, location_box.top + location_box.height))

            region_width = int(x2 - x1)
            region_height = int(y2 - y1)

            if region_width <= 0 or region_height <= 0:
                print(f"Error: Invalid region for refining {template_name}. Skipping refinement.")
                return

            current_image = pyautogui.screenshot(region=(x1, y1, region_width, region_height))
        else:
            print(f"Warning: No specific location for '{template_name}' provided for refinement. Attempting to locate on screen for recapture.")
            located_box = pyautogui.locateOnScreen(template_path, confidence=PYAUTOGUI_CONFIDENCE_INITIAL, grayscale=False)
            if located_box:
                current_image = pyautogui.screenshot(region=located_box)
            else:
                print(f"Could not locate '{template_name}' on screen for refinement. Skipping.")
                return

        if current_image:
            current_image.save(template_path)
            print(f"Template '{template_name}' successfully refined/updated with new image.")
            templates_data = load_templates(TEMPLATES_FULL_PATH)
        else:
            print(f"No image captured for refining '{template_name}'.")

    except Exception as e:
        print(f"Error refining template '{template_name}': {e}")
        import traceback; traceback.print_exc()


# --- Keyboard Listener for Mode Switching ---
# Declared globally to be accessible by on_press and main loop
mouse_listener = None
keyboard_listener = None

def on_press(key):
    global is_new_template_training_mode, is_auto_train_mode, is_settings_menu_active
    global keyboard_listener, mouse_listener

    if is_settings_menu_active:
        if key == keyboard.Key.esc:
            is_settings_menu_active = False
            print("\nExiting Settings Menu.")
            return False
        return

    try:
        if key == keyboard.Key.f9:
            is_new_template_training_mode = not is_new_template_training_mode
            if is_new_template_training_mode:
                print("\n*** New Template Training Mode ENABLED (F9). Click 5 times for new template (auto-confirmed). ***")
                print("    (Press F9 again to disable this mode.)")
            else:
                print("\n*** New Template Training Mode DISABLED (F9). ***")
            print(f"    Current Modes: New Template Training: {'ON' if is_new_template_training_mode else 'OFF'}, Auto-Train: {'ON' if is_auto_train_mode else 'OFF'}")
        elif key == keyboard.Key.f12:
            is_auto_train_mode = not is_auto_train_mode
            if is_auto_train_mode:
                print("\n*** Auto-Train Mode ENABLED (F12). Manual clicks will attempt to refine/train (2 hits). ***")
                print("    (Press F12 again to disable this mode.)")
            else:
                print("\n*** Auto-Train Mode DISABLED (F12). ***")
            print(f"    Current Modes: New Template Training: {'ON' if is_new_template_training_mode else 'OFF'}, Auto-Train: {'ON' if is_auto_train_mode else 'OFF'}")
        elif key == keyboard.Key.f11:
            print("\n*** F11 pressed. Entering Settings Menu. ***")
            if mouse_listener and mouse_listener.is_alive():
                mouse_listener.stop()
            if keyboard_listener and keyboard_listener.is_alive():
                keyboard_listener.stop()
            show_settings_menu()
            return False
        elif key == keyboard.Key.esc:
            print("\nESC pressed. Exiting script.")
            if mouse_listener and mouse_listener.is_alive():
                mouse_listener.stop()
            if keyboard_listener and keyboard_listener.is_alive():
                keyboard_listener.stop()
            sys.exit(0)
    except AttributeError:
        pass


# --- Main Auto-Clicker Logic ---

def auto_click_multiple_templates():
    global templates_data
    global last_scan_near_misses, last_scan_completion_time
    global mouse_listener, keyboard_listener
    global is_settings_menu_active
    global is_new_template_training_mode # Need to access this global variable

    print(f"--- Auto-Clicker Initializing ---")
    print(f"Script running from: {SCRIPT_DIR}")
    print(f"Templates expected in: {TEMPLATES_FULL_PATH}")
    print(f"Debug screenshots will be saved to: {SCREENSHOTS_FULL_PATH}")
    print(f"Click recordings will be saved to: {RECORDINGS_FULL_PATH}")

    load_config()
    templates_data = load_templates(TEMPLATES_FULL_PATH)

    # MODIFIED: Check if no templates are loaded and activate training mode
    if not templates_data:
        print("No templates loaded. Automatically enabling New Template Training Mode.")
        is_new_template_training_mode = True
        print("\n*** New Template Training Mode ENABLED (F9). Click 5 times for new template (auto-confirmed). ***")
        print("    (Press F9 again to disable this mode.)")
    # Removed the check for `is_new_template_training_mode` and `is_auto_train_mode` here as it's now handled by the above `if` block.
    # The script should not exit if no templates are found, but instead enter training mode.
    print(f"Total {len(templates_data)} templates loaded.") # This line needs to be outside the if not templates_data block
    print(f"Starting auto-clicker. Press F9 for New Template Training, F12 for Auto-Train, F11 for Settings, ESC to exit.")
    print(f"    Current Modes: New Template Training: {'ON' if is_new_template_training_mode else 'OFF'}, Auto-Train: {'ON' if is_auto_train_mode else 'OFF'}")


    last_clicked_time = 0

    mouse_listener = mouse.Listener(on_click=on_click)
    mouse_listener.daemon = True
    mouse_listener.start()

    # Initialize keyboard listener once globally
    keyboard_listener = keyboard.Listener(on_press=on_press)
    keyboard_listener.daemon = True
    keyboard_listener.start()

    while True:
        try:
            while True:
                if is_settings_menu_active:
                    time.sleep(0.1)
                    continue

                if not is_new_template_training_mode:
                    current_time = time.time()
                    if current_time - last_clicked_time < CLICK_DELAY_SECONDS:
                        time.sleep(0.01)
                        continue

                    found_and_clicked = False
                    last_scan_near_misses = []

                    for template_name, original_template_pil, template_blocks in templates_data:
                        try:
                            template_path_for_pyautogui = os.path.join(TEMPLATES_FULL_PATH, template_name)

                            location = pyautogui.locateOnScreen(
                                template_path_for_pyautogui,
                                confidence=PYAUTOGUI_CONFIDENCE_INITIAL,
                                grayscale=False
                            )

                            if location:
                                screen_width, screen_height = pyautogui.size()

                                x1 = int(max(0, location.left))
                                y1 = int(max(0, location.top))
                                x2 = int(min(screen_width, location.left + location.width))
                                y2 = int(min(screen_height, location.top + location.height))

                                region_width = int(x2 - x1)
                                region_height = int(y2 - y1)

                                if region_width <= 0 or region_height <= 0:
                                    continue

                                screenshot_region_pil = pyautogui.screenshot(region=(x1, y1, region_width, region_height))

                                candidate_resized_img = screenshot_region_pil.resize(RESIZE_DIMENSIONS, Image.Resampling.LANCZOS)
                                candidate_blocks = get_average_color_blocks(candidate_resized_img)

                                match_confidence_blocks = compare_color_blocks(template_blocks, candidate_blocks, MAX_COLOR_DISTANCE)

                                if match_confidence_blocks >= MATCH_BLOCK_THRESHOLD:
                                    print(f"Matched '{template_name}' with {match_confidence_blocks:.2f} confidence blocks at {location}. Clicking!")

                                    timestamp = int(time.time())
                                    debug_screenshot_path = os.path.join(SCREENSHOTS_FULL_PATH, f"matched_{template_name.replace('.png', '')}_{timestamp}.png")
                                    try:
                                        pyautogui.screenshot(debug_screenshot_path)
                                    except Exception as e:
                                        print(f"Warning: Could not save debug screenshot to {debug_screenshot_path}: {e}")

                                    click_x = location.left + location.width // 2
                                    click_y = location.top + location.height // 2
                                    pyautogui.click(click_x, click_y)

                                    found_and_clicked = True
                                    last_clicked_time = current_time
                                    break
                                elif match_confidence_blocks >= REFINEMENT_MIN_CONFIDENCE:
                                    last_scan_near_misses.append((template_name, location))

                        except pyautogui.ImageNotFoundException:
                            pass
                        except Exception as e:
                            print(f"An error occurred processing template '{template_name}': {e}")
                            import traceback
                            traceback.print_exc()

                    last_scan_completion_time = time.time()
                    if not found_and_clicked:
                        time.sleep(CHECK_INTERVAL_SECONDS)

                else:
                    time.sleep(0.1)

        except KeyboardInterrupt:
            print("\nScript stopped by user (Ctrl+C).")
            break
        except pyautogui.FailSafeException:
            print("\nScript stopped by PyAutoGUI Fail-Safe (mouse moved to top-left corner).")
            break
        finally:
            pass

        # If a listener was stopped (e.g., for settings menu), restart it
        if not mouse_listener.is_alive():
            mouse_listener.start()
        if not keyboard_listener.is_alive():
            keyboard_listener.start()

        if is_settings_menu_active:
             is_settings_menu_active = False
             print("Resuming auto-clicker.")


if __name__ == "__main__":
    print("--- Setup Instructions ---")
    print(f"1. Create a folder named 'templates' in the same directory as this script.")
    print(f"2. Place any existing '.png' templates into the 'templates' folder.")
    print(f"3. A 'screenshots' folder will be created for debug screenshots.")
    print(f"4. A 'recordings' folder will be created for temporary click recordings.")
    print("5. A 'config.json' file will be created/updated to save your settings.")
    print("6. Ensure you are running this script as your regular user (NOT root/sudo) within your virtual environment.")
    print("\n--- Usage ---")
    print(" - Script starts in Auto-Click Mode by default (scans and clicks based on templates).")
    print(" - Press 'F9' to toggle into 'New Template Training Mode': Manually click an element 5 times to create a new template (name is auto-generated).")
    print(" - Press 'F12' to toggle 'Auto-Train Mode': When active, your manual clicks will automatically refine existing templates (2 similar hits needed) or contribute to new template creation if no strong match is found. This runs *alongside* auto-click mode.")
    print(" - Press 'F11' to enter the Settings Menu: Change thresholds, hit counts, and other parameters, saved to config.json.")
    print(" - Reactive Refinement: If the auto-clicker almost matches a template (but doesn't click), and you manually click that exact spot shortly after, it will prompt to refine that template.")
    print(" - Move your mouse to the top-left corner of the screen (0,0) or press 'ESC' to instantly stop the script.")
    print("--------------------------")

    templates_data = []

    auto_click_multiple_templates()
