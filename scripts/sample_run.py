from unical import Unical


if __name__ == "__main__":
    caldaia = Unical.from_json("../config/config.json")

    registry = caldaia.registry
    print(registry)
    caldaia.check_connection()
    data = caldaia.read(200) # riscaldamento
    print(data)

    print(caldaia.read())

    status = registry[200]

    status.value = 6 #

    caldaia.write(status)

    print(caldaia.read())

    pass