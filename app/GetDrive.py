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
    # Define URLs and paths for different OS types
    links = {
        'windows': {
            "url": "https://storage.googleapis.com/chrome-for-testing-public/130.0.6723.91/win32/chromedriver-win32.zip",
            "path": os.path.join('..', 'storage', 'windows.zip')
        },
        'linux': {
            "url": "https://storage.googleapis.com/chrome-for-testing-public/130.0.6723.91/linux64/chromedriver-linux64.zip",
            "path": os.path.join('..', 'storage', 'linux.zip')
        },
        'darwin': {
            "url": "https://storage.googleapis.com/chrome-for-testing-public/130.0.6723.91/mac-x64/chromedriver-mac-x64.zip",
            "path": os.path.join('..', 'storage', 'mac.zip')
        }
    }

    if os_type not in links:
        raise ValueError(f"Unsupported OS type: {os_type}")

    url = links[os_type]['url']
    zip_path = links[os_type]['path']

    print('Start downloading driver...')

    # Ensure the storage directory exists
    os.makedirs(os.path.dirname(zip_path), exist_ok=True)

    # Download the file
    wget.download(url, zip_path)

    # Extract the downloaded zip file
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(os.path.join('..', 'storage'))

    # Remove the zip file after extraction
    os.remove(zip_path)

    print('Driver downloaded and unzipped')
    return os.path.join('..', 'storage', 'chromedriver')


if __name__ == "__main__":
    os_type = check_system()
    downloadDrive(os_type)
