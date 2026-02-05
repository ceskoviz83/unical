from datetime import datetime
import json
from os.path import dirname, join as joinpath
import src.unical.register as registry
from tabulate import tabulate
import pymodbus.framer
from pymodbus.client import ModbusTcpClient
from unical import const
import time
import os
import pandas as pd

class ConnectionExeption(Exception):
    """Break out of the with statement"""
    pass

class Unical():

    RECONNECT_DELAY = 0.1
    RECONNECT_DELAY_MAX = 300
    TIMEOUT = 3
    RETRIES = 3

    HISTORY_FILE = "history.csv"

    def __init__(self, address,
                 port = 502,
                 device_id=1,
                 registry_file: str = None,):

        self.ADDRESS = address
        self.PORT = port
        self.DEVICE_ID = device_id
        self.FRAMER = pymodbus.FramerType.SOCKET
        self.REGISTER : registry.RegistryMap | None = None

        if registry_file is not None:
            self.REGISTER = self.registry_set(registry_file)

    def __str__(self):
        res = []

        for idx in self.REGISTER:
            res += [self.REGISTER[idx].to_dict()]

        header = res[0].keys()
        rows = [x.values() for x in res]

        return tabulate(rows, headers=header, tablefmt="rst")

    def to_dataframe(self):
        res = []
        for idx in self.REGISTER:
            res += [self.REGISTER[idx].to_dict()]

        return pd.DataFrame(res)

    def to_series(self):
        res = self.to_dataframe()
        T = res['timestamp'].mean()
        res = res[['name','value']]
        res = res.set_index('name')
        res =res['value'] # series
        res['timestamp'] = T
        return res

    def save_history(self):
        tick = self.to_series()
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

    def registry_set(self,file):
        DATAFILE = joinpath(dirname(__file__), file)
        register_dict = None
        with open(DATAFILE, encoding='utf-8') as f:
            register_dict = json.load(f)
        self.REGISTER = registry.RegistryMap(register_dict)
        return self.REGISTER

    @property
    def client(self):
        return ModbusTcpClient( framer=self.FRAMER,
                                host=self.ADDRESS,
                                port = self.PORT,
                                reconnect_delay = self.RECONNECT_DELAY,
                                reconnect_delay_max = self.RECONNECT_DELAY_MAX,
                                timeout = self.TIMEOUT,
                                retries = self.RETRIES)

    def read(self,
             reg: registry.Register,
             client : ModbusTcpClient = None,
             ) :

        if client is None:
            with self.client as c:
                result = c.read_holding_registers(address=reg.address,
                                                     count = reg.length,
                                                     device_id=self.DEVICE_ID)

                pass
        else:
            result = client.read_holding_registers(address=reg.address,
                                              count=reg.length,
                                              device_id=self.DEVICE_ID)

        return result

    def update(self):
        """Basic async read operation."""

        timestamp = datetime.now()
        with self.client as c:
            if not c.connected:
                raise ConnectionExeption("Connection failed")
            for idx in self.REGISTER:
                # leggi e aggiorna il registro
                reg = self.REGISTER[idx]
                if reg.read:
                    result = self.read(reg=reg,
                                       client=c)

                    if result.isError():
                        print(f"Exception code: {result.exception_code}")
                        '''
                        01	Illegal Function	Device doesn't support this function
                        02	Illegal Data Address	Address doesn't exist
                        03	Illegal Data Value	Value out of range
                        04	Slave Device Failure	Device error
                        05	Acknowledge	Request accepted, processing
                        06	Slave Device Busy	Try again later
                        '''
                    if not result.isError():
                        reg.timestamp = timestamp
                        reg.raw = result.registers[0]

            return result.registers



    def run(self):
        # Run async function
        while(1):
            try:
                data = self.update()
                print(self.to_dataframe())
                self.save_history()
            except ConnectionExeption as e:
                print(e)

            time.sleep(const.SAMPLETIME)

