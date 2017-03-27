#! python3

from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import csv
import time
import sys

PAGE_COUNT = 1          # Page count just for convenience.
# Path to PhantomJS executable.
phantom_path = r'D:\Soft\phantomjs-2.1.1-windows\bin\phantomjs'
# Url to scrape.
stats_url = 'http://stats.nhlnumbers.com/players'


def get_table_rows(webdriver, csvwriter):
    """ (WebDriver object, _csv.writer object) -> NoneType
    Search content of the page for 'player-data' table. Collect table's rows and write them in csv file.
    """
    global PAGE_COUNT
    try:
        soup = BeautifulSoup(webdriver.page_source, 'html.parser')
    except AttributeError:
        print('Was not able to parse content of the page. Stopping script execution.')
        webdriver.close()
        sys.exit()
    salary_table = soup.find('table', {'id': 'player-data'})
    rows = salary_table.find('tbody').findAll('tr')
    for row in rows:
        row_data = []
        for cell in row.findAll('td'):
            row_data.append(cell.get_text().strip())
        csvwriter.writerow(row_data)
    print('Page %s is collected.' % PAGE_COUNT)
    PAGE_COUNT += 1
    return


def wait_for_content(webdriver, id, timer=15.0, poll_frequency=0.5):
    """ (WebDriver object, str[, float, float]) -> NoneType
    Wait for page to load content with id we specified as function's argument.
    Stop script if time is out.
    """
    try:
        WebDriverWait(webdriver, timer, poll_frequency).until(EC.presence_of_element_located((By.ID, id)))
    except TimeoutException:
        print('Content on the page has not been loaded... Stopping script execution.')
        webdriver.close()
        sys.exit()


def main(phantomjs_path, url):
    """ (str, str) -> NoneType
    Set up web driver and csv writer. Iterate through table's pages, scrape and save data.
    """
    driver = webdriver.PhantomJS(executable_path=phantomjs_path)
    try:
        driver.get(url)
    except WebDriverException:
        print("Url was not accessible. Stopping script execution.")
        driver.close()
        sys.exit()
    wait_for_content(driver, 'player-data')
    # time.sleep(1)
    # Select per page display option with most rows.
    try:
        driver.find_element_by_css_selector(".per-page > option:nth-child(4)").click()
        time.sleep(1)
    except NoSuchElementException:
        print('Per page display option element was not accessible. Proceeding with default per page display value.')
    # Open csv file and set up csv writer.
    csv_file = open('salaries_data.csv', 'w', encoding='utf-8', newline='')
    writer = csv.writer(csv_file, delimiter=';')
    # Collect header of the table and write it into csv file.
    try:
        headers = BeautifulSoup(driver.page_source, 'html.parser').find('table', {'id': 'player-data'}).find\
            ('thead').findAll('tr')
        header = [i.get_text().strip() for i in headers[1].findAll('th')]
        # Adjust header's column descriptions.
        for i in range(3, 5):
            header[i] += ' Cap Hit'
        for i in range(5, len(header)):
            header[i] += ' Salary'
        # Write header into table.
        writer.writerow(header)
    except AttributeError:
        print('Can not parse header content of the table. Trying to collect data without table header.')
    try:
        # Write in table rows on the first page of table.
        get_table_rows(webdriver=driver, csvwriter=writer)
        # Click on 'next page' button and write new table rows until end of table is reached and button is disabled.
        while not driver.find_elements_by_css_selector('div.paginate-next.paginate-disabled'):
            driver.find_element_by_css_selector('div.paginate-next').click()
            # Wait for dynamic content of table to change.
            time.sleep(0.5)
            get_table_rows(webdriver=driver, csvwriter=writer)
        print('Done.')
    finally:
        # Close csv writer end web driver.
        csv_file.close()
        driver.close()

if __name__ == '__main__':
    main(phantom_path, stats_url)




