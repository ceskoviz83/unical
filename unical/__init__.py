
from unical.const import *

import json
import unical.registry as registry

from os.path import dirname, join as joinpath
DATAFILE = joinpath(dirname(__file__), REGISTRY_FILE)

import asyncio
from pymodbus.client import AsyncModbusTcpClient

class Unical():

    RECONNECT_DELAY = 0.1
    RECONNECT_DELAY_MAX = 300
    TIMEOUT = 3
    RETRIES = 3

    def __init__(self, address, port = 502):

        self.ADDRESS = address
        self.PORT = port

        register_dict = None
        with open(DATAFILE) as f:
            register_dict = json.load(f)
        self.REGISTER = registry.RegistryMap(register_dict)

        pass


    async def _read_register(self, client : AsyncModbusTcpClient,
                             reg : registry.Registry) :

        result = await client.read_holding_registers(address=reg.address,
                                                     count = reg.length,
                                                     slave=1)
        if not result.isError():
            print(f"Data: {result.registers}")
            reg.raw = result.registers


        return result


    async def update(self):
        """Basic async read operation."""
        async with AsyncModbusTcpClient(host=self.ADDRESS,
                                        port = self.PORT,
                                        reconnect_delay = self.RECONNECT_DELAY,
                                        reconnect_delay_max = self.RECONNECT_DELAY_MAX,
                                        timeout = self.TIMEOUT,
                                        retries = self.RETRIES) as client:

            for reg,key in self.REGISTER:
                # leggi e aggiorna il registro
                if reg.read:
                    result = await self._read_register(client,reg)

            return result.registers

    def run(self):
        # Run async function
        data = asyncio.run(self.update())

