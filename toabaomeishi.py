import re
import pymongo
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from pyquery import PyQuery as py
from config import *

client = pymongo.MongoClient(MONGO_URL)
db = client[MONGO_DB]
brower = webdriver.Chrome()
wait = WebDriverWait(brower, 10)


def save_to_mongodb(product):
    try:
        if db[MONGO_TABLE].insert(product):
            print('保存成功')
            return True
        else:
            return False
    except Exception as e:
        print("保存失败", product)


def search():
    brower.get('http://www.taobao.com')
    try:
        input = wait.until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#q'))
        )

        submit = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, '#J_TSearchForm > div.search-button > button'))
        )
        input[0].send_keys("美食")
        submit.click()
        total = wait.until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#mainsrp-pager > div > div > div > div.total'))
        )
        get_products()
        return total[0].text
    except TimeoutException as e:
        search()


def next_page(page_number):
    try:
        input = wait.until(
            EC.presence_of_all_elements_located(
                (By.CSS_SELECTOR, '#mainsrp-pager > div > div > div > div.form > input'))
        )

        submit = wait.until(
            EC.element_to_be_clickable(
                (By.CSS_SELECTOR, '#mainsrp-pager > div > div > div > div.form > span.btn.J_Submit'))
        )
        input[0].clear()
        input[0].send_keys(page_number)
        submit.click()
        wait.until(
            EC.text_to_be_present_in_element(
                (By.CSS_SELECTOR, '#mainsrp-pager > div > div > div > ul > li.item.active > span'), str(page_number))
        )
        get_products()
    except TimeoutException as e:
        next_page(page_number)


def get_products():
    wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#mainsrp-itemlist .items .item')))
    html = brower.page_source
    doc = py(html)
    items = doc('#mainsrp-itemlist .items .item').items()
    for item in items:
        product = {
            'image': item.find('.pic .img').attr('src'),
            'price': item.find('.price').text().replace('\n', ''),
            'deal': item.find('.deal-cnt').text()[:-3].replace('\n', ''),
            'title': item.find('.title').text().replace('\n', ''),
            'shop': item.find('.shop').text().replace('\n', ''),
            'location': item.find('.location').text().replace('\n', '')
        }
        save_to_mongodb(product)


def main():
    try:
        total = search()
        total = int(re.search('(\d+)', total).group(1))
        for num in range(2, total + 1):
            next_page(num)
    except Exception:
        pass
    finally:
        brower.close()


if __name__ == '__main__':
    main()
