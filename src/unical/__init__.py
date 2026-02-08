import copy
import json
import logging
import os
import threading
import time
from dataclasses import dataclass
from datetime import datetime
from logging.handlers import RotatingFileHandler
from os.path import dirname, join as joinpath
from threading import Thread

import pandas as pd
import pymodbus.framer
import sqlalchemy
from pymodbus.client import ModbusTcpClient
from sqlalchemy import create_engine

from unical import const, register
from unical.register import RegistryMap, Register


class ConnectionExeption(Exception):
    """Break out of the with statement"""
    pass


class ConfigClass():
    LOG_DIR = "log"
    LOGGER_NAME = None
    DEBUG_LEVEL = logging.DEBUG

    def __init__(self, **kwargs):

        if not self.LOGGER_NAME:
            raise NotImplementedError("LOGGER_NAME not defined")

        for key in kwargs:
            setattr(self, key, kwargs[key])

        self.logger = self._set_logger()

    @classmethod
    def from_dict(cls, config):
        instance = cls(**config)
        return instance

    def _set_logger(self):
        LOG_PATH = os.path.join(os.getcwd(), self.LOG_DIR)

        if not os.path.exists(LOG_PATH):
            os.mkdir(LOG_PATH)

        logger = logging.getLogger(self.LOGGER_NAME)
        logger.setLevel(self.DEBUG_LEVEL)

        log_filename = os.path.join(LOG_PATH, self.LOGGER_NAME + ".log")

        fh = RotatingFileHandler(log_filename,
                                 mode='a',
                                 maxBytes=5 * 1024 * 1024,
                                 backupCount=2,
                                 encoding=None,
                                 delay=0)

        fh.setLevel(self.DEBUG_LEVEL)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        logger.addHandler(fh)

        return logger


class Modbus(ConfigClass):
    address: str
    registry_file: str
    port: int = 502
    device_id: int = 1
    timeout: int = 10
    retries: int = 3
    sample_time: int = const.SAMPLETIME
    reconnect_delay: float = 0.1
    reconnect_delay_max: int = 300
    framer = pymodbus.FramerType.SOCKET

    LOGGER_NAME = "modbus"

    def __init__(self, **kwargs):

        super().__init__(**kwargs)

        self._registry: RegistryMap | None = None
        if self.registry_file is not None:
            self._registry = self.registry_set(self.registry_file)

        self._data = None
        self._data_lock = threading.Lock()
        self.isrunning = False

        self._polling_thread = None

    @property
    def data(self) -> RegistryMap | None:
        self._data_lock.acquire()
        res = copy.copy(self._data)
        self._data_lock.release()
        return res

    def _registry_read_thread(self):
        self.logger.info("Starting continous reading")
        self.logger.info(f"Sample time is {self.sample_time}")
        while self.isrunning:
            try:
                self._data = self.read()
                time.sleep(self.sample_time)
            except ConnectionExeption as e:
                self.logger.error(e)

        self.logger.info("Stopping continous reading")

    def read_polling(self):
        # Run async function

        self.isrunning = True

        self.logger.info("Starting polling")

        self._polling_thread = Thread(target=self._registry_read_thread, args=())

        self._polling_thread.start()


    def stop_polling(self):
        self.isrunning = False
        self._polling_thread.join()
        self.logger.info("thread finished...exiting")


    def registry_set(self, file):
        DATAFILE = joinpath(dirname(__file__), file)
        register_dict = None
        with open(DATAFILE, encoding='utf-8') as f:
            register_dict = json.load(f)
        reg = register.RegistryMap(register_dict)
        return reg

    @property
    def client(self) -> ModbusTcpClient:

        if self.address is None:
            return None

        return ModbusTcpClient(framer=self.framer, host=self.address, port=self.port,
                               reconnect_delay=self.reconnect_delay, reconnect_delay_max=self.reconnect_delay_max,
                               timeout=self.timeout, retries=self.retries)

    def _read_register(self, reg: register.Register, client: ModbusTcpClient = None, ):

        if client is None:
            with self.client as c:
                result = c.read_holding_registers(address=reg.address, count=reg.length, device_id=self.device_id)

                pass
        else:
            result = client.read_holding_registers(address=reg.address, count=reg.length, device_id=self.device_id)

        return result

    def read(self) -> RegistryMap | None:
        timestamp = datetime.now()

        size = len(self._registry)  # quantità massima di segnali da leggere
        hit = 0  # segnali beccati

        self._data_lock.acquire()

        self._data = copy.copy(self._registry)  # copia

        with self.client as c:
            if not c.connected:
                self.logger.error("Connection failed")
                raise ConnectionExeption("Connection failed")

            self.logger.info(f"Reading data from {self.address}")
            for idx in self._registry:
                # leggi e aggiorna il registro
                reg = self._registry[idx]
                result = self._read_register(reg=reg, client=c)

                if result.isError():
                    self.logger.error(f"Exception code: {result.exception_code}")
                    '''
                    01	Illegal Function	Device doesn't support this function
                    02	Illegal Data Address	Address doesn't exist
                    03	Illegal Data Value	Value out of range
                    04	Slave Device Failure	Device error
                    05	Acknowledge	Request accepted, processing
                    06	Slave Device Busy	Try again later
                    '''

                if not result.isError():
                    self._data[idx].timestamp = timestamp
                    self._data[idx].raw = result.registers[0]

                    hit += 1


        self._data_lock.release()

        elapsed =  datetime.now() - timestamp

        self.logger.info(f"Read data from {self.address} - found {hit} over {size} - Elapsed_time = {elapsed.microseconds / 1000}ms")
        return self._data


@dataclass
class DB(ConfigClass):
    username: str = None
    password: str = None
    address: str = None
    port: int = 502
    database: str = None
    driver: str = "sqlite+pysqlite"

    LOGGER_NAME = "database"

    @property
    def engine(self) -> sqlalchemy.Engine | None:

        if self.address is not None:
            return create_engine(f"{self.driver}:///{self.address}:{self.port}")
        else:
            return None


class UnicalConfig():
    modbus: Modbus
    db: DB = None

    def __init__(self, **kwargs):

        if "modbus" in kwargs:
            self.modbus = Modbus.from_dict(kwargs["modbus"])
        if "db" in kwargs:
            self.db = DB.from_dict(kwargs["db"])

        if not isinstance(self.modbus, Modbus):
            raise TypeError("modbus is not a instance of Modbus")
        if self.db:
            if not isinstance(self.db, DB):
                raise TypeError("db is not a instance of DB")

    @classmethod
    def from_json(cls, filename):
        instance: cls | None = None
        with open(filename, encoding='utf-8') as f:
            data = json.load(f)
            instance = cls(**data)
        return instance

    @property
    def client(self) -> ModbusTcpClient:
        return self.modbus.client

    '''
    def save_history(self):
        tick = self.modbus._registry.to_series()
        tick = pd.DataFrame(tick).T

        if os.path.exists(self.HISTORY_FILE):
            header = False
        else:
            header = True

        tick.to_csv(self.HISTORY_FILE,
                    mode='a',
                    header=header,
                    index=True)

    def get_history(self) -> pd.DataFrame:
        hist = pd.DataFrame()
        if os.path.exists(self.HISTORY_FILE):
            hist = pd.read_csv(self.HISTORY_FILE)

        return hist

    def show_history(self) -> None:
        hist = self.get_history()
        print(hist)
        
    '''


class Unical:

    def __init__(self, modbus_config: Modbus, db_config: DB = None):
        if not isinstance(modbus_config, Modbus):
            raise TypeError("modbus_config is not a instance of Modbus")

        self.modbus = modbus_config
        self.db = db_config

        pass

    @classmethod
    def from_config(cls, config: UnicalConfig):
        return cls(modbus_config=config.modbus, db_config=config.db)

    @classmethod
    def from_json(cls, json_filename: str):
        config = UnicalConfig.from_json(json_filename)
        return cls.from_config(config)

    @property
    def registry(self) -> register.RegistryMap | None:
        return self.modbus._registry

    @property
    def data(self) -> RegistryMap | None:
        return self.modbus.data

    @property
    def df(self) -> pd.DataFrame:
        res = self.modbus.data.to_series()
        res = pd.DataFrame(res).T
        return res

    def read_polling(self):
        self.modbus.read_polling()

    def stop(self):
        self.modbus.stop_polling()

    def read(self) -> RegistryMap | None:
        return self.modbus.read()
