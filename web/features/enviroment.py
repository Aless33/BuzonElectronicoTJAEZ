import django
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import os

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "buzon_electronico_tjaez.settings"
)


def before_all(context):
    django.setup()
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1366,768")
    context.browser = webdriver.Chrome(options=chrome_options)
    context.browser.implicitly_wait(5)


def after_all(context):
    context.browser.quit()
