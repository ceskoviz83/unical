import json
from dataclasses import dataclass
import pandas as pd
from pymodbus.client import ModbusTcpClient


from .modbus import Modbus
from .database import DB
from .register  import RegistryMap, Register
from enum import StrEnum

class DeviceType(StrEnum):
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

    async def check_connection(self) -> bool:
        try:
            self.modbus.check_connection() # connect or raise ConnectionExeption
        except Unical.ConnectionException as e:
            raise e
        return True

    @classmethod
    def from_config(cls, config: UnicalConfig):
        return cls(modbus_client=config.modbus, db_config=config.db)

    @classmethod
    def from_json(cls, json_filename: str):
        config = UnicalConfig.from_json(json_filename)
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

    def read(self) -> RegistryMap | None:
        return self.modbus.read()

    def get_devices(self) -> list[Register]:
        """Get devices on api."""
        DEV = self.data
        res = [DEV[key] for key in DEV]
        return res

    @property
    def controller_name(self) -> str:
        """Return the name of the controller."""
        return self.modbus.address.replace(".", "_")

    def get_device_value(self,
                         device_id: int) -> int |float |bool:

        res : Register = self.data[device_id]
        return res.value

    def get_device_unique_id(self,
                             device_id: str) -> str:
        """Return a unique device id."""
        res : Register = self.data[device_id]
        return f"{self.controller_name}_{res.device_type}_{res.name}"

    
    def get_devices_by_type(self, type : DeviceType) -> list[Register]:
        return [self.registry[id] for id in self.registry if self.registry[id].type ==  type ]
