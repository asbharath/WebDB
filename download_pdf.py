import time
from pathlib import Path
from random import randint
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
import yaml

from Download.image_scraper import ImageScraper

class PDFScraper(ImageScraper):
    def __init__(self, *args, **kwargs):
        self.search_engine = None
        super().__init__(*args, **kwargs)

scraper = PDFScraper(query="test", save_img_dir="test", index=None, num_of_images=None, run_headless=False)

url = "https://learn.lingoda.com/en/login"

with open("settings.yaml") as f:
    settings = yaml.safe_load(f)

username = settings["username"]
password = settings["password"]

lingoda_url = scraper.driver.get(url)
login_user_tag = "input[name='username']"
login_password_tag = "input[name='password']"
login_button_tag = "button"
cookie_button_tag = "button#onetrust-accept-btn-handler"
my_course_tag = "a.MuiTypography-root[href*='course-overview']"
download_button_tag = "a.MuiTypography-root[href$='download']"
lesson_list_tag = "a.MuiTypography-root[href*='lesson']"

save_base_path = Path(settings["folder_path"])
courses_list = [
    "A1.1",
    "A1.2",
    "A2.1",
    "A2.2",
    "B1.1",
    "B1.2",
    "B1.3",
    "B2.1",
    "B2.2",
    "B2.3",
]
total_course_list = ["https://learn.lingoda.com/en/account/course-overview/"+x for x in courses_list]
# find the username and input to the screen
login_user = scraper.driver.find_element(By.CSS_SELECTOR, login_user_tag)
login_user.send_keys(username)

# find the password and input to the screen
login_user = scraper.driver.find_element(By.CSS_SELECTOR, login_password_tag)
login_user.send_keys(password)

# Accept cookies
scraper.wait.until(expected_conditions.visibility_of_element_located((By.CSS_SELECTOR, cookie_button_tag)))
scraper.driver.find_element(By.CSS_SELECTOR, cookie_button_tag).click()

time.sleep(randint(2, 4))
scraper.wait.until(expected_conditions.visibility_of_element_located((By.CSS_SELECTOR, login_button_tag)))
scraper.driver.find_element(By.CSS_SELECTOR, login_button_tag).click()

scraper.wait.until(expected_conditions.visibility_of_element_located((By.CSS_SELECTOR, my_course_tag)))
scraper.driver.find_element(By.CSS_SELECTOR, my_course_tag).click()

time.sleep(randint(2, 4))
for course in total_course_list:
    scraper.driver.get(course)
    scraper.wait.until(expected_conditions.visibility_of_element_located((By.CSS_SELECTOR, lesson_list_tag)))
    lesson_url_dict = {x.text: x.get_property("href") for x in scraper.driver.find_elements(By.CSS_SELECTOR, lesson_list_tag)}
    course_level = course.split("/")[-1]
    Path.mkdir(save_base_path/f"{course_level}", parents=True, exist_ok=True)
    for index, (lesson_name, lesson_url) in enumerate(lesson_url_dict.items()):
        time.sleep(randint(2, 8))
        scraper.driver.get(lesson_url)
        lesson_name = lesson_name.replace("\n","_").replace(" ","-")
        scraper.wait.until(expected_conditions.visibility_of_element_located((By.CSS_SELECTOR, download_button_tag)))
        download = scraper.driver.find_element(By.CSS_SELECTOR, download_button_tag)
        pdf_file_name = save_base_path/f"{course_level}/{lesson_name}.pdf"
        scraper.get_image(download.get_property("href"), pdf_file_name)
        print(f"{index + 1}. {pdf_file_name} saved Successfully!")

scraper.driver.delete_all_cookies()
scraper.driver.close()
