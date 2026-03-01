
import sqlalchemy
from dataclasses import dataclass

from .common import ConfigClass
from .modbus import Modbus


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

