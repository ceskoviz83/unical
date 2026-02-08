import json
from dataclasses import dataclass
import pandas as pd
from pymodbus.client import ModbusTcpClient
from unical.register  import RegistryMap, Register

from unical.modbus import Modbus
from unical.database import DB

from enum import StrEnum

class DeviceType(StrEnum):
    """Device types."""
    TEMP_SENSOR = "temp_sensor"
    OTHER = "other"
    NOT_KNOWN = "unknown"


@dataclass
class Device:
    """API device."""

    device_id: int
    device_unique_id: str
    device_type: DeviceType
    name: str
    state: int | bool
    value: int
    unit: str

    def get_device_name(self, device_id: str, device_type: DeviceType) -> str:
        """Return the device name."""
        if self.device_type == DeviceType.DOOR_SENSOR:
            return f"DoorSensor{self.device_id}"
        if self.device_type == DeviceType.TEMP_SENSOR:
            return f"TempSensor{self.device_id}"
        return f"OtherSensor{self.device_id}"



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

        if res.device_type == DeviceType.DOOR_SENSOR:
            return f"{self.controller_name}_D{res.name}"
        if res.device_type == DeviceType.TEMP_SENSOR:
            return f"{self.controller_name}_T{res.name}"
        return f"{self.controller_name}_Z{res.name}"