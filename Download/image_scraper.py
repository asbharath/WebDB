import argparse
import glob
import os
import logging
import requests
import sys
import time
import urllib
from random import randint
from urllib.request import urlretrieve, urlcleanup

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.common.exceptions import NoSuchElementException

logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)


class ImageScraper:
    def __init__(self, query, save_img_dir, index, run_headless):
        self.query = query
        self.save_img_dir = save_img_dir
        str_replace = query.replace(" ", "_")
        self.file_format = f"{index}_{self.search_engine}_{str_replace}"
        print(self.file_format)
        self.check_directory_contains_data()
        self.driver = self.get_webdriver(run_headless)
        self.images = list()

    def get_webdriver(self, headless):
        """Instantiate firefox webdriver.
        useful link to change User-Agent if required: https://developers.whatismybrowser.com/
        # TODO plan to use this https://github.com/SergeyPirogov/webdriver_manager

        Args:
            headless (bool): When the flag is True scripts runs without invoking the browser

        Returns:
        Webdriver : A webdriver object used crawl webpages.
        """
        browser_options = Options()
        if headless:
            browser_options.add_argument("--headless")

        profile = webdriver.FirefoxProfile()
        profile.set_preference("general.useragent.override",
                               "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36")
        #  "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36")

        # create webdriver Firefox instance
        driver = webdriver.Firefox(options=browser_options, firefox_profile=profile)
        return driver

    def scroll_down(self):
        # code from https://stackoverflow.com/questions/48850974/selenium-scroll-to-end-of-page-in-dynamically-loading-webpage
        """A method for scrolling the page."""

        # Get scroll height.
        last_height = self.driver.execute_script("return document.body.scrollHeight")

        while True:
            # Scroll down to the bottom.
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

            # Wait for the page to load.
            time.sleep(randint(2, 7))

            # Calculate new scroll height and compare with last scroll height.
            new_height = self.driver.execute_script("return document.body.scrollHeight")

            if new_height == last_height:
                break
            last_height = new_height

    def download_images(self):
        logging.info("checking for duplicate urls...")
        logging.info(f"Total duplicate URLs {len(self.images) - len(set(self.images))}")
        self.images = set(self.images)  # remove the duplicates
        logging.info("Downloading images..")
        count = 0
        for index, image_url in enumerate(self.images):
            image_file = os.path.join(self.save_img_dir, f"{self.file_format}_{str(index)}.jpg")
            try:
                urlretrieve(image_url, image_file)
                time.sleep(0.5)
            except Exception as e:
                logging.error(e)
                count += 1
        urlcleanup()
        logging.info(f"Failed to retrieve {count} images")
        return str(index + 1)

    def check_directory_contains_data(self):
        # Exit if directory contains data.
        os.makedirs(self.save_img_dir, exist_ok=True)
        file_path = os.path.join(self.save_img_dir, self.file_format) + "*"
        logging.info(file_path)
        if len(glob.glob(file_path)) > 0:
            logging.info(f"Directory {file_path} contains data...Exiting.")
            sys.exit()

    def prepare_url(self):
        url = self.url + "?q=" + self.query
        if "google" in self.search_engine:
            url = url + "&tbm=isch"  # this is required to display image page for google.
        return url

    def click_button(self, locator):
        """function tries to find the locator passed and clicks on it

        Args:
            locator (str): locator tag that uniquely identifies an element in the DOM
        """
        try:
            self.driver.find_element_by_css_selector(locator).click()
        except NoSuchElementException:
            logging.error(f"Element with locator {locator} not found!")

    def load_all_images(self):
        while not self.driver.find_element_by_css_selector(self.see_more_image_button_tag).is_displayed():
            # Scroll till end.
            self.scroll_down()
            # break the loop if button not present
            if not self.driver.find_element_by_css_selector(self.see_more_image_button_tag).is_displayed():
                break
            # click the button "see more images"
            self.click_button(self.see_more_image_button_tag)

    def get_full_resolution_images(self, driver, list_of_elements):
        """A common function to get the urls for the maximum resolution possible.
        TODO if its gets too messy, separate this method to each of the search engines.

        Args:
            driver (WebDriver): webdriver. This method requires to handle the special case of Yahoo.
            list_of_elements (list): list of elements containing the base Image url.
        """
        for element in list_of_elements:
            try:
                if "yahoo" in self.search_engine:
                    driver = element  # short circuit # TODO find a better way to handle this
                elif "bing" in self.search_engine:
                    element.click()
                    time.sleep(1)  # Wait for the overlay iframe to open.
                    # Below works fine and switches to the right iframe
                    driver.switch_to.frame(driver.find_elements_by_tag_name("iframe")[0])
                    # driver.switch_to_frame(iframe_list[0])
                elif "google" in self.search_engine:
                    element.click()
                else:
                    raise ValueError(f"Invalid search engine: {self.search_engine}")

                # bing special case
                if "bing" in self.search_engine:
                    # convert to list so that look doesn't break
                    img_list = [driver.find_element_by_css_selector(self.full_res_image_tag)]
                else:
                    img_list = driver.find_elements_by_css_selector(self.full_res_image_tag)

                for image in img_list:
                    try:
                        img_src = image.get_attribute('src')
                        if img_src is not None:
                            if "http" in img_src and img_src not in self.images:
                                if "yahoo" in self.search_engine:
                                    img_src = img_src.split("&")[0]  # strip everything after & to get full resolution link
                                    # img_src = img_src + "&w=1000&h=1000"
                                self.images.append(img_src)
                    except Exception as e:
                        logging.error(f"Not able to get src attribute {e}")
                if "bing" in self.search_engine:
                    # driver.switch_to_frame(2)
                    # driver.switch_to_window("Bing ")
                    # FIXME Doesn't work, Ideally driver should get control over the original page.
                    # This doesn't happen for some reason which is to be identified.
                    driver.switch_to_default_content()
            except Exception as e:
                logging.error(f"Failed to retrieve image! {e}")

    def scrape(self):
        url = self.prepare_url()
        logging.info(url)
        self.driver.get(url)

        if "yahoo" in self.search_engine:
            self.click_button(self.refuse_consent)
            # wait till the search is complete
            WebDriverWait(self.driver, timeout=5).until(expected_conditions.title_contains("Yahoo Image Search Results"))

        assert self.driver.find_element_by_css_selector(self.search_results_tag).is_displayed(), f"Search results did not load!"

        # scroll and get more image link in the webpage
        self.load_all_images()

        try:
            elements = self.driver.find_elements_by_css_selector(self.image_thumbnail_tag)
        except Exception as e:
            logging.error(e)

        # logging.info(len(elements))
        # elements = elements[:5]

        self.get_full_resolution_images(self.driver, elements)
        # close driver
        self.driver.close()

        # logging.info(self.images)
        logging.info(f"Total number of images found: {len(self.images)}")

        total_image_downloaded = self.download_images()
        logging.info(f"Total number of images downloaded: {total_image_downloaded}")


class BingImageScraper(ImageScraper):
    def __init__(self, *args, **kwargs):
        self.search_engine = "bing"
        self.url = "https://www.bing.com/images/search"
        self.search_results_tag = "div.dg_b"
        self.see_more_image_button_tag = "a.btn_seemore.cbtn.mBtn"
        self.image_thumbnail_tag = "img.mimg"
        self.full_res_image_tag = "img.nofocus"
        self.close_frame = "div.close.nofocus"
        super().__init__(*args, **kwargs)


class GoogleImageScraper(ImageScraper):
    def __init__(self, *args, **kwargs):
        self.search_engine = "google"
        self.url = "https://www.google.com/search"
        self.search_results_tag = "div.T1diZc.KWE8qe"
        self.see_more_image_button_tag = ".mye4qd"
        self.image_thumbnail_tag = "div.isv-r.PNCib.MSM1fd.BUooTd"
        self.full_res_image_tag = "img.n3VNCb"
        super().__init__(*args, **kwargs)


class YahooImageScraper(ImageScraper):
    def __init__(self, *args, **kwargs):
        self.search_engine = "yahoo"
        self.url = "https://images.search.yahoo.com/search/images"
        self.refuse_consent = ".btn.secondary.reject-all"
        self.search_results_tag = "section#mdoc"
        self.see_more_image_button_tag = ".ygbt.more-res"
        self.image_thumbnail_tag = "li[id*=resitem-]"
        self.full_res_image_tag = "a img"
        super().__init__(*args, **kwargs)
