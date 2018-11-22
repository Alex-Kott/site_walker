import logging
import random
from random import randint, choice
from time import sleep
from threading import Thread
from multiprocessing import Process
from datetime import datetime
from typing import List, Dict

from selenium.webdriver.common.keys import Keys
from selenium.webdriver import Chrome, ChromeOptions, DesiredCapabilities
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.proxy import ProxyType, Proxy as WebDriverProxy
from user_agent import generate_user_agent

from walker_panel.models import Task, Proxy, User, Log

# APP_PATH = '/home/alexkott/Documents/YouDo/site_walker/'
# APP_PATH = '/home/user/site_walker/'

logging.basicConfig(level=logging.ERROR,
                    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    datefmt='%m-%d %H:%M',
                    filename='./logs/log')
logger = logging.getLogger('site_walker')
logger.setLevel(logging.INFO)

SCREENSHOTS_DIR = './screenshots/'
YANDEX_URL = 'https://yandex.ru'


def get_random_screen_resolution() -> str:
    resolutions = ['1280,768',
                   '1280,800',
                   '1280,1024',
                   '1360,768',
                   '1366,768',
                   '1440,900',
                   '1536,864',
                   '1600,900',
                   '1680,1050',
                   '1920,1080',
                   '1920,1200',
                   '2560,1080',
                   '2560,1440']

    return random.choice(resolutions)


def generate_browser_configuration(task: Task) -> Dict[str, str]:
    config = {'user-agent': generate_user_agent(),
              'resolution': get_random_screen_resolution()}

    user_proxy_count = Proxy.objects.filter(owner=task.owner).count()

    if not user_proxy_count:
        return config

    proxy = choice(Proxy.objects.filter(owner=task.owner))
    config['proxy'] = f"http://{proxy.username}:{proxy.password}@{proxy.host}:{proxy.port}"

    return config


def change_region(driver: Chrome, region: str):
    driver.find_element_by_class_name('geolink').click()
    sleep(1)
    city_input = driver.find_element_by_id('city__front-input')
    city_input.clear()
    city_input.send_keys(region)
    sleep(1)
    city_input.send_keys(Keys.ENTER)
    sleep(1)


def is_competitor_site(url, competitor_sites):
    competitor_urls = competitor_sites.split('\r\n')
    for site in competitor_urls:
        if site.find(url) != -1:
            return True

    return False


class TaskRunner(Thread):
    def __init__(self, task: Task):
        Thread.__init__(self)
        self.task = task

    def run(self):
        user = self.task.owner
        log(user, f'Task {self.task.id} started. Target site: {self.task.target_url}')
        logger.info(f"Task {self.task.id} started. User: {user.username}, target site: {self.task.target_url}")
        browser_configuration = generate_browser_configuration(self.task)
        driver = get_driver(browser_configuration)
        driver.get(YANDEX_URL)

        if self.task.region.name != '':
            change_region(driver, self.task.region.name)

        driver.find_element_by_id('text').send_keys(self.task.search_query, Keys.ENTER)
        # driver.save_screenshot(SCREENSHOTS_DIR + f'screenshot_{datetime.now()}.png')
        sleep(2)

        result_items = driver.find_elements_by_class_name('serp-item')

        for item in result_items:
            links = item.find_elements_by_class_name('link_theme_outer')

            try:
                link = links[0]
            except:
                continue

            url = link.find_element_by_tag_name('b').get_attribute('innerText')

            sleep(1)

            log(user, f"Task {self.task.id}, visit url: {url}, target site: {self.task.target_url}, task {self.task.id}")

            logger.info(f"Task {self.task.id}, visit url: {url} User: {user.username}, target site: {self.task.target_url}")
            if self.task.target_url.find(url) != -1:

                link.click()
                driver.switch_to.window(driver.window_handles[-1])
                #  заходим на целевой сайт
                for i in range(5):
                    driver.execute_script(f"window.scrollTo(0, {randint(300, 700)});")
                    #driver.save_screenshot(SCREENSHOTS_DIR + f'screenshot_{datetime.now()}.png')
                    sleep(randint(12,24))
                sleep(30)



                break
            elif is_competitor_site(url, self.task.competitor_sites):

                link.click()
                driver.switch_to.window(driver.window_handles[-1])
                #  заходим к конкурентам
                for i in range(5):
                    sleep(randint(3, 5))
                    driver.execute_script(f"window.scrollTo(0, {randint(300, 800)});")

                driver.close()
                driver.switch_to.window(driver.window_handles[0])

        driver.close()


def get_driver(config: Dict) -> Chrome:
    options = ChromeOptions()
    capabilities = DesiredCapabilities.CHROME
    options.add_argument(f"--window-size={config['resolution']}")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--no-sandbox")
    options.add_argument(f"user-agent={config['user-agent']}")
    # options.add_argument("--window-position=1920,0")
    options.add_argument("--headless")

    if config.get('proxy'):
        proxy = WebDriverProxy({
            'proxyType': ProxyType.MANUAL,
            'httpProxy': config['proxy']
        })
        proxy.add_to_capabilities(capabilities)

    return Chrome("./webdriver/chromedriver", options=options,
                  desired_capabilities=capabilities)


def log(user: User, action: str):
    log_entry = Log(owner=user, action=action)
    log_entry.save()


def run():
    threads = {}
    for task in Task.objects.filter(status=True):
        print(task)
        threads[task.id] = TaskRunner(task=task)
        threads[task.id].daemon = True
        threads[task.id].start()

    for task_id, task_runner in threads.items():
        task_runner.join()

