import json
import shutil
import typing
from zuu.app.scoop import get_app_path
import os
import datetime
from functools import cached_property
import threading
import logging
from zuu.pkg.time import remaining_time
import subprocess
from zuu.io.json import Json
from zuu.common.traverse import get_deep, set_deep

from .utils import run_with_lifetime

KEY_MAPS = {
    "R":"resource",
    "C" : "controller",
    "T" : "task"
}

class MaaInstance:
    def __init__(self, name : str, path : str = None):
        self.name = name
        assert self.name is not None, "name is required"
        
        self.__path = path or get_app_path(name)
        assert self.__path is not None, f"app {name} not found"

        # Call the method in the constructor to ensure paths are checked upon initialization
        self.assert_paths_exist()


    def assert_paths_exist(self):
        for attr in dir(self):
            if attr.startswith("path"):
                path = getattr(self, attr)
                if not os.path.exists(path):
                    raise AssertionError(f"Path {path} for {attr} does not exist. The application is not ready.")
    
    @cached_property
    def path(self):
        return self.__path
    
    @cached_property
    def path_config(self):
        return os.path.join(self.path, "config")

    @cached_property
    def path_resource(self):
        return os.path.join(self.path, "resource")
    
    @cached_property
    def _path_usr(self):
        return os.path.join(os.path.expanduser("~"), ".maamgr", self.name)
    
    @cached_property
    def path_config_file(self):
        pass

    def export(self, path : str = None, asFile : bool = True):
        if asFile:
            
            os.makedirs(self._path_usr, exist_ok=True)
            if not path:
                timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
                pathTarget = os.path.join(self._path_usr, f"{timestamp}.json")
            else:
                pathTarget = path
            shutil.copy(self.path_config_file, pathTarget)
        else:
            with open(self.path_config_file, "r") as f:
                data = json.load(f)
            return data
        
    def patch(self, path : str | None = None, parts : typing.List[str] = [], mustHaveKey : bool = False):
        if not parts:
            return
        
        if path is None:
            path = self.path_config_file
        else:
            assert os.path.exists(os.path.join(self.path, path)), f"path {path} not found"
            path = os.path.join(self.path, path)

        data = Json.load(path)

        for part in parts:
            key, val = part.split("=", 1)
            if mustHaveKey:
                assert get_deep(data, *key.split("/")), f"key {key} not found"
            set_deep(data, *key.split("/"), value=val)

        Json.dump(path, data)

    def _import(self, data : str| dict, replaceKeys : typing.List[str] = []):
        flattened_replaceKeys = []
        for key in replaceKeys:
            if ',' in key:
                flattened_replaceKeys.extend(key.split(','))
            else:
                flattened_replaceKeys.append(key)
        replaceKeys = flattened_replaceKeys
        
        if isinstance(data, str):
            data = Json.load(data)

        if not replaceKeys:
            Json.update(self.path_config_file, data)
            return
        
        updata = {}
        for key in replaceKeys:
            updata[key] = get_deep(data, *key.split("/"))
        Json.update(self.path_config_file, updata)


    def _auto(self, lifetime : str|int, capture_output: bool = False):
        def run_picli():
            self.process = subprocess.Popen([self.path_MaaPiCli, "-d"],
                stdout=subprocess.PIPE if capture_output else subprocess.DEVNULL,
                stderr=subprocess.PIPE if capture_output else subprocess.DEVNULL,
                text=True)  # This makes output strings instead of bytes
            self.stdout, self.stderr = self.process.communicate()

        self.process = None
        self.stdout = None
        self.stderr = None
        thread = threading.Thread(target=run_picli)
        thread.start()

        r = remaining_time(lifetime)
        logging.info(f"remaining time: {r}")
        thread.join(timeout=r)
        
        if thread.is_alive():
            logging.info("Process exceeded lifetime, terminating...")
            if self.process:
                self.process.terminate()
                try:
                    self.process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.process.kill()
            
            thread.join(timeout=1)

        if capture_output:
            return self.stdout, self.stderr

    def get_usr_bkups(self):
        files = []
        os.makedirs(self._path_usr, exist_ok=True)
        for file in os.listdir(self._path_usr):
            if file.endswith(".json"):
                files.append(file)
        # return by sorted modified time, latest first
        return sorted(files, key=lambda x: os.path.getmtime(os.path.join(self._path_usr, x)), reverse=True)
    


class MaaPiCliInstance(MaaInstance):
    @cached_property
    def path_interfaceJson(self):
        return os.path.join(self.path, "interface.json")
    
    @cached_property
    def path_MaaPiCli(self):
        return os.path.join(self.path, "MaaPiCli.exe")

    @cached_property
    def path_config_maaOption(self):
        return os.path.join(self.path_config, "maa_option.json")
    
    @cached_property
    def path_config_maaPiConfig(self):
        return os.path.join(self.path_config, "maa_pi_config.json")

    @cached_property
    def path_config_file(self):
        return self.path_config_maaPiConfig
    
    def _auto(self, lifetime : str|int, capture_output: bool = False):
        return run_with_lifetime([self.path_MaaPiCli, "-d"], lifetime, capture_output)

class MaaArknightsInstance(MaaInstance):
    @cached_property
    def path_config_guiJson(self):
        return os.path.join(self.path_config, "gui.json")

    @cached_property
    def path_config_file(self):
        return self.path_config_guiJson

def create(name : str, path : str = None):
    if name != "maa":
        return MaaPiCliInstance(name, path)
    else:
        return MaaArknightsInstance(name, path)