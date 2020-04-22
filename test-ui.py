#!/usr/bin/python

"""To be used with docker compose"""

import selenium
from selenium.webdriver.chrome.options import Options
from selenium.webdriver import Chrome
from selenium.webdriver.support.ui import WebDriverWait as webdriverwait
import selenium.webdriver.support.expected_conditions as ec
from selenium.webdriver.common.by import By as by

import time, logging, copy, os

WAIT_TIME = 15 or os.environ.get('WAIT_TIME')
MAX_RETRIES = 5 or os.environ.get('MAX_RETRIES')
JUPYTER_TOKEN = os.environ.get('JUPYTER_TOKEN')
SERVICE_NAME = 'jupyter' or os.environ.get('SERVICE_NAME')

if __name__ == '__main__':
    # setup the logger
    try:

        logger = logging.getLogger('selenium_ui')
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        
        logger.setLevel(logging.INFO)
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        ch.setFormatter(formatter)
        logger.addHandler(ch)
        
        fh = logging.FileHandler('/opt/datahub/ui-test.log')
        fh.setLevel(logging.INFO)
        fh.setFormatter(formatter)
        logger.addHandler(fh)

        # initialize the driver options and connect to the notebook
        options = Options()
        options.headless = True
        options.add_argument('--window-size=1920x1480')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-extensions')
        options.add_argument("--proxy-server='direct://'")
        options.add_argument('--proxy-bypass-list=*')
        options.add_argument('--start-maximized')
        options.add_argument("disable-infobars")
        options.add_argument('--ignore-ssl')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        
        browser = Chrome(options=options)
    
        # give it some time for nbconvert to run and to spin up notebook server
        current_retries = 0
        while True:
            
            if current_retries == MAX_RETRIES:
                raise Exception('Max retry limit hit, could not connect to jupyter server')
            
            baseurl = 'http://{SERVICE_NAME}:8888'
            if JUPYTER_TOKEN:
                browser.get(f'{baseurl}?token={JUPYTER_TOKEN}')
            else:
                browser.get({baseurl})
            
            if browser.page_source != '<html><head></head><body></body></html>':
                break
            
            current_retries += 1
            logger.info('Could not connect to server yet... Retry count = {0}'.format(current_retries))
            logger.info(browser.page_source)
            time.sleep(WAIT_TIME)

        logger.info('Connected to jupyter notebook')

        # check only 1 tab
        assert len(browser.window_handles) == 1

        logger.info('Checking DSMLP cluster status')
        cluster_status_link = webdriverwait(browser, WAIT_TIME).until(
            ec.presence_of_element_located((by.LINK_TEXT, 'DSMLP Cluster Status'))
        )
        cluster_status_link.click()
        logger.info('DSMLP cluster status ok')
        
        logger.info('Checking nbgrader')
        courses_link = webdriverwait(browser, WAIT_TIME).until(
            ec.presence_of_element_located((by.LINK_TEXT, 'Courses'))
        )
        courses_link.click()
        logger.info('nbgrader ok')
        
        # navigate back to the files tab
        files_link = webdriverwait(browser, WAIT_TIME).until(
            ec.presence_of_element_located((by.LINK_TEXT, 'Files'))
        )
        files_link.click()
        
        # select the new button + create a python notebook
        logger.info('Checking python notebook')
        new_button = webdriverwait(browser, WAIT_TIME).until(
            ec.element_to_be_clickable((by.ID, 'new-dropdown-button'))
        )
        new_button.click()
        
        create_py3_notebook = webdriverwait(browser, WAIT_TIME).until(
            ec.element_to_be_clickable((by.LINK_TEXT, 'Python 3'))
        )
        create_py3_notebook.click()
        logger.info('Python notebook created')
        
        time.sleep(2)
        
        # check new tab with py notebook
        assert len(browser.window_handles) == 2
        notebook = browser.window_handles[-1]
        browser.switch_to.window(notebook)
        
        # check nbresuse
        logger.info('Checking nbresuse')
        nbresuse_btn = webdriverwait(browser, WAIT_TIME).until(
            ec.element_to_be_clickable((by.XPATH, '//*[@id="collect_metrics"]'))
        )
        nbresuse_btn.click()
        logger.info('nbresuse ok')
        
        # select the quit button
        logger.info('Checking the quit button')
        file = browser.window_handles[0]
        browser.switch_to.window(file)
        quit_btn = webdriverwait(browser, WAIT_TIME).until(
            ec.element_to_be_clickable((by.ID, 'shutdown'))
        )
        quit_btn.click()
        logger.info('Exited the notebook server')
        
        logger.info('UI testing all pass!')

    except Exception as e:
        
        logger.error('failed selenium acceptance testing')
        logger.error(e)
        raise e
