import codecs
import json
import logging
import os
import platform
import time
import zipfile
from datetime import datetime

import gspread
import wget
from dotenv import load_dotenv
from oauth2client.service_account import ServiceAccountCredentials
from selenium import webdriver
from selenium.common.exceptions import StaleElementReferenceException
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

import Payload

load_dotenv('settings.env')
gsp = None
driver = None
HOST_DATA = None
BLACKLIST = None


def setup_logging():
    # Load environment variables at the beginning of the script
    load_dotenv('settings.env')

    # Configure logging from environment variables
    log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
    log_format = os.getenv('LOG_FORMAT', '%(asctime)s - %(message)s')

    # Create log file based on the current date in the logs/ directory
    log_dir = 'logs'
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, f"{datetime.now().strftime('%Y-%m-%d')}_function_calls.log")

    logging.basicConfig(filename=log_file, level=log_level, format=log_format)


setup_logging()


def print_function_name(func):
    def wrapper(*args, **kwargs):
        try:
            log_message = f"Calling function: {func.__name__} with args: {args} and kwargs: {kwargs}"
            logging.info(log_message)
            return func(*args, **kwargs)
        except Exception as e:
            logging.error(f"Error in function {func.__name__}: {e}")
            raise

    return wrapper


## Retry functions

def get_cell_text(cell, retries=3):
    for _ in range(retries):
        try:
            return cell.text
        except StaleElementReferenceException:
            time.sleep(0.25)
    raise StaleElementReferenceException("Failed to get cell text after retries")


def get_row_elements(row, retries=3):
    while retries > 0:
        try:
            return row.find_elements(By.TAG_NAME, 'td')
        except StaleElementReferenceException:
            retries -= 1
            if retries == 0:
                raise
            time.sleep(0.25)


def find_link_element(cell, retries=3):
    for _ in range(retries):
        try:
            return cell.find_elements(By.TAG_NAME, 'a')[1]
        except StaleElementReferenceException:
            time.sleep(0.25)
    raise StaleElementReferenceException("Failed to find link element after retries")


def get_link_attribute(link_element, attribute='href', retries=3):
    for _ in range(retries):
        try:
            return link_element.get_attribute(attribute)
        except StaleElementReferenceException:
            time.sleep(0.25)
    raise StaleElementReferenceException(f"Failed to get attribute '{attribute}' after retries")


def get_row_elements_with_retries(row, retries=3):
    for _ in range(retries):
        try:
            return row.find_elements(By.TAG_NAME, 'td')
        except StaleElementReferenceException:
            time.sleep(0.25)
    raise StaleElementReferenceException("Failed to find row elements after retries")


def find_elements_with_retries(parent_element, by, value, retries=3):
    for _ in range(retries):
        try:
            return parent_element.find_elements(by, value)
        except StaleElementReferenceException:
            time.sleep(0.25)
    raise StaleElementReferenceException(f"Failed to find elements by {by}='{value}' after retries")


@print_function_name
def open_driver_with_retries(retries=3):
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_service = Service(executable_path=driver_path)

    for _ in range(retries):
        try:
            driver = webdriver.Chrome(service=chrome_service, options=chrome_options)
            driver.minimize_window()
            driver.get(os.getenv('DEFAULT_URL'))
            return driver
        except WebDriverException:
            time.sleep(0.25)
    raise WebDriverException("Failed to open driver and navigate to URL after retries")


def do_payload_with_retries(payload, retries=3):
    for _ in range(retries):
        try:
            return do_payload(payload)
        except (StaleElementReferenceException, WebDriverException) as e:
            logging.error(f"Error in do_payload: {e}")
            time.sleep(1)
    raise Exception("Failed to execute do_payload after retries")


## End of retry functions


@print_function_name
def check_system():
    system = platform.system().lower()
    supported_systems = ["linux", "windows", "darwin"]
    if system not in supported_systems:
        print("System not supported")
        exit(1)
    return system


@print_function_name
def read_file_with_encoding(file_path, encoding='utf-8'):
    try:
        with codecs.open(file_path, 'r', encoding=encoding) as file:
            content = json.load(file)
        return content
    except UnicodeDecodeError as e:
        print(f"Error decoding file: {e}")
        return None


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


@print_function_name
def downloadDrive(os_type='windows'):
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


@print_function_name
def get_drive():
    system = check_system()
    if system not in links:
        raise ValueError(f"Unsupported OS type: {system}")

    print(f"Downloading driver for {system}...")
    _driver_path = ChromeDriverManager().install()

    return _driver_path


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


def read_data_from_sheet(sheet_name):
    def append_index_to_sheet_data(sheet_data):
        for index, row in enumerate(sheet_data):
            row.append(index + 1 + 1)
        return sheet_data

    spread_sheet = gsp.open_by_url(os.getenv('SPREAD_SHEET_URL')).worksheet(sheet_name)
    data = spread_sheet.get_all_values()
    data = data[1:]
    data = append_index_to_sheet_data(data)
    return data


def get_blacklist_from_sheet(retries=3):
    for _ in range(retries):
        try:
            spread_sheet = gsp.open_by_url(os.getenv('SPREAD_SHEET_URL')).worksheet(os.getenv('BLACKLIST_SHEET_NAME'))
            data = spread_sheet.get_all_values()
            data = data[1:]
            flat_data = [item.lower() for sublist in data for item in sublist]
            return flat_data
        except Exception as e:
            print(f"An error occurred: {e}. Retrying...")
            time.sleep(1)
    raise Exception("Failed to get blacklist from sheet after retries")


def extract_data(data):
    data = data
    payloads = []
    for data_row in data:
        data_row[2] = get_hostname_by_hostid(HOST_DATA, data_row[2])
        payloads.append(Payload.Payload(data_row))
    return payloads


def write_data_to_sheet(data, line_number, sheet_name):
    try:
        # Ensure line_number is an integer
        line_number = int(line_number)
        range_name = os.getenv('DESTINATION_RANGE').format(n=line_number)
        inforange = os.getenv('INFORMATION_RANGE').format(n=line_number)
        spread_sheet_url = os.getenv('SPREAD_SHEET_URL')
        worksheet = gsp.open_by_url(spread_sheet_url).worksheet(sheet_name)
        # Add datetime to the data
        updated_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if data is None:
            note = "Not Found"
            infor = [note, updated_time]
            worksheet.update(range_name=inforange, values=[infor])
            return None
        # Convert data to a list of lists
        note = "Found"
        data_list = [[note, updated_time] + data.toArray()]

        # Update the data in the sheet
        worksheet.update(range_name=range_name, values=data_list)
    except ValueError as e:
        print(line_number)
        print(type(line_number))
        print(f"Error: {e}. Ensure that line_number is a valid integer.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


@print_function_name
def process(sheet_name):
    sheet_data = read_data_from_sheet(sheet_name)
    payloads = extract_data(sheet_data)
    for payload_data in payloads:
        ans = do_payload_with_retries(payload_data, retries=int(os.getenv('RETRIES_TIME')))
        if ans is not None:
            print(f"Found a match for {payload_data.name}")
            write_data_to_sheet(ans, payload_data.sheet_row, sheet_name)
            print(f"Match written to sheet at row {payload_data.sheet_row}")
        else:
            write_data_to_sheet(ans, payload_data.sheet_row, sheet_name)


@print_function_name
def multi_process():
    sheets = os.getenv('SHEET_NAMES').split(',')
    for sheet in sheets:
        try:
            process(sheet)
        except Exception as e:
            logging.error(f"Error in process: {e}")
            driver.refresh()


@print_function_name
def do_payload(payload: Payload.Payload):
    retries_time = int(os.getenv('RETRIES_TIME'))
    if payload.check is None or int(payload.check) != 1:
        return
    host_id = payload.id
    wait = WebDriverWait(driver, float(os.getenv('TIMEOUT')))

    host_id = str(host_id) + " "
    input_field = wait.until(EC.element_to_be_clickable((By.ID, 'speedhostname')))
    input_field.send_keys(host_id)
    input_field.send_keys(Keys.BACKSPACE)
    input_field.send_keys(Keys.ENTER)
    time.sleep(1)

    retries = retries_time
    while retries > 0:
        try:
            table = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'td table.tb.bijia.limit')))
            more_row = driver.find_element(By.XPATH, "//tr[@class='more']")
            driver.execute_script("arguments[0].click();", more_row)
            break
        except StaleElementReferenceException:
            retries -= 1
            if retries == 0:
                raise
            time.sleep(0.25)

    data_array = []

    for row in find_elements_with_retries(table, By.TAG_NAME, 'tr', retries=retries_time):
        row_data = []
        for cell in get_row_elements_with_retries(row, retries=retries_time):
            cell_text = get_cell_text(cell, retries=retries_time)
            if cell_text == " ":
                continue
            elif cell_text == "卖给他":
                link_element = find_link_element(cell, retries=retries_time)
                row_data.append(get_link_attribute(link_element, attribute='href', retries=retries_time))
            else:
                row_data.append(cell_text)
        data_array.append(row_data)

    data_array = data_array[3:-2]
    results = []
    for row in data_array:
        result = Payload.Result(row)
        results.append(result)

    ans = None
    for result in results:
        if result.type in payload.types:
            if payload.gd_min >= result.min_gold and payload.gd_max <= result.max_gold:
                if BLACKLIST is not None and result.username.lower() in BLACKLIST:
                    print(f"User {result.username} is in the blacklist")
                    logging.info(f"User {result.username} is in the blacklist")
                    continue
                ans = result
                break
    input_field.clear()
    return ans


def get_hostname_by_hostid(data, hostid):
    for entry in data:
        if entry['hostid'] == str(hostid):
            return entry['hostname']
    return None


if __name__ == "__main__":
    load_dotenv('settings.env')
    driver_path = get_drive()
    gsp = get_gspread(os.getenv('KEY_PATH'))
    HOST_DATA = read_file_with_encoding(os.getenv('DATA_PATH'), encoding='utf-8')

    driver = open_driver_with_retries(retries=int(os.getenv('RETRIES_TIME')))
    while True:
        clear_screen()
        try:
            BLACKLIST = get_blacklist_from_sheet()
        except Exception as e:
            logging.error(f"Error in get_blacklist_from_sheet: {e}")
        multi_process()
        time.sleep(int(os.getenv('REFRESH_TIME')))
