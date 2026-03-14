import os
from sqlalchemy import String,TIMESTAMP,Integer,Float
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from logging.handlers import RotatingFileHandler

import logging

class Base(DeclarativeBase):
     pass

class Sensor(Base):
     __tablename__ = "sensors"

     id: Mapped[int] = mapped_column(primary_key=True)
     address : Mapped[int]  =  mapped_column(Integer, nullable=False)
     timestamp  = mapped_column(TIMESTAMP, nullable=False)
     name : Mapped[str] = mapped_column(String(30), nullable=False)
     value : Mapped[float]= mapped_column(Float, nullable=False)
     unit : Mapped[str]= mapped_column(String(10), nullable=False)


class ConncetionError(Exception):
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

