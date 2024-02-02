# -*- coding: utf-8 -*-
"""
Mic Roster Web Scraper
======================

A module for logging into the Mic Roster website and fetching shift information.

This module is designed to scrape the Mic Roster website to log in and extract shift information,
utilizing the requests and BeautifulSoup libraries. Functions include creating a BeautifulSoup object
from an HTTP response, extracting VIEWSTATE and EVENTVALIDATION values, logging into the website,
processing calendar data, and a main function to coordinate these actions.

Functions
---------
make_soup(response)
    Creates a BeautifulSoup object from an HTTP response.
get_view_event(soup)
    Extracts VIEWSTATE and EVENTVALIDATION values from a BeautifulSoup object.
login(url)
    Logs into the Mic Roster website using provided credentials.
process_response_cal(response)
    Processes and prints calendar data (shifts) from an HTTP response.
main()
    Coordinates the overall process of logging in and scraping shift information.

Author: matthewpicone
Date: 1/12/2023
"""

import requests
from bs4 import BeautifulSoup
import credentials as cr

login_url = 'https://ess.tmc.tambla.net/Microster.SelfService/Default.aspx'
roster_url = 'https://ess.tmc.tambla.net/Microster.SelfService/MyRoster2.aspx'

session = requests.Session()


def make_soup(response):
    """
    Create a BeautifulSoup object from an HTTP response.

    Given an HTTP response from the requests library, this function creates and
    returns a BeautifulSoup object, which is used for parsing HTML content.

    Parameters
    ----------
    response : Response
        The HTTP response object from the requests' library.

    Returns
    -------
    BeautifulSoup
        A BeautifulSoup object for parsing HTML content.
    """
    return BeautifulSoup(response.text, 'html.parser')


def get_view_event(soup):
    """
    Extract VIEWSTATE and EVENTVALIDATION values from a BeautifulSoup object.

    This function parses a BeautifulSoup object to find and return the values
    of the `__VIEWSTATE` and `__EVENTVALIDATION` form fields, which are often
    required for POST requests in ASP.NET websites.

    Parameters
    ----------
    soup : BeautifulSoup
        The BeautifulSoup object representing a web page.

    Returns
    -------
    tuple of str
        A tuple containing the VIEWSTATE and EVENTVALIDATION values.
    """
    v = soup.find('input', {'name': '__VIEWSTATE'}).get('value')
    e = soup.find('input', {'name': '__EVENTVALIDATION'}).get('value')
    return v, e


def login(url):
    """
    Log into the Mic Roster website using the provided URL and credentials.

    This function performs a login action on the Mic Roster website. It first gets
    the login page, extracts necessary form fields, and then submits a POST request
    with the user credentials.

    Parameters
    ----------
    url : str
        The URL of the login page.

    Returns
    -------
    None
    """
    response = session.get(url)
    soup = make_soup(response)
    viewstate, eventvalidation = get_view_event(soup)
    form_data = {
        'ctl00$ContentPlaceHolder1$txtPersonnelId': cr.credentials.username,
        'ctl00$ContentPlaceHolder1$txtPassword': cr.credentials.password,
        '__VIEWSTATE': viewstate,
        '__EVENTVALIDATION': eventvalidation,
        'ctl00$ContentPlaceHolder1$btnLogin.x': '0',
        'ctl00$ContentPlaceHolder1$btnLogin.y': '0',
    }
    session.post(url, data=form_data)


def process_response_cal(response):
    """
    Extract and process calendar data (shifts) from an HTTP response.

    This function processes the response from the shift information page,
    extracting and printing the calendar data including the shifts.

    Parameters
    ----------
    response : Response
        The HTTP response object containing calendar data.

    Returns
    -------
    None
    """
    soup = make_soup(response)
    month_heading = soup.find('span', id='ctl00_ContentPlaceHolder1_calendar_lblCurrentMonth')
    if month_heading:
        month = month_heading.get_text(strip=True)
        print(f"Month Heading: {month}")
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
                print(f"{d} {month}:  Shift: {cell_text}")
                date += 1


def main():
    """
    Main function for web scraping to fetch shift information.

    This function orchestrates the process of logging into the Mic Roster
    website and scraping shift information. It maintains a session and
    repeatedly fetches and processes shift data until the user decides to exit.

    Parameters
    ----------

    Returns
    -------
    None
    """
    login(login_url)

    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "en-AU,en;q=0.9",
        "Connection": "keep-alive",
        "Host": "ess.tmc.tambla.net",
        "Referer": "https://ess.tmc.tambla.net/Microster.SelfService/MyRoster2.aspx",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "same-origin",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) "
                      "Version/17.1 Safari/605.1.15"
    }

    response = session.get(roster_url, headers=headers)
    if response.status_code == 200:
        print("Request was successful.")
        process_response_cal(response)
    else:
        print(f"Failed to retrieve data with status code: {response.status_code}")


if __name__ == '__main__':
    main()
