from unical import Unical
import time

if __name__ == "__main__":
    caldaia = Unical.from_json("config/config.json")

    caldaia.connect()
    #caldaia.read_polling()

    #time.sleep(5)

    #caldaia.stop()

    data = caldaia.read()

    print(data)

    pass





