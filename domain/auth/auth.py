import undetected_chromedriver as uc
from time import sleep

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver import ActionChains

SELLER_WILDBERRIES_URL = "https://seller-auth.wildberries.ru/ru/"

NUMBER_INPUT_CSS_SELECTOR = ".SimpleInput-JIIQvb037j"
COUNTRY_CODE_INPUT_CSS_SELECTOR = ".FormPhoneInputBorderless__select-dR9O1RdqnB"
NUMBER_INPUT_BUTTON_CSS_SELECTOR = "button.IconButton-dyRP\\+yvOcb:nth-child(1)"
CODE_INPUT_CONTAINER_CSS_SELECTOR = "li.SimpleCodeInput__item-Pk-qM5fzm\\+"
COUNTRY_CODES = ["374", "375", "852", "7", "996", "86", "853", "7", "90", "998"]


def request_code(driver: uc.Chrome, number: str) -> None:
    """
    Requests SMS verification code from seller.wildberries.ru
    Args:
        driver - selenium web driver
        number - number in format 9991231212 or with country code like 998901234567
    """
    driver.get(SELLER_WILDBERRIES_URL)

    # Wait for phone input field
    number_input = WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, NUMBER_INPUT_CSS_SELECTOR))
    )

    # Detect country code
    country_code = COUNTRY_CODES[0]
    index_of_country_code = 0

    for c in COUNTRY_CODES:
        if number.startswith(c):
            country_code = c
            break
        index_of_country_code += 1

    number = number[len(country_code):]

    # Open dropdown
    WebDriverWait(driver, 30).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, COUNTRY_CODE_INPUT_CSS_SELECTOR))
    ).click()

    # Wait until dropdown appears
    dropdown = WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, "ul.SelectDropdown-RY5wl9c2I9"))
    )

    # Find all country options
    options = dropdown.find_elements(By.CSS_SELECTOR, "button.DropdownListItem-avWolvN3jh")

    # Scroll to and click the correct code
    if index_of_country_code < len(options):
        target = options[index_of_country_code]
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", target)
        ActionChains(driver).move_to_element(target).click().perform()
    else:
        print(f"⚠️ Could not find country code index {index_of_country_code}")

    # Enter number
    number_input.send_keys(number)

    # Click send button
    send_button = WebDriverWait(driver, 30).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, NUMBER_INPUT_BUTTON_CSS_SELECTOR))
    )
    send_button.click()


def verify_code(driver: uc.Chrome, verification_code: str) -> dict:
    code_input_containers: list[WebElement] = WebDriverWait(driver, 30).until(
        EC.presence_of_all_elements_located(
            (By.CSS_SELECTOR, CODE_INPUT_CONTAINER_CSS_SELECTOR)
        )
    )

    for i in range(len(code_input_containers)):
        code_input_container = code_input_containers[i]
        code_input_cell = code_input_container.find_element(By.TAG_NAME, "input")
        code_input_cell.send_keys(verification_code[i])
        sleep(0.2)

    sleep(5)

    if "Неверный код" in driver.page_source:
        return {
            "success": False,
            "message": "Неверный код из SMS"
        }

    return {
        "success": True,
        "message": "Авторизация успешна",
    }
