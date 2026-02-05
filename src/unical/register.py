from enum import Enum

from datetime import datetime
from collections.abc import MutableMapping
from src.unical import const


class RegistryT(Enum):
    INT = 0
    BYTE = 1
    BITS = 2
    ASCII = 3
    WORD = 4

class RegistryException(Exception):
    pass

class Mapper[T](MutableMapping):
        def __init__(self):
            self._d = {}

        def __iter__(self):
            return iter(self._d)

        def __len__(self):
            return len(self._d)

        def __repr__(self):
            return f"{self.__class__.__name__}({self._d})"

        def __str__(self):
            return str(self._d)

        def __contains__(self, key):
            return key in self._d.keys()

        def __delitem__(self, key):
            if key not in self._d:
                raise KeyError(key)
            del self._d[key]

        def __setitem__(self, key: str | None, value: T):
            self._d[key] = value

        def __getitem__(self, key):
            if key not in self._d:
                raise KeyError(key)
            return self._d[key]



class Taxonomy(Mapper[str]):
    pass


class Register:
    name: str = None
    address: int = None
    length: int = 0
    read : bool = False
    write : bool = False
    type : str = None
    raw  = None
    unit: str = None
    scale: float = 1.0
    offset: float = 0.0
    bits = None
    timestamp : datetime = None
    taxonomy = None

    def __init__(self,d : dict):

        for key,value in d.items():
            if hasattr(self,key):
                self.__setattr__(key,value)
        return

    def __repr__(self):
        return str(self.to_dict())

    def to_dict(self) -> dict:
        f = {'timestamp': self.timestamp,
             'address': self.address,
             'name': self.name,
             'raw': self.raw,
             'value': self.value,
             'unit': self.unit}
        if self.description:
            f['description'] = self.description

        return f

    def __str__(self):
        return str(self.__repr__())

    @property
    def has_taxonomy(self):
        return True if self.taxonomy is not None else False

    @property
    def description(self) -> list:
        res = []
        if self.raw is None:
            return None
        if self.bits is not None:
            res = []

            for key, val in self.bits.items():
                bit = int(key)

                if (self.raw >> bit) & 1:
                    res.append(val)
            return res
        elif self.taxonomy is not None:
            if str(self.raw) in self.taxonomy.keys():
                res.append(self.taxonomy[str(self.raw)])
        else :
            res =None

        return res

    @property
    def value(self):
        res = self.raw
        if self.type == "INT":
            res = round(self.raw * self.scale + self.offset, ndigits=const.DECIMALS)
        return res

class RegistryMap(Mapper[Register]):

    def __init__(self, d : list):
        super().__init__()
        for el in d:
            item = Register(el)
            self += item


    def __setitem__(self, key : str | None, value : Register):
        if key is None:
            key = value.address
        super().__setitem__(key,value)

    def __add__(self, other : Register):
        if self.__contains__(other.address):
            raise KeyError(other.address)
        self._d[other.address] = other

        return self