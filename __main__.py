from unical import UnicalConfig,Unical
import time

if __name__ == "__main__":
    caldaia = Unical.from_json("config/config.json")
    #caldaia.read_polling()

    #time.sleep(5)

    #caldaia.stop()

    caldaia.read()





