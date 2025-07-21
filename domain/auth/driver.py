import undetected_chromedriver as uc


def get_driver():
    options = uc.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--window-size=1200,800")
    options.add_argument("--lang=ru-RU")
    return uc.Chrome(options=options, headless=True)

