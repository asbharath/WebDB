import glob
import os
import logging
import time
import requests
from random import randint

from tqdm import tqdm
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.common.exceptions import NoSuchElementException

logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4422.0 Safari/537.36"


def open_file(file):
    """open file for reading or writing depending on the flag

    Args:
        file (str): File to be opened

    Returns:
        list: Returns a list containing the data read from the given file
    """
    assert os.path.isfile(file), f"{file} not a file"
    with open(file) as f:
        return f.read().splitlines()


class ImageScraper:
    def __init__(self, query, save_img_dir, index, num_of_images, run_headless):
        """Initialize the variables

        Args:
            query (str): search query
            save_img_dir (str): directory name where the images are saved
            index (str): used in formatting the file name
            run_headless (bool): run the script without launching the firefox browser
        """
        self.query = query
        self.save_img_dir = save_img_dir.replace(" ", "_")  # replace space with _
        str_replace = query.replace(" ", "_")
        self.num_of_images = num_of_images
        self.file_format = f"{index}_{self.search_engine}_{str_replace}"
        self.driver = self.get_webdriver(run_headless)
        self.images = list()
        self.wait = WebDriverWait(self.driver, timeout=5)
        os.makedirs(self.save_img_dir, exist_ok=True)  # create save_img_dir
        self.links_file = os.path.join(self.save_img_dir, "links.txt")
        if not os.path.isfile(self.links_file):  # create empty file if links.txt file not found within directory
            open(self.links_file, "w").close()
            self.list_of_links = list()
        else:
            self.list_of_links = open_file(self.links_file)
        self.counter = 0

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
        profile.set_preference("general.useragent.override", USER_AGENT)

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

        # Scroll one last time
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

    def get_image(self, url, image_file):
        """Sends a GET request with the image URL provided and saves the image.

        Args:
            url (str): image url
            image_file (str): image file name
        """
        img_request = requests.request("GET", url, headers={"User-Agent": USER_AGENT})
        with open(image_file, "wb") as f:
            f.write(img_request.content)

    def download_images(self):
        """Retrives images from the image url list and downloads one by one.

        Returns:
            int: Total number of images downloaded
        """
        logging.info("checking for duplicate urls...")
        logging.info(f"Total duplicate URLs {len(self.images) - len(set(self.images))}")
        self.images = set(self.images)  # remove the duplicates
        if self.images:  # if list has links, download the images
            index = self.get_file_index()  # get the corresponding index
            failure_count = 0
            success_count = 0
            write_links_file = open(self.links_file, 'a')
            for image_url in tqdm(self.images, desc="Downloading images", ascii=True, ncols=100):
                file_name = os.path.join(self.save_img_dir, f"{self.file_format}_{str(index).zfill(5)}.jpg")
                try:
                    self.get_image(image_url, file_name)
                    success_count += 1
                    index += 1
                    write_links_file.writelines(f"\n{image_url}")  # append the image url in the links.txt file
                except Exception as e:
                    logging.error(f"{e}, image URL: {image_url}")
                    failure_count += 1
            write_links_file.close()
            logging.info(f"Failed to retrieve {failure_count} images")
            logging.info(f"Total number of images downloaded: {success_count}")
        else:
            logging.info(f"No new images found!!")

    def get_file_index(self):
        """function checks whether files are present for the given search engine and query
        if files are found, gets the max number from file name else return index 1

        Returns:
            int: max number from the file name or 1
        """
        file_path = os.path.join(self.save_img_dir, self.file_format) + "*"
        list_of_files = glob.glob(file_path)
        if not list_of_files:  # Empty list returns False
            return 1  # index set to 1
        else:
            list_of_files.sort()  # sort by ascending order
            last_file = list_of_files[-1]  # get the last file
            index = last_file.split("_")[-1].split(".")[0]  # gives 99 from 0_yahoo_some_query_99.jpg
            return int(index)

    def get_url(self):
        """format the url and navigate to it.
        """
        url = self.url + "?q=" + self.query
        if "google" in self.search_engine:
            url = url + "&tbm=isch"  # this is required to display image search results page for google.
        logging.info(url)
        logging.info(f"Total number of images to be scraped: {self.num_of_images}")
        self.driver.get(url)

    def click_button(self, locator):
        """function tries to find the locator passed and clicks on it

        Args:
            locator (str): locator tag that uniquely identifies an element in the DOM
        """
        try:
            button = self.driver.find_element_by_css_selector(locator)
            if button.is_displayed():
                button.click()
                time.sleep(1)
        except NoSuchElementException:
            logging.error(f"Element with locator {locator} not found!")

    def load_all_images(self):
        """scrolls down to load the dynamic webpage and clicks on the load more image button when found
        """
        self.scroll_down()
        try:
            button_tag = self.driver.find_element_by_css_selector(self.see_more_image_button_tag)
        except NoSuchElementException:
            logging.error(f"Element accessed using tag [{self.see_more_image_button_tag}] not found!")

        while button_tag.is_displayed():
            # click the button "see more images"
            self.click_button(self.see_more_image_button_tag)
            # Scroll till end.
            self.scroll_down()
            # break the loop if button not present
            if not button_tag.is_displayed():
                break

    def get_all_elements_from_image_thumbnail(self):
        """Gets all the webdriver elements from the image thumbnails in the search results page.

        Returns:
            list: List containing all the webdriver elements for the page
        """
        try:
            list_of_elements = self.driver.find_elements_by_css_selector(self.image_thumbnail_tag)
        except Exception as e:
            logging.error(f"Error in getting the elements from image thumbnails {e}")
        return list_of_elements

    def scrape(self):
        raise NotImplementedError("Override this method!!")


class BingImageScraper(ImageScraper):
    def __init__(self, *args, **kwargs):
        self.search_engine = "bing"
        self.url = "https://www.bing.com/images/search"
        self.search_results_tag = "div.dg_b"
        self.image_thumbnail_tag = "img.mimg"
        self.iframe_locator_tag = "iframe.insightsOverlay"
        self.full_res_image_tag = "img.nofocus"
        self.button_close_iframe_tag = "div.close.nofocus"
        self.next_image = "div#navr"
        super().__init__(*args, **kwargs)

    def scrape(self):
        """Bing Image scrape function
        """
        self.get_url()
        assert self.driver.find_element_by_css_selector(self.search_results_tag).is_displayed(), f"Search results did not load!"

        try:
            # click the first image
            self.driver.find_element_by_css_selector(self.image_thumbnail_tag).click()
            # find the iframe
            frame_locator = self.driver.find_element_by_css_selector(self.iframe_locator_tag)
            # switch to iframe containing image carasoul
            self.wait.until(expected_conditions.frame_to_be_available_and_switch_to_it(frame_locator))
            time.sleep(1)
            # next image button
            next_image = self.driver.find_element_by_css_selector(self.next_image)
            while next_image.is_displayed():  # loop until next image button is no longer visible
                try:
                    image = self.driver.find_element_by_css_selector(self.full_res_image_tag)
                    img_src = image.get_attribute('src')
                    if img_src is not None:
                        if "http" in img_src and img_src not in self.list_of_links:
                            self.images.append(img_src)
                except Exception as e:
                    logging.error(f"Not able to get src attribute {e}")
                next_image.click()
                self.counter += 1
                # break the loop when number of images is equal to scraped images
                if self.counter > self.num_of_images:
                    break
            self.click_button(self.button_close_iframe_tag)  # click the close button on the iframe
            self.driver.switch_to_default_content()  # switch context to the original window
        except Exception as e:
            logging.error(f"Failed to retrieve image! {e}")
        logging.info(f"Total number of new images found: {len(self.images)}")

        # clean up
        self.driver.delete_all_cookies()
        self.driver.close()

        self.download_images()


class GoogleImageScraper(ImageScraper):
    def __init__(self, *args, **kwargs):
        self.search_engine = "google"
        self.url = "https://www.google.com/search"
        self.search_results_tag = "div.T1diZc.KWE8qe"
        self.see_more_image_button_tag = ".mye4qd"
        self.image_thumbnail_tag = "img.rg_i.Q4LuWd"
        self.full_res_image_tag = "img.n3VNCb"
        self.next_image = "a.gvi3cf"  # This button is not recognized after the first loop.
        super().__init__(*args, **kwargs)

    def scrape(self):
        """Google Image scrape function
        """
        self.get_url()
        assert self.driver.find_element_by_css_selector(self.search_results_tag).is_displayed(), f"Search results did not load!"
        # scroll and get more image link in the webpage
        self.load_all_images()
        list_of_elements = self.get_all_elements_from_image_thumbnail()
        logging.info(f"total thumbnail images present {len(list_of_elements)}")

        for element in tqdm(list_of_elements, desc="Scraping google images", ascii=True, ncols=100):
            try:
                element.click()
                time.sleep(0.5)
                try:
                    # 3 images are retrieved and one of them containing 'jpg' has full image resolution.
                    images = self.driver.find_elements_by_css_selector(self.full_res_image_tag)
                    for image in images:
                        img_src = image.get_attribute('src')
                        if img_src is not None:
                            if "jpg" in img_src and img_src not in self.list_of_links:
                                self.images.append(img_src)
                except Exception as e:
                    logging.error(f"Not able to get src attribute {e}")
            except Exception as e:
                logging.error(f"Failed to retrieve image! {e}")
            self.counter += 1
            # break the loop when number of images is equal to scraped images
            if self.counter > self.num_of_images:
                break
        logging.info(f"Total number of new images found: {len(self.images)}")

        # clean up
        self.driver.delete_all_cookies()
        self.driver.close()

        self.download_images()


class YahooImageScraper(ImageScraper):
    def __init__(self, *args, **kwargs):
        self.search_engine = "yahoo"
        self.url = "https://images.search.yahoo.com/search/images"
        self.search_results_tag = "section#mdoc"
        self.see_more_image_button_tag = ".ygbt.more-res"
        self.image_thumbnail_tag = "li[id*=resitem-]"
        self.full_res_image_tag = "a img"
        super().__init__(*args, **kwargs)

    def scrape(self):
        """Yahoo Image scrape function
        """
        self.get_url()

        # Yahoo refuse cookie on the initial popup
        try:
            if self.driver.find_element_by_css_selector("form.consent-form").is_displayed():
                # agree to consent! Easier to click "Agree" than to disagree :-(
                self.driver.find_element_by_name('agree').click()
                # wait till the search is complete
                self.wait.until(expected_conditions.title_contains("Yahoo Image Search Results"))
        except NoSuchElementException:
            logging.info("button not found, proceeding..")

        assert self.driver.find_element_by_css_selector(self.search_results_tag).is_displayed(), f"Search results did not load!"

        # Yahoo the button is always visible, so we can't use load_all_images function
        while self.driver.find_element_by_css_selector(self.see_more_image_button_tag).is_displayed():
            self.scroll_down()
            self.click_button(self.see_more_image_button_tag)
            # this is necessary so that last image thumbnails loads without failing.
            self.scroll_down()

        list_of_elements = self.get_all_elements_from_image_thumbnail()
        logging.info(f"total thumbnail images present {len(list_of_elements)}")

        for element in tqdm(list_of_elements, desc="Scraping yahoo images", ascii=True, ncols=100):
            try:
                images = element.find_elements_by_css_selector(self.full_res_image_tag)
                if not images:
                    continue
                # 1st index is the source image with high resolution
                img_src = images[0].get_attribute('src')
                if img_src is not None:
                    if "http" in img_src and img_src not in self.list_of_links:
                        img_src = img_src.split("&")[0]  # strip everything after & to get full resolution link
                        self.images.append(img_src)
            except Exception as e:
                logging.error(f"not able to get src attribute {e}")
            self.counter += 1
            # break the loop when number of images is equal to scraped images
            if self.counter > self.num_of_images:
                break

        # clean up
        self.driver.delete_all_cookies()
        self.driver.close()

        logging.info(f"Total number of new images found: {len(self.images)}")
        self.download_images()
