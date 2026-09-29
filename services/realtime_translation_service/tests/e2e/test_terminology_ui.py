import os
import time
import requests
import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# --- CẤU HÌNH MÔI TRƯỜNG ---
FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:5173")
BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000")
SCREENSHOT_DIR = "tests/e2e/screenshots/terminology"

def ensure_test_user():
    # Tạo user nếu chưa có
    try:
        requests.post(f"{BACKEND_URL}/api/auth/register", json={
            'identifier': 'testuser123@gmail.com',
            'password': 'TestPassword123!',
            'confirmPassword': 'TestPassword123!',
            'fullName': 'Test User',
            'userType': 'public'
        })
    except:
        pass
    
    # Đăng nhập lấy token
    res = requests.post(f"{BACKEND_URL}/api/auth/login", json={
        'identifier': 'testuser123@gmail.com',
        'password': 'TestPassword123!'
    })
    if res.status_code == 200:
        return res.json().get('data', {}).get('token')
    return None

@pytest.fixture(scope="session")
def driver():
    token = ensure_test_user()
    if not token:
        pytest.fail("Cannot create/login test user for E2E tests.")
        
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.set_capability("goog:loggingPrefs", {"browser": "ALL", "performance": "ALL"})
    
    driver = webdriver.Chrome(options=options)
    driver.implicitly_wait(5)
    
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)
    
    # 1. Truy cập root
    driver.get(FRONTEND_URL)
    
    # 2. Inject JWT token vào sessionStorage
    driver.execute_script(f"sessionStorage.setItem('iuh_portal_ai_token', '{token}');")
    
    yield driver
    driver.quit()

@pytest.fixture(autouse=True)
def go_to_translation(driver):
    # Mỗi test case đều vào thẳng trang translation
    driver.get(FRONTEND_URL + "/translation")
    # Chờ trang load xong (ví dụ chờ textarea xuất hiện)
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.TAG_NAME, "textarea"))
    )

# --- HELPER FUNCTIONS ---
def take_screenshot(driver, name):
    filepath = os.path.join(SCREENSHOT_DIR, f"{name}.png")
    driver.save_screenshot(filepath)
    return filepath

def input_text(driver, text):
    textarea = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.TAG_NAME, "textarea"))
    )
    # Dùng Selenium Keys để chọn toàn bộ text và xóa
    from selenium.webdriver.common.keys import Keys
    textarea.send_keys(Keys.CONTROL + "a")
    textarea.send_keys(Keys.BACKSPACE)
    # Đề phòng trên Mac dùng Command+A
    textarea.send_keys(Keys.COMMAND + "a")
    textarea.send_keys(Keys.BACKSPACE)
    
    # Ngoài ra force clear bằng JS
    driver.execute_script("arguments[0].value = ''; arguments[0].dispatchEvent(new Event('input', { bubbles: true }));", textarea)
    
    time.sleep(0.5)
    textarea.send_keys(text)

def select_domain(driver, domain_name):
    try:
        # Nhấn vào vùng chọn domain (thẻ chứa icon ChevronDown)
        dropdown = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//div[contains(@class, 'flex items-center justify-between w-64')]"))
        )
        dropdown.click()
        
        # Nhập từ khóa vào ô search
        search_input = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.XPATH, "//input[@placeholder='Tìm hoặc nhập tên ngành...']"))
        )
        search_input.clear()
        search_input.send_keys(domain_name)
        time.sleep(0.5)
        
        # Click vào kết quả option
        option = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, f"//div[contains(@class, 'cursor-pointer')]//span[text()='{domain_name}']"))
        )
        option.click()
        time.sleep(0.5)
    except Exception as e:
        print(f"Lỗi chọn domain: {e}")

def wait_for_translation_to_finish(driver):
    # Đợi debounce trigger (300ms) + 100ms margin
    time.sleep(0.5)
    try:
        # Đợi spinner biến mất nếu nó đang chạy
        WebDriverWait(driver, 15).until(
            EC.invisibility_of_element_located((By.CSS_SELECTOR, ".animate-pulse"))
        )
    except:
        pass
    # Đợi component render xong
    time.sleep(1.5)

def get_warning_text(driver):
    try:
        warning_box = driver.find_element(By.XPATH, "//span[contains(text(), '⚠️ Cảnh báo')]/..")
        return warning_box.text
    except:
        return None

# ==========================================
# CÁC TEST CASES
# ==========================================

def test_e2e_tc01_short_exact_match(driver):
    select_domain(driver, "Công nghệ Thông tin (IT)")
    input_text(driver, "Memory leak")
    wait_for_translation_to_finish(driver)
    
    warning = get_warning_text(driver)
    take_screenshot(driver, "E2E-TC01_success_no_warning")
    assert warning is None

def test_e2e_tc02_short_no_match(driver):
    select_domain(driver, "Công nghệ Thông tin (IT)")
    input_text(driver, "Random unknown word")
    wait_for_translation_to_finish(driver)
    
    textarea = driver.find_element(By.TAG_NAME, "textarea")
    translated_text = driver.find_element(By.XPATH, "//div[contains(@class, 'whitespace-pre-wrap')]").text
    warning = get_warning_text(driver)
    
    with open("tc02_debug.txt", "w", encoding="utf-8") as f:
        f.write(f"Source text: {textarea.get_attribute('value')}\n")
        f.write(f"Translated text: {translated_text}\n")
        f.write(f"Warning: {warning}\n")
        f.write("=== CONSOLE LOGS ===\n")
        try:
            for log in driver.get_log('browser'):
                f.write(f"{log}\n")
        except Exception as e:
            f.write(f"Failed to get console logs: {e}\n")
        
    take_screenshot(driver, "E2E-TC02_fallback_warning")
    assert warning is not None
    assert "không được tìm thấy" in warning.lower()

def test_e2e_tc03_long_success(driver):
    select_domain(driver, "Y khoa / Sức khỏe")
    input_text(driver, "Checking drug interaction is extremely important.")
    wait_for_translation_to_finish(driver)
    
    warning = get_warning_text(driver)
    take_screenshot(driver, "E2E-TC03_long_success_no_warning")
    assert warning is None

def test_e2e_tc05_long_no_terminology(driver):
    select_domain(driver, "Y khoa / Sức khỏe")
    input_text(driver, "This is just a normal sentence to translate.")
    wait_for_translation_to_finish(driver)
    
    warning = get_warning_text(driver)
    take_screenshot(driver, "E2E-TC05_long_no_term_no_warning")
    assert warning is None

def test_e2e_tc06_case_insensitivity(driver):
    select_domain(driver, "Công nghệ Thông tin (IT)")
    input_text(driver, "MEMORY LEAK")
    wait_for_translation_to_finish(driver)
    
    warning = get_warning_text(driver)
    take_screenshot(driver, "E2E-TC06_case_insensitivity_success")
    assert warning is None

def test_e2e_tc07_flow1_short(driver):
    select_domain(driver, "Dịch thông thường (Mặc định)")
    input_text(driver, "Memory leak")
    wait_for_translation_to_finish(driver)
    
    warning = get_warning_text(driver)
    take_screenshot(driver, "E2E-TC07_flow1_short_no_warning")
    assert warning is None
    
def test_e2e_tc08_flow1_long(driver):
    select_domain(driver, "Dịch thông thường (Mặc định)")
    input_text(driver, "A memory leak causes crashes in the system.")
    wait_for_translation_to_finish(driver)
    
    warning = get_warning_text(driver)
    take_screenshot(driver, "E2E-TC08_flow1_long_no_warning")
    assert warning is None
