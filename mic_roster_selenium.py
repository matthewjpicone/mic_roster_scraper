# -*- coding: utf-8 -*-
"""
Mic Roster Web Scraper.

A Python module designed for interacting with the Mic Roster website, capable of logging in and fetching shift
information. It employs the requests and BeautifulSoup libraries for web scraping, and Selenium for automating web
browser interaction.

Available functions facilitate logging into the website, navigating through its pages, and extracting shift details
from the user's calendar. Additionally, it demonstrates integration with Google Calendar API to manage shift schedules.

Author: matthewpicone
Date: 1/12/2023
"""
import sys
# MIT License
#
# Copyright (c) 2024 Matthew Picone
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import time

import googleapiclient
import requests
from bs4 import BeautifulSoup
import datetime
import pytz
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
import pickle
import os.path
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

event_dict = {}

def setup_chrome_driver():
    """
    Initializes and returns a headless Chrome WebDriver with optimized settings.

    The function configures the Chrome WebDriver to run in headless mode,
    ensuring it can run without a GUI. This is particularly useful for running
    automated tests or web scraping tasks in environments without a display.
    Additional configurations are applied to maximize compatibility and performance
    in various execution environments, such as containers or virtual machines.

    Options configured:
    - `--headless`: Run Chrome in headless mode (without a graphical user interface).
    - `--no-sandbox`: Disable the Chrome's sandbox security feature. Necessary in certain environments but reduces
    security.
    - `--disable-dev-shm-usage`: Avoid using `/dev/shm` for memory management to prevent issues in environments with
    limited shared memory.
    - `--disable-gpu`: Disables GPU hardware acceleration, which is not needed for headless operation.
    - `start-maximized`: Starts Chrome maximized; useful for certain tests that may require a larger viewport.
    - `disable-infobars`: Prevents Chrome from displaying information bars at the top of the window.
    - `--disable-extensions`: Disables all Chrome extensions to prevent them from affecting automated tests.

    Returns:
        WebDriver: An instance of Chrome WebDriver configured with the specified options.

    Note:
        This function requires the `selenium` package and `webdriver_manager` to be installed in the Python environment.
    """
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('start-maximized')
    chrome_options.add_argument('disable-infobars')
    chrome_options.add_argument('--disable-extensions')
    try:
        driver = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)
    except WebDriverException as e:
        driver  = webdriver.Chrome("/Users/matthewpicone/Developer/mic_roster_scraper/chromedriver", options=chrome_options)
    return driver


def make_soup(response: requests.Response or requests) -> BeautifulSoup:
    """
    Converts an HTTP response or HTML content to a BeautifulSoup object for parsing.

    This function is designed to handle both cases where the input is an HTTP response object,
    typically from requests library, or a direct string of HTML content. It attempts to parse
    the content using BeautifulSoup with 'html.parser' as the parser.

    Parameters:
    - response (requests.Response): An HTTP response object (with a .text attribute) or a string containing HTML
    content.

    Returns:
    - A BeautifulSoup object initialized with the content from the input. This object can then be
      used for parsing and manipulating HTML content.

    Raises:
    - AttributeError: If the input does not have a .text attribute and is not a string. However,
      this exception is caught within the function, and it tries to parse the input directly as a string.
    """
    try:
        return BeautifulSoup(response.text, 'html.parser')
    except AttributeError:
        return BeautifulSoup(response, 'html.parser')


def get_view_event(soup: BeautifulSoup):
    """
    Extracts the values of `__VIEWSTATE` and `__EVENTVALIDATION` from a BeautifulSoup object.

    This function is specifically designed to work with ASP.NET web pages, which often use
    `__VIEWSTATE` and `__EVENTVALIDATION` as part of their form management and state preservation
    mechanisms. These hidden form fields are used to maintain state between server and client.
    The function searches the parsed HTML for these fields and extracts their values.

    Parameters:
    - soup (BeautifulSoup): A BeautifulSoup object containing the parsed HTML of an ASP.NET page.

    Returns:
    - A tuple containing two elements:
      - The value of the `__VIEWSTATE` input field.
      - The value of the `__EVENTVALIDATION` input field.
    """
    v = soup.find('input', {'name': '__VIEWSTATE'}).get('value')
    e = soup.find('input', {'name': '__EVENTVALIDATION'}).get('value')
    return v, e


def login(driver, url: str, username: str, password: str) -> str:
    """
    Automates login to a specified URL using Selenium WebDriver.

    This function navigates to a given URL, waits for specific login form elements to load, fills in the login
    credentials (username and password), and submits the form. It then waits for a specific element to appear
    on the page following a successful login, indicating that the login process has completed. The function
    assumes that the WebDriver (`driver`) and credentials repository (`cr`) are already defined and accessible
    in the scope where this function is called.

    Parameters:
    - driver: Selenium. An instance of selenium.webdriver
    - url: String. The URL of the login page to navigate to.

    Returns:
    - The page source of the webpage after the login attempt, as a string.
    """
    driver.get(url)
    # Wait for the login elements to load
    WebDriverWait(driver, 10).until(
        ec.presence_of_element_located((By.NAME, 'ctl00$ContentPlaceHolder1$txtPersonnelId'))
    )
    # Fill in login form and submit
    driver.find_element_by_name('ctl00$ContentPlaceHolder1$txtPersonnelId').send_keys(username)
    driver.find_element_by_name('ctl00$ContentPlaceHolder1$txtPassword').send_keys(password)
    driver.find_element_by_name('ctl00$ContentPlaceHolder1$btnLogin').click()
    WebDriverWait(driver, 10).until(
        ec.presence_of_element_located((By.ID, "ctl00_ContentPlaceHolder1_calendar_lnkNextMonth"))
    )
    return driver.page_source


def fetch_next_page_html(driver, button_name: str):
    """
    Navigates to the next page in a web application and returns the HTML content of the page.

    This function locates a button by its ID, simulates a click to navigate to the next page, waits
    briefly for the page to load, and then returns the HTML source of the resulting page. It is designed
    to work within a Selenium WebDriver context, assuming that a `driver` instance is available in the
    scope from which this function is called.

    Parameters:
    - driver: Selenium. An instance of selenium.webdriver
    - button_name (str): The ID of the button that triggers navigation to the next page.

    Returns:
    - A string containing the HTML source of the page after navigation.

    Raises:
    - selenium.common.exceptions.NoSuchElementException: If the button with the specified ID is not found
      on the current page.
    """
    # Navigate to the next page
    next_page_button = driver.find_element_by_id(button_name)
    next_page_button.click()
    time.sleep(1)  # Wait briefly for the page to load
    # Return the HTML of the page
    return driver.page_source


def convert_month_to_num(month_string: str):
    """
    Converts a month name to its corresponding two-digit numerical representation.

    This function accepts a month name (case-insensitive) as input and returns the month's
    two-digit numerical string representation (e.g., "January" returns "01"). If the input
    does not match any month name, it returns 'Invalid'.

    Parameters:
    - month_string (str): The name of the month to convert. The function is case-insensitive.

    Returns:
    - A string representing the two-digit numerical representation of the given month if the
      month name is valid. Returns 'Invalid' if the month name is not recognized.
    """
    month = {'january': '01', 'february': '02', 'march': '03', 'april': '04',
             'may': '05', 'june': '06', 'july': '07', 'august': '08',
             'september': '09', 'october': '10', 'november': '11', 'december': '12'}
    return month.get(month_string.lower(), 'Invalid')


def process_response_cal(response):
    global event_dict
    soup = make_soup(response)
    month_heading = soup.find('span', id='ctl00_ContentPlaceHolder1_calendar_lblCurrentMonth')
    if month_heading:
        month = month_heading.get_text(strip=True)
    else:
        month = None

    cell_data = {}
    date = 1
    for cell in range(1, 40):
        cell_id = f"ctl00_ContentPlaceHolder1_calendar_DateCell{cell}"
        cell_content = soup.find('td', id=cell_id)
        if cell_content:
            div_content = cell_content.find('div')
            cell_text = div_content.get_text(strip=True) if div_content else ""
            cell_text = cell_text.replace(")", ") ") if ")" in cell_text else cell_text
            cell_data[date] = cell_text
            if cell_text:
                if date < 10:
                    d = f"0{date}"
                else:
                    d = date
                if cell_text.split(" ")[0] != "OFF" and cell_text.split(" ")[0] != "PH" and cell_text.split(" ")[
                    0] != "OT" and cell_text.split(" ")[0] != "NA" and cell_text.split(" ")[0] != "SICK" and \
                        cell_text.split(" ")[0] != "Not":
                    date_text = month.split(" ")
                    shift_text = cell_text.split(" ")
                    time_text = cell_text.split(" ")[0].split("-")
                    try:
                        event = {
                            'summary': f'{shift_text[2]}',
                            'location': '25 Garden Street Eveleigh NSW 2015',
                            'description': f'Date shift last updated: {datetime.datetime.now().strftime("%d/%m/%Y %H:%M")}',
                            'start': {
                                'dateTime': f'{date_text[1]}-{convert_month_to_num(date_text[0])}-{d}T'
                                            f'{time_text[0][:2]}:{time_text[0][2:]}:00',
                                'timeZone': 'Australia/Sydney',
                            },
                            'end': {
                                'dateTime': f'{date_text[1]}-{convert_month_to_num(date_text[0])}-{d}T'
                                            f'{time_text[1][:2]}:{time_text[1][2:]}:00',
                                'timeZone': 'Australia/Sydney',
                            },
                            'reminders': {
                                'useDefault': False,
                                'overrides': [
                                    {'method': 'email', 'minutes': 24 * 60},
                                    {'method': 'email', 'minutes': 12 * 60},
                                    {'method': 'popup', 'minutes': 12 * 60},
                                    {'method': 'popup', 'minutes': 60},
                                    {'method': 'popup', 'minutes': 10},
                                ]
                            }
                        }
                        event_dict[
                            (f'{date_text[1]}-{convert_month_to_num(date_text[0])}-{d}T'
                             f'{time_text[0][:2]}:{time_text[0][2:]}:00')] = event
                    except:
                        input(f"Error with {shift_text}, press enter to continue")
                date += 1
    return event_dict


def authenticate_google_calendar(scopes: list) -> dict:
    """
    Authenticates the user with the Google Calendar API and returns a service object.

    This function attempts to load previously saved credentials from a 'token.pickle' file. If the file
    does not exist, the credentials are invalid, or the credentials have expired, the function initiates
    a new authentication flow. Once the user successfully authenticates, the credentials are saved for
    future use in the 'token.pickle' file.

    Parameters:
    - scopes (list): A list of strings representing the OAuth scopes for which permission is being requested.
                     These scopes define the level of access the application needs.

    Returns:
    - A Google Calendar service object that can be used to make API calls. This object provides a
      dictionary-like interface for interacting with the Google Calendar API.

    Raises:
    - FileNotFoundError: If the 'credentials.json' file, containing the OAuth 2.0 Client ID and Client Secret,
      is not found. This file is required to initiate the new authentication flow.
    - google.auth.exceptions.RefreshError: If the refresh token is invalid, expired, and cannot be refreshed.
      This indicates that the user needs to re-authenticate.

    Example:
    ```
    SCOPES = ['https://www.googleapis.com/auth/calendar']
    service = authenticate_google_calendar(SCOPES)
    # Now you can use 'service' to interact with the Google Calendar API
    ```

    Note:
    The 'credentials.json' file must be obtained from the Google Developer Console by creating
    OAuth 2.0 credentials for your application. The 'token.pickle' file is automatically created
    and updated by this function; it should not be modified manually.
    """
    creds = None
    if os.path.exists('/Users/matthewpicone/Developer/mic_roster_scraper/token.pickle'):
        with open('/Users/matthewpicone/Developer/mic_roster_scraper/token.pickle', 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                '/Users/matthewpicone/Developer/mic_roster_scraper/credentials.json', scopes)
            creds = flow.run_local_server(port=0)
        with open('/Users/matthewpicone/Developer/mic_roster_scraper/token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('calendar', 'v3', credentials=creds)
    return service


def create_calendar_event(service: googleapiclient.discovery.Resource, event: dict):
    """
    Creates a new event in the user's Google Calendar.

    Parameters:
    - service (googleapiclient.discovery.Resource): The authenticated Google Calendar service object, obtained
      through the `authenticate_google_calendar(scopes: list)` function.
    - event (dict): A dictionary containing event details as required by the Google Calendar API.

    Example:
    ```
    SCOPES = ['https://www.googleapis.com/auth/calendar']
    service = authenticate_google_calendar(SCOPES)
    event = {
        'summary': 'Event Name',
        'location': '123 Example Street, Exampletown, ExampleState, 2000',
        'description': 'Details of the shift',
        'start': {
            'dateTime': '2024-05-28T09:00:00',
            'timeZone': 'Australia/Sydney',
        },
        'end': {
            'dateTime': '2024-05-28T17:00:00',
            'timeZone': 'Australia/Sydney',
        },
        'reminders': {
            'useDefault': False,
            'overrides': [
                {'method': 'email', 'minutes': 24 * 60},
                {'method': 'email', 'minutes': 12 * 60},
                {'method': 'popup', 'minutes': 12 * 60},
                {'method': 'popup', 'minutes': 60},
                {'method': 'popup', 'minutes': 10},
            ]
        }
    }
    create_calendar_event(service, event)
    ```
    """
    # Call the Calendar API to create an event
    service.events().insert(calendarId='primary', body=event).execute()
    print(f"Event created: {event.get('summary')}")

def list_calendar_events(service: googleapiclient.discovery.Resource, calendar_id='primary', max_results=10,
                         days_past=30):
    """
    Lists events from the user's Google Calendar within a specified time frame.

    Parameters:
    - service (googleapiclient.discovery.Resource): The authenticated Google Calendar service object, obtained
      through the `authenticate_google_calendar(scopes: list)` function.
    - calendar_id (str): ID of the calendar to list events from. Default is 'primary'.
    - max_results (int): Maximum number of events to return. Default is 10.
    - days_past (int): Number of days in the past to retrieve events for, up to now. Default is 30.

    Returns:
    - A list of event objects for the specified time frame.
    """

    # Calculate timeMin for 'days_past' days ago
    utc_now = datetime.datetime.utcnow().replace(tzinfo=pytz.UTC)
    time_min = (utc_now - datetime.timedelta(days=days_past)).isoformat()

    events_result = service.events().list(calendarId=calendar_id, timeMin=time_min,
                                          maxResults=max_results, singleEvents=True,
                                          orderBy='startTime').execute()
    events = events_result.get('items', [])

    return events


def delete_calendar_event(service: googleapiclient.discovery.Resource, calendar_id='primary', event_id=None):
    """
    Deletes an event from the user's Google Calendar.

    Parameters:
    - service (googleapiclient.discovery.Resource): The authenticated Google Calendar service object, obtained
      through the `authenticate_google_calendar(scopes: list)` function.
    - calendar_id (str): ID of the calendar from which to delete the event. Default is 'primary'.
    - event_id (str): The ID of the event to delete.

    Note:
    - Prints a success message upon deletion or an error message if the operation fails.
    """

    try:
        service.events().delete(calendarId=calendar_id, eventId=event_id).execute()
        print(f"Event with ID {event_id} deleted successfully.")
    except Exception as e:
        print(f"An error occurred: {e}")


def search_events_on_specific_day(service: googleapiclient.discovery.Resource, date: str, calendar_id: str = 'primary',
                                  timezone: str = 'UTC') -> list:
    """
    Searches for events in the user's Google Calendar on a specific day, according to the given date and timezone.

    Parameters:
    - service (googleapiclient.discovery.Resource): The authenticated Google Calendar service object, obtained
      through the `authenticate_google_calendar(scopes: list)` function. This object is used to make API calls.
    - date (str): The date to search for events, in 'YYYY-MM-DD' format. This specifies the specific day to look for
    events.
    - calendar_id (str): The ID of the calendar to search in. Defaults to 'primary', which is the user's primary Google
    Calendar.
    - timezone (str): The timezone to consider for the start and end of the specified day. Defaults to 'UTC'. This is
    important for correctly determining the day's boundaries in the specified timezone.

    Returns:
    - A list of dictionaries, each representing an event found on the specified day. The list will be empty if no events
    are found.

    Note:
    - This function uses the specified timezone to accurately determine the beginning and end of the specified day.
      Events are then searched within this time frame.
    """
    date_obj = datetime.datetime.strptime(date, '%Y-%m-%d')

    # Set the timezone for the date object
    tz = pytz.timezone(timezone)
    date_obj = tz.localize(date_obj)

    # Define the start and end of the specified day
    time_min = date_obj.isoformat()
    time_max = (date_obj + datetime.timedelta(days=1)).isoformat()

    # Call the Calendar API
    events_result = service.events().list(calendarId=calendar_id,
                                          timeMin=time_min,
                                          timeMax=time_max,
                                          singleEvents=True,
                                          orderBy='startTime').execute()
    events = events_result.get('items', [])

    return events


def main():
    login_url = 'https://ess.tmc.tambla.net/Microster.SelfService/Default.aspx'
    global event_dict
    driver = setup_chrome_driver()
    service = authenticate_google_calendar(['https://www.googleapis.com/auth/calendar'])
    start_date = datetime.datetime.now().day
    events_tbd = list_calendar_events(service, max_results=1000, days_past=start_date)
    event_length = len(events_tbd)
    for event in events_tbd:
        print(event_length, end=" ")
        event_id = event['id']
        delete_calendar_event(service, event_id=event_id)
        event_length -= 1
    import credentials as cr
    process_response_cal(login(driver, login_url, cr.credentials.username, cr.credentials.password))
    time.sleep(2)

    process_response_cal(fetch_next_page_html(driver, "ctl00_ContentPlaceHolder1_calendar_lnkNextMonth"))
    time.sleep(2)
    process_response_cal(fetch_next_page_html(driver, "ctl00_ContentPlaceHolder1_calendar_lnkNextMonth"))
    time.sleep(2)
    # for i in range(24):
    #     try:
    #         process_response_cal(fetch_next_page_html(driver, "ctl00_ContentPlaceHolder1_calendar_lnkPreviousMonth"))
    #         time.sleep(2)
    #     except:
    #         pass
    driver.quit()

    for _, event in event_dict.items():
        try:
            create_calendar_event(service, event)
        except:
            print(f"Skipped event {event}")


if __name__ == '__main__':
    main()
