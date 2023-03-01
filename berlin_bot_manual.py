import time
import os
import logging
from platform import system

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

system = system()

default_timeout = 30
default_time_sleep = 10

logging.basicConfig(
    format='%(asctime)s\t%(levelname)s\t%(message)s',
    level=logging.INFO,
)

class WebDriver:
    def __init__(self):
        self._driver: webdriver.Chrome
        self._implicit_wait_time = 20

    def __enter__(self) -> webdriver.Chrome:
        logging.info("Open browser")
        # some stuff that prevents us from being locked out
        options = webdriver.ChromeOptions() 
        options.add_argument('--disable-blink-features=AutomationControlled')
        self._driver = webdriver.Chrome(options=options)
        self._driver.implicitly_wait(self._implicit_wait_time) # seconds
        self._driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        self._driver.execute_cdp_cmd('Network.setUserAgentOverride', {"userAgent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.53 Safari/537.36'})
        return self._driver

    def __exit__(self, exc_type, exc_value, exc_tb):
        logging.info("Close browser")
        self._driver.quit()

class BerlinBot:
    def __init__(self, driver: webdriver.Chrome):
        self.driver = driver
        self.wait_time = 20
        self._sound_file = os.path.join(os.getcwd(), "alarm.wav")
        self._error_message = """Für die gewählte Dienstleistung sind aktuell keine Termine frei! Bitte"""

    def clickPATH(self, element: str):
        try:
            WebDriverWait(self.driver, 20).until(EC.element_to_be_clickable((By.XPATH, element)))
            self.driver.find_element(By.XPATH, element).click()
        except TimeoutException:
            print(f"Element not found: {element}")
            time.sleep(default_time_sleep)
            self.driver.find_element(By.XPATH, element).click()

    
    def clickID(self, id: str):
        try:
            WebDriverWait(self.driver, default_timeout).until(EC.element_to_be_clickable((By.ID, id)))
            self.driver.find_element(By.ID, id).click()
        except TimeoutException:
            print(f"Element not found: {id}")
            time.sleep(default_time_sleep)
            self.driver.find_element(By.ID, id).click()

    def select(self, id: str, text: str):
        try:
            # WebDriverWait(self.driver, 20).until(EC.element_to_be_clickable((By.ID, id)))
            WebDriverWait(self.driver, default_timeout).until(EC.visibility_of_element_located((By.ID, id)))
            s = Select(self.driver.find_element(By.ID, id))
            s.select_by_visible_text(text)
        except TimeoutException:
            print(f"Element not found: {id}")
            time.sleep(default_time_sleep)
            s = Select(self.driver.find_element(By.ID, id))
            s.select_by_visible_text(text)

    def enter_start_page(self):
        logging.info("Visit start page")
        self.driver.get("https://otv.verwalt-berlin.de/ams/TerminBuchen")

        self.clickPATH('//*[@id="mainForm"]/div/div/div/div/div/div/div/div/div/div[1]/div[1]/div[2]/a')

    def tick_off_some_bullshit(self):
        logging.info("Ticking off agreement")

        self.clickPATH('//*[@id="xi-div-1"]/div[4]/label[2]/p')
        self.clickID('applicationForm:managedForm:proceed')

    def enter_form(self):
        logging.info("Fill out form")

        # select china
        self.select('xi-sel-400', 'China')

        # eine person
        self.select('xi-sel-422', 'eine Person')

        # no family
        self.select('xi-sel-427', 'nein')

        # extend stay
        self.clickPATH('//*[@id="xi-div-30"]/div[2]/label/p')

        # click on study group
        self.clickPATH('//*[@id="inner-479-0-2"]/div/div[3]/label/p')

        # b/c of stufy
        self.clickPATH('//*[@id="inner-479-0-2"]/div/div[4]/div/div[3]/label')

        # submit form
        self.submit()

    def submit(self):
        self.clickID('applicationForm:managedForm:proceed')

    def wait(self):
        try:
            WebDriverWait(self.driver, default_timeout).until(EC.element_to_be_clickable((By.ID, 'applicationForm:managedForm:proceed')))
            return True
        except TimeoutException:
            return False
    def _success(self):
        logging.info("!!!SUCCESS - do not close the window!!!!")
        while True:
            self._play_sound_osx(self._sound_file)
            time.sleep(5)
        
        # todo play something and block the browser

    @staticmethod
    def run_once():
        with WebDriver() as driver:
            bot = BerlinBot(driver)
            bot.enter_start_page()
            # bot.tick_off_some_bullshit()
            
            # filling the form manually
            input("Press Enter to Continue, or Ctrl + C to Interrupt")
            bot.submit()

            # retry submit
            while True:
                if "Auswahl Termin" in driver.page_source:
                    bot._success()
                # if not bot._error_message in driver.page_source:
                #     bot._success()
                logging.info("Retry submitting form")
                bot.submit()
                bot.wait()

    # stolen from https://github.com/JaDogg/pydoro/blob/develop/pydoro/pydoro_core/sound.py
    @staticmethod
    def _play_sound_osx(sound, block=True):
        """
        Utilizes AppKit.NSSound. Tested and known to work with MP3 and WAVE on
        OS X 10.11 with Python 2.7. Probably works with anything QuickTime supports.
        Probably works on OS X 10.5 and newer. Probably works with all versions of
        Python.
        Inspired by (but not copied from) Aaron's Stack Overflow answer here:
        http://stackoverflow.com/a/34568298/901641
        I never would have tried using AppKit.NSSound without seeing his code.
        """
        from AppKit import NSSound
        from Foundation import NSURL
        from time import sleep

        logging.info("Play sound")
        if "://" not in sound:
            if not sound.startswith("/"):
                from os import getcwd

                sound = getcwd() + "/" + sound
            sound = "file://" + sound
        url = NSURL.URLWithString_(sound)
        nssound = NSSound.alloc().initWithContentsOfURL_byReference_(url, True)
        if not nssound:
            raise IOError("Unable to load sound named: " + sound)
        nssound.play()

        if block:
            sleep(nssound.duration())

if __name__ == "__main__":
    BerlinBot.run_once()
