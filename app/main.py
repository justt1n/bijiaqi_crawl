import os
import platform
import wget
import zipfile
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

import time

gsp = None
driver = None
data = None

def check_system():
    system = platform.system().lower()
    supported_systems = ["linux", "windows", "darwin"]
    if system not in supported_systems:
        print("System not supported")
        exit(1)
    return system


def downloadDrive(os_type='windows'):
    # Define URLs and paths for different OS types
    links = {
        'windows': {
            "url": "https://storage.googleapis.com/chrome-for-testing-public/128.0.6613.119/win64/chromedriver-win64.zip",
            "path": os.path.join('storage', 'chromedriver-win64.zip'),
            "driver": os.path.join('storage', 'chromedriver-win64', 'chromedriver.exe')
        },
        'linux': {
            "url": "https://storage.googleapis.com/chrome-for-testing-public/128.0.6613.119/linux64/chromedriver-linux64.zip",
            "path": os.path.join('storage', 'chromedriver-linux64.zip'),
            "driver": os.path.join('storage', 'chromedriver-linux64', 'chromedriver')
        },
        'darwin': {
            "url": "https://storage.googleapis.com/chrome-for-testing-public/128.0.6613.119/mac-x64/chromedriver-mac-x64.zip",
            "path": os.path.join('storage', 'chromedriver-mac-x64.zip'),
            "driver": os.path.join('storage', 'chromedriver-mac-x64', 'chromedriver')
        }
    }

    if os_type not in links:
        raise ValueError(f"Unsupported OS type: {os_type}")

    url = links[os_type]['url']
    zip_path = links[os_type]['path']
    driver_path = links[os_type]['driver']

    print('Start downloading driver...')

    # Ensure the storage directory exists
    os.makedirs(os.path.dirname(zip_path), exist_ok=True)

    # Download the file
    wget.download(url, zip_path)

    # Extract the downloaded zip file
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(os.path.join('storage'))

    os.remove(zip_path)

    print('Driver downloaded and unzipped')
    return driver_path


def get_drive():
    system = check_system()
    if (system == "linux"):
        print("Open drive for linux...")
    elif (system == "windows"):
        print("Open drive for windows...")
    elif (system == "darwin"):
        print("Open drive for mac...")
    else:
        return None
    path = downloadDrive(system)
    return path


def get_gspread(keypath="key.json"):
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(keypath, scope)
    client = gspread.authorize(creds)
    return client


def clear_screen():
    system = check_system()
    if system == "linux" or system == "darwin":
        os.system('clear')
    elif system == "windows":
        os.system('cls')


def read_data_from_sheet(gspread):
    # TODO: Read data from sheet
    pass


def extract_data(data):
    # TODO: Extract data from sheet to array of payload
    pass


def write_data_to_sheet(gspread, data, line_number):
    # TODO: Write data to sheet
    pass


def process(driver, gspread):
    # TODO: Read data from sheet and turn into payload
    # data = read_data_from_sheet(gspread)
    # payload = extract_data(data)
    # TODO: Use selenium to use that data
    # for payload_data in payload:
        # TODO: Do something with payload then write to sheet
        # Do something with payload
        # do_payload()
        # Write to sheet
        # write_data_to_sheet(gspread, payload_data, 1)
    pass

def do_payload(host_id):
    time.sleep(3)
    input_field = driver.find_element(By.ID, 'speedhostname')
    input_field.send_keys('Aegwynn US - Horde ')
    input_field.send_keys(Keys.BACKSPACE)
    input_field.send_keys(Keys.ENTER)


if __name__ == "__main__":
    load_dotenv('settings.env')
    driver_path = get_drive()
    gsp = get_gspread(os.getenv('KEY_PATH'))

    chrome_options = Options()
    chrome_options.add_experimental_option("detach", True)

    chrome_service = Service(executable_path=driver_path)

    try:
        driver = webdriver.Chrome(service=chrome_service, options=chrome_options)
    except Exception as e:
        driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=chrome_options)

    driver.get(os.getenv('DEFAULT_URL'))
    while (True):
        clear_screen()
        process(driver, gspread)



