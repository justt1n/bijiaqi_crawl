import os
import platform
import wget
import zipfile
import gspread
import json
import codecs
from oauth2client.service_account import ServiceAccountCredentials
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.common.exceptions import StaleElementReferenceException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import Payload
import time

gsp = None
driver = None
HOST_DATA = None

def print_function_name(func):
    def wrapper(*args, **kwargs):
        print(f"Calling function: {func.__name__}")
        return func(*args, **kwargs)
    return wrapper

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

    driver_path = links[system]['driver']

    if os.path.exists(driver_path):
        print(f"Driver already exists at {driver_path}")
        return driver_path

    print(f"Downloading driver for {system}...")
    path = downloadDrive(system)
    return path


def get_gspread(keypath="key.json"):
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(keypath, scope)
    client = gspread.authorize(creds)
    return client


@print_function_name
def clear_screen():
    system = check_system()
    if system == "linux" or system == "darwin":
        os.system('clear')
    elif system == "windows":
        os.system('cls')


@print_function_name
def read_data_from_sheet():
    def append_index_to_sheet_data(sheet_data):
        for index, row in enumerate(sheet_data):
            row.append(index + 1 + 1)
        return sheet_data

    spread_sheet = gsp.open_by_url(os.getenv('SPREAD_SHEET_URL')).get_worksheet(0)
    data = spread_sheet.get_all_values()
    data = data[1:]
    data = append_index_to_sheet_data(data)
    return data


@print_function_name
def extract_data(data):
    data = data
    payloads = []
    for data_row in data:
        data_row[2] = get_hostname_by_hostid(HOST_DATA, data_row[2])
        payloads.append(Payload.Payload(data_row))
    return payloads


@print_function_name
def write_data_to_sheet(data, line_number):
    try:
        # Ensure line_number is an integer
        line_number = int(line_number)
        range_name = os.getenv('DESTINATION_RANGE').format(n=line_number)
        spread_sheet_url = os.getenv('SPREAD_SHEET_URL')
        worksheet = gsp.open_by_url(spread_sheet_url).get_worksheet(0)

        # Convert data to a list of lists
        data_list = [data.toArray()]

        worksheet.update(range_name=range_name, values=data_list)
    except ValueError as e:
        print(line_number)
        print(type(line_number))
        print(f"Error: {e}. Ensure that line_number is a valid integer.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

@print_function_name
def process():
    # TODO: Read data from sheet and turn into payload
    sheet_data = read_data_from_sheet()
    payloads = extract_data(sheet_data)
    # TODO: Use selenium to use that data
    for payload_data in payloads:
        ans = do_payload(payload_data)
        if ans is not None:
            print(f"Found a match for {payload_data.name}")
            write_data_to_sheet(ans, payload_data.sheet_row)
            print(f"Match written to sheet at row {payload_data.sheet_row}")


def get_cell_text(cell, retries=3):
    while retries > 0:
        try:
            return cell.text
        except StaleElementReferenceException:
            retries -= 1
            if retries == 0:
                raise
            time.sleep(0.5)

def get_row_elements(row, retries=3):
    while retries > 0:
        try:
            return row.find_elements(By.TAG_NAME, 'td')
        except StaleElementReferenceException:
            retries -= 1
            if retries == 0:
                raise
            time.sleep(0.5)

@print_function_name
def do_payload(payload: Payload.Payload):
    if int(payload.check) == 0:
        return
    host_id = payload.id
    wait = WebDriverWait(driver, 3)

    host_id = str(host_id) + " "
    input_field = wait.until(EC.element_to_be_clickable((By.ID, 'speedhostname')))
    input_field.send_keys(host_id)
    input_field.send_keys(Keys.BACKSPACE)
    input_field.send_keys(Keys.ENTER)
    time.sleep(1)

    retries = 10
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
            time.sleep(0.5)

    data_array = []

    header = []
    for row in table.find_elements(By.CSS_SELECTOR, 'tr.tb_head'):
        header.append(row.text)

    for row in table.find_elements(By.TAG_NAME, 'tr'):
        row_data = []
        for cell in get_row_elements(row):
            cell_text = get_cell_text(cell)
            if cell_text == " ":
                continue
            elif cell_text == "卖给他":
                link_element = cell.find_elements(By.TAG_NAME, 'a')[1]
                row_data.append(link_element.get_attribute('href'))
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
                ans = result
                break
    input_field.clear()
    return ans


@print_function_name
def get_hostname_by_hostid(data, hostid):
    for entry in data:
        if entry['hostid'] == str(hostid):
            return entry['hostname']
    return None


@print_function_name
def open_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Chạy Chrome ở chế độ headless
    chrome_options.add_argument("--no-sandbox")
    chrome_service = Service(executable_path=driver_path)

    try:
        driver = webdriver.Chrome(service=chrome_service, options=chrome_options)
    except Exception as e:
        driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=chrome_options)

    driver.get(os.getenv('DEFAULT_URL'))
    return driver

if __name__ == "__main__":
    load_dotenv('settings.env')
    driver_path = get_drive()
    gsp = get_gspread(os.getenv('KEY_PATH'))
    HOST_DATA = read_file_with_encoding(os.getenv('DATA_PATH'), encoding='utf-8')

    sheet_data = read_data_from_sheet()
    payloads = extract_data(sheet_data)
    driver = open_driver()

    driver.get(os.getenv('DEFAULT_URL'))
    while (True):
        clear_screen()
        process()
        break

