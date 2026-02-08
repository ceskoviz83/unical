import os.path

import pymodbus
import json
import threading
from datetime import datetime
import copy

from unical.register import RegistryMap
from pymodbus.client import ModbusTcpClient

from unical import register
from unical.common import ConfigClass
from unical import const

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

    def check_connection(self) -> bool:
        res = True
        with self.client as c:
            if not c.connected:
                res = False
                raise ConnectionExeption("Connection failed")
        return res

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
        DATAFILE = os.path.join(os.getcwd(), const.CONFIG_DIR , file)
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

