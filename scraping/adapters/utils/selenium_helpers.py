"""
Selenium-related helper functions for web scraping.
"""

import time
from typing import Optional, List
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service


def create_chrome_driver(
    headless: bool = True,
    timeout: int = 30,
    user_agent: Optional[str] = None
) -> webdriver.Chrome:
    """
    Create a configured Chrome WebDriver instance.
    
    Args:
        headless: Whether to run browser in headless mode
        timeout: Page load timeout in seconds
        user_agent: Custom user agent string (optional)
    
    Returns:
        Configured Chrome WebDriver instance
    """
    chrome_options = Options()
    
    if headless:
        chrome_options.add_argument('--headless')
    
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--start-maximized')
    
    # Set user agent
    if user_agent is None:
        user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    chrome_options.add_argument(f'user-agent={user_agent}')
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.set_page_load_timeout(timeout)
    
    return driver


def safe_click(driver: webdriver.Chrome, element: WebElement, use_js: bool = True) -> bool:
    """
    Safely click an element, with fallback to JavaScript click.
    
    Args:
        driver: Chrome WebDriver instance
        element: Element to click
        use_js: Whether to use JavaScript click (more reliable)
    
    Returns:
        True if successful, False otherwise
    """
    try:
        if use_js:
            driver.execute_script("arguments[0].click();", element)
        else:
            element.click()
        return True
    except Exception as e:
        print(f"⚠ Click failed: {e}")
        return False


def wait_for_element(
    driver: webdriver.Chrome,
    selector: str,
    by: By = By.CSS_SELECTOR,
    timeout: int = 10,
    clickable: bool = False
) -> Optional[WebElement]:
    """
    Wait for an element to be present or clickable.
    
    Args:
        driver: Chrome WebDriver instance
        selector: Element selector
        by: Selector type (CSS_SELECTOR, XPATH, etc.)
        timeout: Maximum wait time in seconds
        clickable: Whether to wait for element to be clickable
    
    Returns:
        WebElement if found, None otherwise
    """
    try:
        condition = EC.element_to_be_clickable if clickable else EC.presence_of_element_located
        element = WebDriverWait(driver, timeout).until(
            condition((by, selector))
        )
        return element
    except TimeoutException:
        print(f"⚠ Timeout waiting for element: {selector}")
        return None
    except Exception as e:
        print(f"⚠ Error waiting for element: {e}")
        return None


def find_element_with_fallbacks(
    driver: webdriver.Chrome,
    selectors: List[str],
    by: By = By.CSS_SELECTOR
) -> Optional[WebElement]:
    """
    Try multiple selectors in order until one is found.
    
    Args:
        driver: Chrome WebDriver instance
        selectors: List of selectors to try
        by: Selector type
    
    Returns:
        First matching element, or None if not found
    """
    for selector in selectors:
        try:
            element = driver.find_element(by, selector)
            if element.is_displayed():
                return element
        except (NoSuchElementException, Exception):
            continue
    return None


def scroll_to_bottom(driver: webdriver.Chrome, sleep_time: float = 2):
    """
    Scroll to the bottom of the page.
    
    Args:
        driver: Chrome WebDriver instance
        sleep_time: Time to wait after scrolling
    """
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(sleep_time)


def get_page_text(driver: webdriver.Chrome) -> str:
    """
    Get all visible text from the page.
    
    Args:
        driver: Chrome WebDriver instance
    
    Returns:
        Full page text
    """
    try:
        return driver.find_element(By.TAG_NAME, "body").text
    except Exception:
        return ""
