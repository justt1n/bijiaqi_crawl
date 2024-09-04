import wget
import os
import zipfile
import platform

def check_system():
    system = platform.system().lower()
    supported_systems = ["linux", "windows", "darwin"]
    if system not in supported_systems:
        print("System not supported")
        exit(1)
    return system

def downloadDrive(os_type='windows'):
    windowsUrl = "https://chromedriver.storage.googleapis.com/114.0.5735.90/chromedriver_win32.zip"
    
    link = {
        'windows': {
            "url": "https://chromedriver.storage.googleapis.com/114.0.5735.90/chromedriver_win32.zip",
            "path": "../storage/windows.zip"
        },
        'linux': {
            "url": "https://chromedriver.storage.googleapis.com/114.0.5735.90/chromedriver_linux64.zip",
            "path": "../storage/linux.zip"
        },
        'darwin': {
            "url": "https://chromedriver.storage.googleapis.com/114.0.5735.90/chromedriver_mac64.zip",
            "path": "../storage/mac.zip"
        }
    }
    
    url = link[os_type]['url']
    zip_path = link[os_type]['path']
    
    # Ensure the storage directory exists
    os.makedirs(os.path.dirname(zip_path), exist_ok=True)
    
    wget.download(url, zip_path)
    
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall('../storage/')
    
    os.remove(zip_path)
    
    print('Model downloaded and unzipped')
    return 'Model downloaded and unzipped'

if __name__ == "__main__":
    os_type = check_system()
    downloadDrive(os_type)