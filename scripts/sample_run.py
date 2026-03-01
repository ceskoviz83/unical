from unical import Unical


if __name__ == "__main__":
    caldaia = Unical.from_json("../config/config.json")
    caldaia.check_connection()
    #caldaia.read_polling()

    #time.sleep(5)

    #caldaia.stop()

    data = caldaia.read()

    devices = caldaia.get_entities()

    print(caldaia.get_value(400))

    l = caldaia.data.to_list()

    print(data)

    pass