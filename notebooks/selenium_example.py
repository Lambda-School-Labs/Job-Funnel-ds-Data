from selenium import webdriver
from selenium.webdriver.common.keys import Keys

browser = webdriver.Chrome()

browser.get('https://google.com')

que=browser.find_element_by_xpath("//input[@name='q']")
que.send_keys("Software testing")
que.send_keys(Keys.RETURN)
