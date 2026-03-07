from enum import Enum
from tabulate import tabulate
from datetime import datetime
import pandas as pd
from collections.abc import MutableMapping
from collections import UserList,UserDict
from . import const

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
    raw : int|list = None
    unit: str = None
    scale: float = None
    offset: float = 0
    entity_type : str = None
    device: str = None
    timestamp : datetime = None
    taxonomy :dict = None
    bits: dict = None

    def __init__(self,d : dict):

        for key,value in d.items():
            if hasattr(self,key):
                self.__setattr__(key,value)
        if self.length == 0 :
            raise RegistryException(f"Register {self.name} has no length")

        return

    def __repr__(self):

        res = ""

        for key in self.to_dict():
            res += f"{key}: {self.to_dict()[key]} - "
        return res

    def to_dict(self) -> dict:
        f = {'timestamp': self.timestamp,
             'address': self.address,
             'name': self.name,
             'raw': self.raw,
             'value': self.value,
             'unit': self.unit,
             'description': self.description,}

        return f

    def __str__(self):
        return str(self.__repr__())

    @property
    def has_taxonomy(self):
        return True if self.taxonomy is not None else False

    @property
    def has_bits(self):
        return True if self.bits is not None else False

    @property
    def description(self) -> list:
        res = []
        if self.raw is None:
            return None
        if self.has_bits:
            res = {}
            for offset in range(self.length):
                word = self.bits[offset]
                for i, desc in enumerate(word):
                    res[desc] = True if (self.raw >> i) & 1 == 1 else False
        elif self.taxonomy is not None:
            if str(self.raw) in self.taxonomy.keys():
                res.append(self.taxonomy[str(self.raw)])
        else :
            res =None

        return res



    @property
    def value(self):
        res = self.raw

        if self.scale is not None:
            res = round(self.raw * self.scale + self.offset, ndigits=const.DECIMALS)
        return res

class RegistryMap(Mapper[Register]):

    def __init__(self, d : list):
        super().__init__()

        for el in d:
            item = Register(el)
            self += item


    def __setitem__(self,
                    key : str | None,
                    value : Register):
        if key is None:
            key = value.address
        super().__setitem__(key,value)


    def __add__(self, other : Register):
        if self.__contains__(other.address):
            raise KeyError(other.address)
        self._d[other.address] = other
        return self

    def __str__(self):
        res = []

        for idx in self:
            res += [self[idx].to_dict()]

        header = res[0].keys()
        rows = [x.values() for x in res]

        return tabulate(rows, headers=header, tablefmt="rst")

    def to_list(self) -> UserList[Register]:
        return UserList[Register]([self[key] for key in self])

    def to_dict(self) -> UserDict[int,Register]:
        return UserDict[int,Register]({int(key) : self[key].to_dict() for key in self})

    def to_dataframe(self):
        res = []
        for idx in self.register:
            res += [self.register[idx].to_dict()]

        return pd.DataFrame(res)

    def to_series(self):
        res = self.to_dataframe()
        T = res['timestamp'].mean()
        res = res[['name','value']]
        res = res.set_index('name')
        res =res['value'] # series
        res['timestamp'] = T
        return res