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
from unical.register  import RegistryMap, Register

from unical.modbus import Modbus
from unical.database import DB

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


class Unical:

    def __init__(self,
                 modbus_config: Modbus,
                 db_config: DB = None):
        if not isinstance(modbus_config, Modbus):
            raise TypeError("modbus_config is not a instance of Modbus")

        self.modbus :Modbus= modbus_config
        self.db :DB  = db_config
        pass

    def connect(self) -> bool:
        self.modbus.check_connection() # connect or raise ConnectionExeption
        return True

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
