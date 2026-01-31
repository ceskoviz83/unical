from pymodbus.client import ModbusTcpClient
import unical
import json


if __name__ == "__main__":

    client = unical.Unical(address='localhost', port=502)

    client.run()
