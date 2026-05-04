import os

import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


BASE_URL = os.getenv("BASE_URL", "http://app:8000").rstrip("/")
SELENIUM_REMOTE_URL = os.getenv(
    "SELENIUM_REMOTE_URL",
    "http://selenium:4444/wd/hub",
)
SMOKE_EMAIL = os.getenv("SMOKE_EMAIL", "smoke@example.test")
SMOKE_PASSWORD = os.getenv("SMOKE_PASSWORD", "123")

PAGE_CHECKS = {
    "/": ["Activism Tool", "Navigation"],
    "/species": ["Total Species"],
    "/species/at-risk": ["At-Risk Species"],
    "/species/key": ["Key Species"],
    "/species/stats": ["Species Summary", "Total Species"],
    "/order-summary": ["Order Summary", "Total Species"],
    "/map": ["At-Risk Species Map"],
    "/time-dot-graph": ["Time Dot Graph"],
    "/survey-map": ["Survey Maps", "Surveys"],
    "/bird-traits": ["Bird Traits"],
    "/download-ala": ["Download ALA Data", "Upload KML File", "Start Pipeline"],
}


def login(driver, wait):
    driver.get(f"{BASE_URL}/login")

    email_input = wait.until(EC.presence_of_element_located((By.NAME, "email")))
    password_input = wait.until(EC.presence_of_element_located((By.NAME, "password")))

    email_input.clear()
    email_input.send_keys(SMOKE_EMAIL)
    password_input.clear()
    password_input.send_keys(SMOKE_PASSWORD)

    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
    wait.until(EC.presence_of_element_located((By.LINK_TEXT, "Logout")))

    if "Logout" not in driver.page_source:
        raise AssertionError(
            "Login failed. Create the smoke user first: "
            f"{SMOKE_EMAIL} / {SMOKE_PASSWORD}"
        )


def check_page(driver, wait, path, expected_texts):
    driver.get(f"{BASE_URL}{path}")
    wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))

    if "Internal Server Error" in driver.page_source:
        raise AssertionError(f"{path} returned an internal server error.")

    if "Login" in driver.title:
        raise AssertionError(f"{path} redirected to login.")

    missing_texts = [text for text in expected_texts if text not in driver.page_source]
    if missing_texts:
        raise AssertionError(
            f"{path} is missing expected text: {', '.join(missing_texts)}"
        )


@pytest.fixture(scope="session")
def driver():
    options = webdriver.ChromeOptions()
    if os.getenv("VISIBLE_BROWSER", "false").lower() != "true":
        options.add_argument("--headless=new")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--no-sandbox")
    options.add_argument("--window-size=1280,900")

    browser = webdriver.Remote(
        command_executor=SELENIUM_REMOTE_URL,
        options=options,
    )
    yield browser
    browser.quit()


@pytest.fixture(scope="session")
def wait(driver):
    return WebDriverWait(driver, 15)


@pytest.fixture(scope="session", autouse=True)
def logged_in(driver, wait):
    login(driver, wait)


@pytest.mark.parametrize(
    ("path", "expected_texts"),
    PAGE_CHECKS.items(),
    ids=PAGE_CHECKS.keys(),
)
def test_protected_page_contains_expected_content(driver, wait, path, expected_texts):
    check_page(driver, wait, path, expected_texts)
