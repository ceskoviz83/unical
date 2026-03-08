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
    min : float|int = None
    max : float|int = None
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
    bitmask : list = None
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
             'address': str(self.address),
             'name': self.name,
             'raw': self.raw,
             'value': self.value,
             'unit': self.unit,
             'read': self.read,
             'write': self.write,
             'description': self.description,}

        if self.has_bitmask:
            f['address'] += "." + str(min(self.bitmask))

        return f

    def __str__(self):
        return str(self.__repr__())

    @property
    def has_taxonomy(self):
        return True if self.taxonomy is not None else False

    @property
    def has_bitmask(self):
        return True if self.bitmask is not None else False

    @property
    def has_bits(self):
        return True if self.bits is not None else False

    @property
    def description(self) -> list:
        res = []
        if self.value is None:
            return None
        if self.has_bits:
            res = {}
            for offset in range(self.length):
                word = self.bits[offset]
                for i, desc in enumerate(word):
                    res[desc] = True if (self.value >> i) & 1 == 1 else False
        elif self.taxonomy is not None:
            if str(self.value) in self.taxonomy.keys():
                res.append(self.taxonomy[str(self.value)])
        else :
            res =None

        return res

    @property
    def value(self):
        if not self.read:
            raise RegistryException(f"Register {self.name} is not readable")

        if self.raw is None:
            return None

        res = self.raw

        if self.has_bitmask:
            mask = 0
            shift = min(self.bitmask)
            for bit in self.bitmask:
                mask += 2**bit

            res &= mask  # and dei numeri

            res >>= shift  # shifta

        if self.scale is not None:
            res = round(self.raw * self.scale + self.offset, ndigits=const.DECIMALS)
        return res

    @value.setter
    def value(self, x):
        if not self.write:
            raise RegistryException(f"Register {self.name} is not writable")

        if self.min is not None and x < self.min:
            raise RegistryException(f"Value {x} is out of range for register {self.name} - Min value is {self.min}")

        if self.max is not None and x > self.max:
            raise RegistryException(f"Value {x} is out of range for register {self.name} - Max value is {self.max}")

        if not self.write:
            raise RegistryException(f"Register {self.name} is not writable")

        if self.scale is not None:
            self.raw = int(round((x - self.offset) / self.scale, ndigits=0))

        elif self.has_bitmask:

            bitlen = len(self.bitmask)

            # check if x i complant with max value
            if x > 2**bitlen-1:
                raise RegistryException(f"Value {x} is out of range for register {self.name} - Max value is {2**bitlen-1}")


            if self.has_taxonomy:
                if not self._check_taxonomy_value(x):
                    raise RegistryException(f"Value {x} is not in taxonomy for register {self.name}- allowed values are:{self.taxonomy.keys()}")

            # maschera i valori in ingresso
            mask = 0x0000
            for pos in range(bitlen):
                mask ^= 2**pos

            x &= mask

            mask = 0xffff
            for bit in self.bitmask:
                mask ^= 2**bit

            # setta a zero i bit della maschera
            self.raw &= mask

            x <<= min(self.bitmask) # sposta le posizioni
            self.raw |= x

        elif self.has_taxonomy:
            if self._check_taxonomy_value(x):
                self.raw = x
            else:
                raise RegistryException(f"Value {x} is not in taxonomy for register {self.name} - allowed values are:{self.taxonomy.keys()}")
        else:
            self.raw = int(x)
        return

    def _check_taxonomy_value(self,x) -> bool :
        found = False
        for key in self.taxonomy.keys():
            if str(x) == key:
                found = True
                break

        return found

class RegistryMap(Mapper[Register]):

    def __init__(self, d : list):
        super().__init__()

        for el in d:
            item = Register(el)
            self += item


    def __getitem__(self, key: str|int) -> list | Register:

        key = str(key)
        res = []

        # restituisci l'elenco delle chiavi
        addresses = [s for s in self._d.keys() if key + '.' in s]

        if len(addresses) == 0:
            res = self._d[key]
        elif "." in key:
            res = [self._d[addr] for addr in self._d.keys() if str(key + '.') in addr]

        return res

    def __setitem__(self,
                    key : str | None,
                    reg : Register):
        if key is None:
            key = reg.address

        if reg.has_bitmask:
            key = '.'.join([key,str(min(reg.bitmask))])

        super().__setitem__(str(key), reg)

    def __add__(self, other : Register):
        addr = str(other.address)


        if other.has_bitmask:
            addr = '.'.join([addr,str(min(other.bitmask))])

        if self.__contains__(addr):
            raise KeyError(f"Address {other.address} already exists")

        self._d[addr] = other # __setitem__
        return self

    def __str__(self):
        res = []

        for idx in self:
            res += [self[idx].to_dict()]

        header = res[0].keys()
        rows = [x.values() for x in res]

        return tabulate(rows,
                        headers=header,
                        disable_numparse=True,
                        tablefmt="rst")

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