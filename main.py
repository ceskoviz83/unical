from unical import Unical


if __name__ == "__main__":

    caldaia = Unical(address='homeassistant.local',
                         port=502,
                         registry_file='sensors.json')

    caldaia.run()





