import enum
import decimal
from collections import namedtuple

from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime, Enum, func
from sqlalchemy.orm import relationship

from .database import Base


class VehicleClassEnum(enum.Enum):
    bike_b = {"short": "bike_b", "long": "Reiðhjól B"}
    bike_c = {"short": "bike_c", "long": "Reiðhjól C"}
    lb_1 = {"short": "lb_1", "long": "Létt bifhjól 1"}
    lb_2 = {"short": "lb_2", "long": "Létt bifhjól 2"}


class Retailer(Base):
    __tablename__ = "retailers"

    id = Column(Integer, primary_key=True, index=True)
    created = Column(DateTime, server_default=func.now())
    name = Column(String)
    slug = Column(String, unique=True)
    website_url = Column(String, nullable=True)


class Model(Base):
    __tablename__ = "models"

    id = Column(Integer, primary_key=True, index=True)
    created = Column(DateTime, server_default=func.now())
    active = Column(Boolean, default=True)

    retailer_id = Column(Integer, ForeignKey(Retailer.id), nullable=True)
    retailer = relationship(Retailer)

    name = Column(String)
    make = Column(String)
    classification = Column(Enum(VehicleClassEnum), default=VehicleClassEnum.bike_b)
    price = Column(Integer, nullable=True)
    weight = Column(Integer, nullable=True)
    year = Column(Integer, nullable=True)
    motor_model = Column(String, nullable=True)
    motor_output = Column(Integer, nullable=True)
    image_url = Column(String, nullable=True)
    sku = Column(String)
    last_scraped = Column(DateTime)
