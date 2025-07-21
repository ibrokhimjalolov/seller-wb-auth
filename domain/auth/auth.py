import undetected_chromedriver as uc
from time import sleep

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait


SELLER_WILDBERRIES_URL = "https://seller-auth.wildberries.ru/ru/"

NUMBER_INPUT_CSS_SELECTOR = r".SimpleInput-JIIQvb037j"
NUMBER_INPUT_BUTTON_CSS_SELECTOR = r"button.IconButton-dyRP\+yvOcb:nth-child(1)"

CODE_INPUT_CONTAINER_CSS_SELECTOR = r"li.SimpleCodeInput__item-Pk-qM5fzm\+"


def request_code(driver: uc.Chrome, number: str) -> None:
    """
    Function that requests sms verification code from seller.wildberries.ru
    Args:
        driver - selenium web driver
        number - number in format 9991231212 (10-digits without country code - +7)
    Returns:
        None
    """
    driver.get(SELLER_WILDBERRIES_URL)

    number_input = WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.CSS_SELECTOR,
                                        NUMBER_INPUT_CSS_SELECTOR))
    )

    number_input.send_keys(number)

    button = WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.CSS_SELECTOR,
                                        NUMBER_INPUT_BUTTON_CSS_SELECTOR))
    )
    button.click()


def verify_code(driver: uc.Chrome, verification_code: str) -> list[dict]:
    """
    Function that proceeds seller verification on seller.wildberries.ru
    Args:
        driver - selenium web driver
        verification_code - 6-digits code from SMS
    Returns:
        list[dict] - essential user cookies
    """
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

    return driver.get_cookies()

