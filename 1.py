from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time

# Настройка драйвера
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))

# Открытие страницы
driver.get("https://salesweb.civilview.com/Sales/SalesSearch?countyId=73")

# Даем время странице загрузиться (можно настроить по необходимости)
time.sleep(3)

# Сбор всех ссылок с таблицы
links = driver.find_elements(By.XPATH, '//table[@class="table table-striped "]/tr//a')

# Выводим все найденные ссылки
print(f"Найдено {len(links)} ссылок.")
for link in links:
    href = link.get_attribute('href')
    print(href)

    # Переходим по каждой ссылке
    driver.get(href)

    # Даем странице время загрузиться
    time.sleep(2)

    # Пример получения данных с новой страницы
    title = driver.title
    print(f"Заголовок страницы: {title}")

    # Вернуться к основной странице
    driver.back()

    # Даем время загрузиться основной странице
    time.sleep(2)

# Закрытие браузера
driver.quit()