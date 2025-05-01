#!/Users/sachinkumaryadav/code-sac/tweet-cli/venv/bin/python3 
import os
import sys
import argparse
import pickle
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from dotenv import load_dotenv
import time
import random
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

class TwitterCLI:
    def __init__(self):
        # Load .env from the script's directory
        script_dir = os.path.dirname(os.path.realpath(__file__))
        env_path = os.path.join(script_dir, '.env')
        load_dotenv(env_path)

        self.username = os.getenv("TWITTER_USERNAME")
        self.password = os.getenv("TWITTER_PASSWORD")
        self.passcode = os.getenv("TWITTER_PASSCODE")
        if not self.username or not self.password:
            logger.error("TWITTER_USERNAME and TWITTER_PASSWORD must be set in .env")
            sys.exit(1)
        if not self.passcode or not (self.passcode.isdigit() and len(self.passcode) == 4):
            logger.error("TWITTER_PASSCODE must be a 4-digit number in .env")
            sys.exit(1)

        self.options = Options()
        self.options.add_argument("--headless")
        self.options.add_argument("--disable-gpu")
        self.options.add_argument("--no-sandbox")
        self.options.add_argument("--disable-dev-shm-usage")
        self.options.add_argument(
            "user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
        )
        self.driver = None
        self.cookie_file = os.path.join(script_dir, "twitter_cookies.pkl")  # Cookies in script dir

    def setup_driver(self):
        try:
            self.driver = webdriver.Chrome(options=self.options)
            self.wait = WebDriverWait(self.driver, 10)
            logger.info("WebDriver initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize WebDriver: {e}")
            sys.exit(1)

    def load_cookies(self):
        if os.path.exists(self.cookie_file):
            self.driver.get("https://twitter.com")
            with open(self.cookie_file, "rb") as f:
                cookies = pickle.load(f)
                for cookie in cookies:
                    self.driver.add_cookie(cookie)
            self.driver.refresh()
            time.sleep(random.uniform(2, 4))
            try:
                self.wait.until(EC.presence_of_element_located((By.XPATH, "//div[@role='textbox']")))
                logger.info("Session restored from cookies")
                return True
            except:
                logger.info("Cookies invalid, proceeding with login")
                return False
        return False

    def save_cookies(self):
        with open(self.cookie_file, "wb") as f:
            pickle.dump(self.driver.get_cookies(), f)
        logger.info("Cookies saved")

    def login(self):
        if self.load_cookies():
            return

        self.driver.get("https://twitter.com/login")
        time.sleep(random.uniform(2, 4))

        try:
            username_field = self.wait.until(
                EC.presence_of_element_located((By.XPATH, "//input[@name='text']"))
            )
            username_field.send_keys(self.username)
            time.sleep(random.uniform(1, 2))
            username_field.send_keys(Keys.RETURN)

            password_field = self.wait.until(
                EC.presence_of_element_located((By.XPATH, "//input[@name='password']"))
            )
            password_field.send_keys(self.password)
            time.sleep(random.uniform(1, 2))
            password_field.send_keys(Keys.RETURN)

            time.sleep(random.uniform(3, 5))
            self.save_cookies()
            logger.info("Logged in to Twitter successfully")
        except Exception as e:
            logger.error(f"Login failed: {e}")
            self.cleanup()
            sys.exit(1)

    def post_tweet(self, tweet_text):
        self.driver.get("https://twitter.com/compose/tweet")
        time.sleep(random.uniform(2, 4))

        try:
            tweet_box = self.wait.until(
                EC.presence_of_element_located((By.XPATH, "//div[@role='textbox']"))
            )
            for char in tweet_text:
                tweet_box.send_keys(char)
                time.sleep(random.uniform(0.05, 0.15))
            time.sleep(random.uniform(1, 2))

            post_button = self.wait.until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//button[.//span[text()='Post']] | //div[@data-testid='tweetButtonInline'] | //div[@data-testid='tweetButton']")
                )
            )
            post_button.click()
            time.sleep(random.uniform(2, 3))
            logger.info(f"Tweet posted: '{tweet_text}'")
        except Exception as e:
            logger.error(f"Failed to post tweet: {e}")
            self.cleanup()
            sys.exit(1)

    def cleanup(self):
        if self.driver:
            self.driver.quit()
            logger.info("WebDriver closed")

    def tweet(self, passcode, text):
        if not self.verify_passcode(passcode):
            logger.error("Invalid passcode")
            sys.exit(1)
        self.setup_driver()
        self.login()
        self.post_tweet(text)
        self.cleanup()

    def verify_passcode(self, passcode):
        return passcode == self.passcode

def main():
    parser = argparse.ArgumentParser(description="Tweet from the command line with a passcode")
    parser.add_argument("passcode", help="4-digit passcode")
    parser.add_argument("text", nargs="+", help="Text to tweet")
    args = parser.parse_args()

    tweet_text = " ".join(args.text)
    if len(tweet_text) > 280:
        logger.error("Tweet exceeds 280 characters")
        sys.exit(1)

    twitter = TwitterCLI()
    twitter.tweet(args.passcode, tweet_text)

if __name__ == "__main__":
    main()