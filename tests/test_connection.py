from unical import Unical

import os
import unittest
class TestUnical(unittest.TestCase):

    PATH = os.getcwd()
    CONFIG_PATH = os.path.join(PATH, "config")
    CONFIG_FILE = os.path.join(CONFIG_PATH, "config.json")

    def __init__(self, *args, **kwargs):
        unittest.TestCase.__init__(self,  *args, **kwargs)
        self.caldaia = Unical.from_json(self.CONFIG_FILE)


    def test_from_json(self):
        caldaia = Unical.from_json(self.CONFIG_FILE)

        self.assertIsNotNone( caldaia)

    def test_connects(self):
        res = self.caldaia.check_connection()
        self.assertTrue(res)

    def test_read(self):
        data = self.caldaia.read_all()
        l = self.caldaia.data.to_list()

        self.assertIsNotNone(l,list)

        print(l)
        pass


    def test_get_devices(self):
        devices = self.caldaia.get_entities()

        self.assertIsNone(devices)

        self.caldaia.read_all()
        devices = self.caldaia.get_entities()
        self.assertIsNotNone(devices)
        self.assertGreater( len(devices), 1)

    def test_get_device_value(self):
        self.caldaia.read_all(400)
        res = self.caldaia.get_value(400)
        print(res)

if __name__ == "__main_":
    unittest.main()






