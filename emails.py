#Import Settings
from settings import * #See readme to learn how to create this file

#Import Selenium
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains

#Import Modules
import time
from io import BytesIO
from PIL import Image
from datetime import datetime, timedelta
import pytz
import openai

openai.api_key = API_TOKEN

class Automation():

    def __init__(self):
        
        #Chrome driver setup
        options = webdriver.ChromeOptions()
        options.add_argument('--start-maximized')
        options.add_argument(f'user-agent={USER_AGENT}')
        options.add_argument('--no-sandbox')
        options.add_argument('window-size=1920x1080')
        self.driver = webdriver.Chrome(PATH, options = options)
        self.driver.maximize_window()

        #Stores events
        self.events = []
        self.emailqueue = []
    
    def quit(self):
        '''Closes the page and exits driver'''

        self.driver.close()
        self.driver.quit()
    
    def search_for_events(self):
        '''Scrapes the wavesync page for events, returns links to events'''
        
        #Elements
        event_div_class = 'MuiPaper-root.MuiCard-root.MuiPaper-elevation3.MuiPaper-rounded'

        #Opens wavesync page
        self.driver.get(WAVESYNC_PAGE)

        #Scrapes for events
        event_divs = self.driver.find_elements(By.CLASS_NAME, event_div_class)

        #Closes if no events found
        if len(event_divs) == 0:
            self.quit()
        
        #Returns links to events
        return [div.find_element(By.XPATH, '..').get_attribute('href') for div in event_divs]

    def scrape_event(self, link):
        '''Scrapes information from each event and creates items'''
        
        #Elements
        title_xpath = '//h1[@style="padding: 0px; font-size: 30px;"]'
        flier_xpath = '//*[@title="Image Uploaded for Event Cover Photo"]'
        datetime_xpath = '//p[@style="margin: 2px 0px; white-space: normal;"]'
        description_class = 'DescriptionText'

        #Creates an object to store the event and opens the page
        curr_event = Event()
        self.driver.get(link)

        #Scrapes the key attributes of event
        curr_event.title = self.driver.find_element(By.XPATH, title_xpath).get_attribute('innerText')
        curr_event.datetime = self.driver.find_elements(By.XPATH, datetime_xpath)[0].get_attribute('innerText')
        curr_event.description = self.driver.find_element(By.CLASS_NAME, description_class).get_attribute('innerText')
        curr_event.location = self.driver.find_elements(By.XPATH, datetime_xpath)[2].get_attribute('innerText')



        #Saves the flier in a folder called fliers
        flier_div = self.driver.find_element(By.XPATH, flier_xpath)
        f_x = flier_div.location['x']
        f_y = flier_div.location['y']
        f_width = flier_div.size['width']
        f_height = flier_div.size['height']
        screenshot = self.driver.get_screenshot_as_png()
        image = Image.open(BytesIO(screenshot))
        flier = image.crop((f_x, f_y, f_x + f_width, f_y + f_height))
        flier.save(f'fliers/{curr_event.title}_flier.png')
        curr_event.flier = f'fliers/{curr_event.title}_flier.png'

        #Converts datetime to useable format
        curr_event.convert_datetime_format()

        #Adds event to events list
        self.events.append(curr_event)

    def check_dates(self):
        '''Checks if emails are meant to be sent out today'''

        today = datetime.now().date()

        for event in self.events:

            #Important dates
            thirteen_days_before = event.date.date() - timedelta(days=13)
            seven_days_before = event.date.date() - timedelta(days=13)
            
            #Checks if an email should be sent today
            if (today == thirteen_days_before) or (today == seven_days_before) or (today == event.date.date()):
                self.emailqueue.append(event)
        
        if len(self.emailqueue) == 0:
            self.quit()

    def generate_email_text(self, event):
        '''Generates email text for the email'''

        response = openai.Completion.create(
            model="text-davinci-002",
            prompt=f'Given the following event title and description, write a 300-word email inviting club members for Tulane Cookie and Code Club to attend said meeting. Title: {event.title}, Description: {event.description}. Dont write a greeting or a closing remark.',
            temperature=0.5,
            max_tokens=3000
        )

        event.emailtext = response.choices[0].text
    
    def mailchimp_login(self):
        '''Logs in to mailchimp'''

        #Elements

        #Navigates to mailchimp website
        self.driver.get('https://login.mailchimp.com/')

        #Location username and password fields
        username_input = self.driver.find_element(By.NAME, 'username')
        password_input = self.driver.find_element(By.NAME, 'password')

        #Enters username and password
        username_input.send_keys(MAILCHIMP_USERNAME)
        password_input.send_keys(MAILCHIMP_PASSWORD)
        time.sleep(.5)
        password_input.send_keys(Keys.ENTER)

        #Deal with email verification



class Event():

    def __init__(self):

        self.title = None
        self.description = None
        self.location = None
        self.datetime = None
        self.date = None
        self.flier = None
        self.emailtext = None
    
    def convert_datetime_format(self):
        '''Converts datetime string to date and time variables'''

        #Removes 'to' from the datetime string
        self.datetime = self.datetime.replace(' to', '')

        date_format = '%A, %B %d %Y at %I:%M %p %Z'
        date_and_time = datetime.strptime(self.datetime, date_format)
        us_central_tz = pytz.timezone('US/Central')
        self.date = us_central_tz.localize(date_and_time) 


        
        


x = Automation()
x.mailchimp_login()