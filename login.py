import os
import time
import csv
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# --- CONFIGURATION ---
URL = "https://app.hisabkitabnepal.com/admin/login"
TEST_CASES = [
    {"username": "your-username", "password": "your-password", "name": "valid_login"},
    {"username": "invalid_user", "password": "wrong_pass", "name": "invalid_login"},
    {"username": "", "password": "", "name": "empty_fields"},
]
SCREENSHOT_DIR = "./hisabkitab_screenshot"
CSV_FILE = "./hisabkitab_login_results.csv"
CHROMEDRIVER_PATH = None

# --- Create screenshot folder ---
if not os.path.exists(SCREENSHOT_DIR):
    os.makedirs(SCREENSHOT_DIR)

# --- Setup driver ---
try:
    if CHROMEDRIVER_PATH:
        if not os.path.isfile(CHROMEDRIVER_PATH):
            raise FileNotFoundError(f"ChromeDriver not found at {CHROMEDRIVER_PATH}")
        service = Service(CHROMEDRIVER_PATH)
        driver = webdriver.Chrome(service=service)
    else:
        driver = webdriver.Chrome()
except Exception as e:
    print(f"ERROR: Unable to start ChromeDriver. {e}")
    exit(1)

# --- Prepare CSV ---
if not os.path.exists(CSV_FILE):
    with open(CSV_FILE, mode="w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Timestamp", "Test Case", "Username", "Password", "Result", "Error Message", "Screenshot"])

# --- Function to perform login test ---
def test_login(username, password, test_name):
    driver.get(URL)
    driver.maximize_window()
    wait = WebDriverWait(driver, 15)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Detect input fields
    username_field = wait.until(EC.visibility_of_element_located(
        (By.XPATH, "//input[@type='text' or @type='email' or contains(@placeholder,'Username') or contains(@placeholder,'Email')]")
    ))
    password_field = driver.find_element(By.XPATH, "//input[@type='password']")

    # Screenshot before entering credentials
    before_path = os.path.join(SCREENSHOT_DIR, f"{test_name}_before.png")
    driver.save_screenshot(before_path)

    # Enter credentials
    username_field.clear()
    password_field.clear()
    username_field.send_keys(username)
    password_field.send_keys(password)

    # Screenshot after entering credentials
    entered_path = os.path.join(SCREENSHOT_DIR, f"{test_name}_entered.png")
    driver.save_screenshot(entered_path)

    # --- Universal login button detection ---
    try:
        login_button = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//*[contains(translate(text(),'LOGIN','login'),'login')] | //input[@type='submit']")
        ))
        # Use JS click to handle custom buttons
        driver.execute_script("arguments[0].click();", login_button)
    except Exception as e:
        print(f"{test_name}: Could not find login button ❌ {e}")
        screenshot_path = os.path.join(SCREENSHOT_DIR, f"{test_name}_no_button.png")
        driver.save_screenshot(screenshot_path)
        result = "Failed"
        error_message = "Login button not found"
        with open(CSV_FILE, mode="a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([timestamp, test_name, username, password, result, error_message, screenshot_path])
        return

    # Wait for result
    time.sleep(2)
    error_message = ""
    try:
        # Check if dashboard exists
        dashboard_element = wait.until(EC.visibility_of_element_located(
            (By.XPATH, "//h1[contains(text(),'Dashboard')]")
        ))
        result = "Success"
        screenshot_path = os.path.join(SCREENSHOT_DIR, f"{test_name}_success.png")
        driver.save_screenshot(screenshot_path)
    except:
        # Check if page shows error message
        try:
            error_elem = driver.find_element(By.XPATH, "//div[contains(@class,'error') or contains(@class,'alert')]")
            error_message = error_elem.text
        except:
            error_message = "No dashboard or error message found"
        result = "Failed"
        screenshot_path = os.path.join(SCREENSHOT_DIR, f"{test_name}_failed.png")
        driver.save_screenshot(screenshot_path)

    # Save result to CSV
    with open(CSV_FILE, mode="a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([timestamp, test_name, username, password, result, error_message, screenshot_path])

    print(f"{test_name}: {result} " if result == "Success" else f"{test_name}: {result} ")

# --- Run all test cases ---
try:
    for case in TEST_CASES:
        test_login(case["username"], case["password"], case["name"])
finally:
    driver.quit()
