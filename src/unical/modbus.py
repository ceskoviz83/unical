import os.path

import pymodbus
import json
from threading import Thread,Lock
from datetime import datetime
import copy
import time

from pymodbus.client import ModbusTcpClient

from .register import RegistryMap
from . import register , const
from .common import ConfigClass


class ModbusConnectionError(Exception):
    pass

class ModbusReadError(Exception):
    pass

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
        self._data_lock = Lock()
        self.isrunning = False

        self._polling_thread = None

        self._client : ModbusTcpClient = ModbusTcpClient(framer=self.framer,
                                       host=self.address,
                                       port=self.port,
                                       reconnect_delay=self.reconnect_delay,
                                       reconnect_delay_max=self.reconnect_delay_max,
                                       timeout=self.timeout,
                                       retries=self.retries)


    @property
    def data(self) -> RegistryMap | None:
        self._data_lock.acquire()
        res = copy.copy(self._data)
        self._data_lock.release()
        return res

    def connect(self) -> bool:

        return self._client.connect()

    def close(self):
        return self._client.close()

    @property
    def connected(self):
        return self._client.connected

    def check_connection(self) -> bool:
        res = True
        with self._client as c: # prova ad aprire la soket
            if not c.connected:
                res = False
                raise ModbusConnectionError(f"Connection to {self.address}:{self.port} failed")
        return res


    def _registry_read_thread(self):
        self.logger.info("Starting continous reading")
        self.logger.info(f"Sample time is {self.sample_time}")
        while self.isrunning:
            try:
                self._data = self.read()
                time.sleep(self.sample_time)
            except ModbusReadError as e:
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


    def registry_set(self, files : str | list[str]):

        if isinstance(files, str):
            files = [files]

        if not isinstance(files, list):
            raise TypeError("files must be a list of string or string")

        register_list = []

        for file in files:
            #DATAFILE = os.path.join(const.CONFIG_ABS_PATH, file)
            with open(file, encoding='utf-8') as f:
                register_list += json.load(f) # append list

        reg = register.RegistryMap(register_list)

        return reg


    def _read_register(self,
                       reg: register.Register,
                       client: ModbusTcpClient = None, ):

        if reg.length > 1:
            pass

        if client is None:
            with self.client as c:
                result = c.read_holding_registers(address=reg.address, count=reg.length, device_id=self.device_id)
                pass
        else:
            result = client.read_holding_registers(address=reg.address, count=reg.length, device_id=self.device_id)

        return result

    def read(self, id = None) -> RegistryMap | None:
        timestamp = datetime.now()

        size = len(self._registry)  # quantità massima di segnali da leggere
        hit = 0  # segnali beccati

        self._data_lock.acquire()

        self._data = copy.copy(self._registry)  # copia

        with self._client as c:
            if not c.connected:
                self.logger.error("Connection failed")
                raise ModbusConnectionError(f"Modbus connection is down")

            self.logger.info(f"Reading data from {self.address}")

            if id is not None:
                result = self._read_register(reg=self._registry[id],
                                             client=c)
                if not result.isError():
                    self._data[id].timestamp = datetime.now()
                    self._data[id].raw = result.registers[0]

            else:
                for idx in self._registry:
                    # leggi e aggiorna il registro
                    reg = self._registry[idx]

                    result = self._read_register(reg=reg,
                                                 client=c)

                    if not result.isError():
                        self._data[idx].timestamp = datetime.now()

                        if reg.length == 1:
                            self._data[idx].raw = result.registers[0]
                        else:
                            self._data[idx].raw = result.registers

                    hit += 1


        self._data_lock.release()

        elapsed =  datetime.now() - timestamp

        self.logger.info(f"Read data from {self.address} - found {hit} over {size} - Elapsed_time = {elapsed.microseconds / 1000}ms")
        return self._data



