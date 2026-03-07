import json
import os
import sys
from dataclasses import dataclass
import logging
import pandas as pd
from pymodbus.client import ModbusTcpClient

from .modbus import Modbus
from .database import DB
from .register  import RegistryMap, Register
from enum import StrEnum
from .const import UNICAL_PATH

class EntityType(StrEnum):
    """Device types."""
    TEMP_SENSOR = "temp_sensor"
    PRES_SENSOR = "press_sensor"
    PERCENT_SENSOR = "percent_sensor"
    DURATION_SENSOR = "duration_sensor"
    OTHER = "other"
    NOT_KNOWN = "unknown"

class UnicalConfig():
    modbus: Modbus
    db: DB = None
    path = None

    def __init__(self, **kwargs):

        if "path" in kwargs:
            self.path = kwargs["path"] # path della configurazione

        if "modbus" in kwargs:

            # aggiungi il path a registry_file in modo tale che il percorso sia un percorso assoluto
            if isinstance(kwargs["modbus"]["registry_file"], str):
                kwargs["modbus"]["registry_file"] = os.path.join(self.path, kwargs["modbus"]["registry_file"])

            if isinstance(kwargs["modbus"]["registry_file"], list):
                for i, file in enumerate(kwargs["modbus"]["registry_file"]):
                    kwargs["modbus"]["registry_file"][i] = os.path.join(self.path, file)

            self.modbus = Modbus.from_dict(kwargs["modbus"])

        if "db" in kwargs:
            self.db = DB.from_dict(kwargs["db"])

        if not isinstance(self.modbus, Modbus):
            raise TypeError("modbus is not a instance of Modbus")
        if self.db:
            if not isinstance(self.db, DB):
                raise TypeError("db is not a instance of DB")

    @classmethod
    def from_json(cls, abs_filename):
        instance: cls | None = None
        config_path = os.path.dirname(abs_filename) # directory assoluta della configurazione
        with open(abs_filename, encoding='utf-8') as f: # apri il file
            data = json.load(f)
            data['path'] = config_path
            instance = cls(**data)
        return instance

    @property
    def client(self) -> ModbusTcpClient:
        return self.modbus.client


class Unical:

    class ConnectionException(Exception):
        pass

    def __init__(self,
                 modbus_client: Modbus,
                 db_config: DB = None):
        if not isinstance(modbus_client, Modbus):
            raise TypeError("modbus_config is not a instance of Modbus")

        self.modbus : Modbus= modbus_client
        self.db :DB  = db_config
        pass

    def check_connection(self) -> bool:
        try:
            self.modbus.check_connection() # connect or raise ConnectionExeption
        except Unical.ConnectionException as e:
            raise e
        return True

    @classmethod
    def from_config(cls, config: UnicalConfig):
        return cls(modbus_client=config.modbus,
                   db_config=config.db)

    @classmethod
    def from_json(cls, json_abs_filename: str):
        config = UnicalConfig.from_json(json_abs_filename)
        return cls.from_config(config)

    @property
    def registry(self) -> RegistryMap | None:
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

    def read(self, id= None) -> RegistryMap | None:
        return self.modbus.read(id=id)

    def get_entities(self) -> list[Register] | None:
        """Get devices on api."""
        if not self.data:
            print("No devices found - Perhaps you have not called read method?",file=sys.stderr)
            return None
        res = [self.data[key] for key in self.data]
        return res


    def _check_data(self):
        """Check if data is valid."""
        if self.data is None:
            raise ValueError("Data is None - Perhaps you have not called read method?")

    @property
    def controller_name(self) -> str:
        """Return the name of the controller."""
        return self.modbus.address.replace(".", "_")

    def get_value(self,
                  id: int) -> int | float | bool:
        self._check_data()
        res : Register = self.data[id]
        return res.value

    def get_unique_id(self,
                      id: str) -> str:
        """Return a unique device id."""

        self._check_data()

        res : Register = self.data[id]
        return f"{self.controller_name}_{res.entity_type}_{res.name}"

    def get_by_type(self, type : EntityType) -> list[Register]:
        self._check_data()
        return [self.registry[id] for id in self.registry if self.registry[id].entity_type ==  type ]
