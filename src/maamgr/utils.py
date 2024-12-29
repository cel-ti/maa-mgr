import subprocess
import typing
from zuu.app.scoop import is_installed, list as scoop_list, get_app_path, get_path
import logging
import os
import time
import threading
from zuu.pkg.time import remaining_time
import sys

class TeeStdout:
    """
    A wrapper for stdout that both prints to console and logs to a file.
    
    Usage:
        sys.stdout = TeeStdout('output.log')
        print("This will be both printed and logged")
    """
    def __init__(self, log_file_path: str):
        self.terminal = sys.stdout
        self.log_file = open(log_file_path, 'a', encoding='utf-8')

    def write(self, message):
        self.terminal.write(message)
        self.log_file.write(message)
        self.log_file.flush()  # Ensure immediate writing to file

    def flush(self):
        self.terminal.flush()
        self.log_file.flush()

def redirect_stdout(log_file_path: str):
    """
    Redirects stdout to both console and a log file.
    
    Args:
        log_file_path (str): Path to the log file where output will be saved
    """
    sys.stdout = TeeStdout(log_file_path)

def is_bucket_installed(bucket_name: str) -> bool:
    """
    Checks if a specific Scoop bucket is installed on the system.

    Args:
        bucket_name (str): The name of the Scoop bucket to check.

    Returns:
        bool: True if the bucket is installed, False otherwise.
    """
    try:
        result = subprocess.run(
            ["scoop", "bucket", "list"],
            capture_output=True,
            text=True,
            check=True,
            shell=True,
        )
        return bucket_name in result.stdout
    except subprocess.CalledProcessError:
        return False


def check_scoop(echo : typing.Callable = print):
    if not is_installed():
        echo("Scoop is not installed. Please install Scoop first.")
        return
    
    logging.info("Scoop is installed.")

    if not is_bucket_installed("maa"):
        echo("maa bucket is not installed. Please wait for it to be installed.")
        subprocess.run(["scoop", "bucket", "add", "maa", "https://github.com/cel-ti/maa-bucket"])
    else:
        logging.info("maa bucket is installed.")

def check_maa_update(echo : typing.Callable = print):
    # get all maa pkgs
    pkgs = [k for k in scoop_list() if k["bucket"] == "maa"]
    for pkg in pkgs:
        try:
            app_path = get_app_path(pkg["name"])
        except Exception:
            echo(f"App {pkg['name']} not found. Skipping...")
            continue
        echo(f"Updating {pkg['name']}...")

        # check if app_path exists
        if not os.path.exists(app_path):
            echo(f"App {pkg['name']} not found. Skipping...")
            continue

        # check mdate < 12 hours
        if time.time() - os.path.getmtime(app_path) < 12 * 60 * 60:
            echo(f"App {pkg['name']} is less than 12 hours old. Skipping...")
            continue

        subprocess.run(["scoop", "update", f"maa/{pkg['name']}"])

    # update scoop path mdate
    os.utime(get_path(), None)

def run_with_lifetime(cmd : typing.List[str], lifetime : str|int, capture_output : bool = False):
    process = None
    stdout = None
    stderr = None
    def run_picli():
        nonlocal process, stdout, stderr
        process = subprocess.Popen(cmd,
            stdout=subprocess.PIPE if capture_output else subprocess.DEVNULL,
            stderr=subprocess.PIPE if capture_output else subprocess.DEVNULL)
        stdout, stderr = process.communicate()
        if capture_output:
            try:
                stdout = stdout.decode('utf-8')
                stderr = stderr.decode('utf-8')
            except UnicodeDecodeError:
                logging.error("Captured output is not in UTF-8 encoding.")

    thread = threading.Thread(target=run_picli)
    thread.start()

    r = remaining_time(lifetime)
    logging.info(f"remaining time: {r}")
    thread.join(timeout=r)
    
    if thread.is_alive():
        logging.info("Process exceeded lifetime, terminating...")
        if process:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
        
        thread.join(timeout=1)

    if capture_output:
        return stdout, stderr
