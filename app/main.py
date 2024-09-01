import os
import platform


def check_system():
    system = platform.system().lower()
    supported_systems = ["linux", "windows", "darwin"]
    if system not in supported_systems:
        print("System not supported")
        exit(1)
    return system


def get_drive():
    system = check_system()
    if (system == "linux"):
        print("Open drive for linux...")
        # TODO: Open drive for linux
    elif (system == "windows"):
        print("Open drive for windows...")
        # TODO: Open drive for windows
    elif (system == "darwin"):
        print("Open drive for mac...")
        # TODO: Open drive for mac
    # TODO return drive
    return None


def get_gspread():
    # TODO: Open gspread
    pass


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
    data = read_data_from_sheet(gspread)
    payload = extract_data(data)
    # TODO: Use selenium to use that data
    for payload_data in payload:
        # TODO: Do something with payload then write to sheet
        # Do something with payload
        do_payload()
        # Write to sheet
        write_data_to_sheet(gspread, payload_data, 1)


def do_payload():
    pass


def main():
    driver = get_drive()
    gspread = get_gspread()
    the_url = "https://"
    driver.get(the_url)
    while (True):
        clear_screen()
        process(driver, gspread)
