import re
import enum

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    TypeDecorator,
    func,
    cast,
)
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import relationship

from .database import Base


class ArrayOfEnum(TypeDecorator):
    impl = ARRAY

    def bind_expression(self, bindvalue):
        return cast(bindvalue, self)

    def result_processor(self, dialect, coltype):
        super_rp = super(ArrayOfEnum, self).result_processor(dialect, coltype)

        def handle_raw_string(value):
            inner = re.match(r"^{(.*)}$", value).group(1)
            return inner.split(",") if inner else []

        def process(value):
            if value is None:
                return None
            return super_rp(handle_raw_string(value))

        return process


class VehicleClassEnum(enum.Enum):
    bike_b = {"short": "bike_b", "long": "Reiðhjól B"}
    bike_c = {"short": "bike_c", "long": "Reiðhjól C"}
    lb_1 = {"short": "lb_1", "long": "Létt bifhjól"}
    lb_2 = {"short": "lb_2", "long": "Hraðhjól 45km/klst"}


class TagEnum(enum.Enum):
    open_frame = "Opin rammi"
    mountain = "Fjallahjól"
    road = "Götuhjól / Racer"
    city = "Borgarhjól"


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
    make = Column(String, default=None)
    classification = Column(Enum(VehicleClassEnum), default=VehicleClassEnum.bike_b)
    price = Column(Integer, nullable=True)
    weight = Column(Integer, nullable=True)
    year = Column(Integer, nullable=True)
    motor_model = Column(String, nullable=True)
    motor_output = Column(Integer, nullable=True)
    image_url = Column(String, nullable=True)
    sku = Column(String)
    last_scraped = Column(DateTime)
    scrape_url = Column(String)
    tags = Column(ARRAY(Enum(TagEnum, create_constraint=False)))
