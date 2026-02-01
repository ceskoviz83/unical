from pymodbus.client import ModbusTcpClient
from pymodbus.pdu.register_message import ReadInputRegistersResponse

import unical
import const


if __name__ == "__main__":

    caldaia = unical.Unical(address='192.168.1.121',
                            port=502,
                            registry_file='sensors.json')

    caldaia.run()





