import argparse
import glob
import os
import requests
import sys
import time
import urllib
from random import randint
from urllib.request import urlopen

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.wait import WebDriverWait
from selenium.common.exceptions import NoSuchElementException

from utils import scroll_till_element_is_found,

parser = argparse.ArgumentParser()
parser.add_argument("--search_engine", type=str, default='all', help='Search for images using a specific or all search engines.')
parser.add_argument("--query", type=str, help='query for which images are searched and downloaded')
parser.add_argument("--save_image_path", type=str, help='path to save the downloaded images')
parser.add_argument("--get_high_res_images", type=bool, help='Search and get the original image source which could be higher resolution')
parser.add_argument("--get_extra_images", type=bool, default=False, help='Scroll to end by loading all possible images and click on button to load more images')
parser.add_argument("--run_headless", type=bool, default=True, help='Runs the script on browser without displaying the browser in GUI.')
parser.add_argument("--script_sleep_time", type=float, default=2, help='Script sleep time to wait for page to load especially when scrolling.')
args = parser.parse_args()

MAP_URLS = {
    bing: "https://www.bing.com/images/search",
    google: "https://www.google.com/search",
    yahoo: "https://images.search.yahoo.com/search/images"
}

os.makedirs(args.save_image_path, exist_ok=True)
if len(os.listdir(args.save_image_path)) > 0:
    print("Directory contains data...Exiting.")
    sys.exit()

# if args.search_engine.lower() == "all":
#     args.search_engine = MAP_URLS.keys()  # include search engines
# else:
#     args.search_engine = list(args.search_engine)  # Convert to list


image_file_name = index + "_" + args.search_engine + "_" + args.query + "_" str(i) + ".jpg"
image_path = os.path.join(args.save_image_path, image_file_name)


def get_url(query):
    # Append the user provided search query
    url = MAP_URLS[engine] + "?q=" + query
    if "google" in engine:
        url = url + "&tbm=isch"  # this is required to display image page.
    return url


def get_css_locators(search_engine):
    get_css = {
        bing = {
            "more_results_button": ".btn_seemore cbtn mBtn",
            "end_of_page": "div.OuJzKb.Yu2Dnd"
        },
        google = {
            "more_results_button": ".mye4qd",
            "end_of_page": "div.OuJzKb.Yu2Dnd"
        },
        yahoo = {
            "more_results_button": ".mye4qd",
            "end_of_page": "div.OuJzKb.Yu2Dnd"
        }
    }
    return get_css[search_engine]


def scrape_images_from_google(args):
    chrome_options = Options()

    if args.run_headless:
        chrome_options.add_argument("--headless")

    driver = webdriver.Chrome(options=chrome_options)
    count = 0
    url = get_url(args.query)
    print(url)
    driver.get(url)
    css_tags = get_css_locators(args.search_engine)
    more_results_button = driver.find_element_by_css_selector(".mye4qd")  # CSS selector for 
    scroll_till_element_found(more_results_button)

    try:
        more_results_button.click()
        end_of_search = driver.find_element_by_css_selector("div.OuJzKb.Yu2Dnd")
        scroll_till_element_found(end_of_search)
    except NoSuchElementException:
        print("Element not found.")

    if end_of_search.is_displayed():
        print("Reached the end of page")

def download_images():
    pass


def scroll_to_end(args, driver):
    time.sleep(randint(2, 5))  # random wait to mimic human behavior
    driver.find_element_by_tag_name('body').send_keys(Keys.END)


def main(args):

    list_of_image_links = {}

    url = get_url(args.search_engine)
    driver.get(url)
    for _ in range(1, 10):  # TODO add this as a variable
        scroll()
    try:
        more_results = driver.find_element_by_class_name("")
        more_results.click()
        for _ in range(1, 10):  # TODO add this as a variable
            scroll()

    # for engine in args.search_engine:
    #     list_of_image_links[engine] = get_list_of_images(args)
   

if __name__ == "__main__":
    main(args)

