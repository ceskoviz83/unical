from sqlalchemy import String,TIMESTAMP,Integer,Float
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

class Base(DeclarativeBase):
     pass

class Sensor(Base):
     __tablename__ = "sensors"

     id: Mapped[int] = mapped_column(primary_key=True)
     address : Mapped[int]  =  mapped_column(Integer, nullable=False)
     timestamp  = mapped_column(TIMESTAMP, nullable=False)
     name : Mapped[str] = mapped_column(String(30), nullable=False)
     value : Mapped[float]= mapped_column(Float, nullable=False)
     unit : Mapped[str]= mapped_column(String(10), nullable=False)

     def __repr__(self) -> str:
         return f"ID=(id={self.id!r}, name={self.name!r}, value= {self.value + " " + self.unit})"