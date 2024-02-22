# Mic Roster Web Scraper

## Project Overview
The Mic Roster Web Scraper is an advanced Python tool engineered for seamless automation of logging into the Mic Roster platform and retrieving shift schedules. Leveraging the robust `requests` and `BeautifulSoup4` libraries, this module offers an intuitive and efficient method for navigating web pages, parsing HTML, and extracting critical shift information. Ideal for employees and administrators, this scraper simplifies access to roster details, enhancing productivity and time management.

## Key Features
- **Enhanced Automated Login**: Streamlined login process with improved security measures.
- **Comprehensive Shift Information Extraction**: Captures detailed shift schedules, including times, roles, and locations.
- **Advanced Data Parsing**: Employs BeautifulSoup for superior HTML content parsing.
- **User-Friendly Interface**: Simplified functions and a guided setup process for effortless operation.
- **Highly Customizable**: Offers flexibility to adapt to various user needs and website updates.

## Getting Started

### Prerequisites
- Python 3.6 or later
- Git (for cloning the repository)

### Installation

1. Ensure Python and Git are installed on your system.
2. Clone the repository to your local machine:
   ```
   git clone https://github.com/mic_roster_web_scraper.git
   ```
3. Navigate to the project directory and install dependencies:
   ```
   pip install -r requirements.txt
   ```

### Configuration
- Set up a `credentials.py` file in the project root with your Mic Roster login details.

## Usage Guide

1. Import the scraper in your script:
   ```python
   from mic_roster_web_scraper import MicRosterScraper
   ```
2. Initialize the scraper and call the `fetch_shifts` method to retrieve shift data:
   ```python
   scraper = MicRosterScraper()
   shifts = scraper.fetch_shifts()
   ```

## License

This project is licensed under the MIT License - see the LICENSE.md file for details.
