#
import time

import selenium.webdriver
from selenium import webdriver


def add_single_page(driver, th_list):
    time.sleep(2)
    els = driver.find_elements('xpath', '//*[@id="page-series-detail"]/div/div/div/ul/li/a[2]')
    for el in els:
        base_info = {}
        base_info['href'] = el.get_attribute('href')
        base_info['title'] = el.get_attribute('title')

        th_list.append(base_info)


class BiliBiliSeries:
    def __init__(self, uid: str, sid: str):
        self.uid = uid
        self.sid = sid

    @property
    def videos(self):
        th_list = []

        try:
            driver = webdriver.Chrome()
            driver.implicitly_wait(2)  # seconds

            url = 'https://space.bilibili.com/{}/channel/seriesdetail?sid={}'.format(self.uid, self.sid)
            driver.get(url)

            # Pre Page
            while len(driver.find_elements('xpath',
                                           "//li[@title='下一页'][not(contains(@class, 'be-pager-disabled'))]")) > 0:
                add_single_page(driver, th_list)
                # Click Next Page Button
                driver.find_element('xpath', "//li[@title='下一页']").click()

            # Last Page
            add_single_page(driver, th_list)

            return th_list

        finally:
            driver.quit()


class BiliBiliVideo:

    def __init__(self, bv: str, driver: webdriver.Chrome):
        self.bv = bv
        self.driver = driver

    @property
    def sub_video_list(self):
        self.driver.get('https://www.bilibili.com/video/{}'.format(self.bv))

        multi_page_els = self.driver.find_elements('xpath', '//*[@id="multi_page"]')
        if len(multi_page_els) == 0:
            # SINGLE VIDEO
            title = self.driver.find_element('xpath', '//*[@id="viewbox_report"]/h1').get_attribute('title')
            state_map = {'multi_page': False, 'sub_videos': [{'title': title}]}
        else:
            # MULTIPLE VIDEOS
            li_els = self.driver.find_elements('xpath', '//*[@id="multi_page"]/div[2]/ul/li')
            state_map = {'multi_page': True, 'sub_videos': []}
            for li_el in li_els:
                title = li_el.find_element('xpath', './/a/div/div[1]/span[2]').text
                state_map['sub_videos'].append({'title': title})

        return state_map
