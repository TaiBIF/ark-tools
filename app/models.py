from sqlalchemy import (
    Column,
    Integer,
    Numeric,
    String,
    Text,
    DateTime,
    Date,
    Boolean,
    ForeignKey,
    Table,
    desc,
    select,
)

from app.database import (
    Base,
    session,
    TimestampMixin,
)


class Ark(Base):
    __tablename__ = 'ark'

    identifier = Column(String(100), primary_key=True, autoincrement=False) # {naan}/{shoulder}{assigned_name}
    naan = Column(Integer, ForeignKey('naan.naan'))
    assigned_name = Column(String(1000))
    shoulder = Column(String(20), ForeignKey('shoulder.shoulder'))
    url = Column(String(1000))
    who = Column(String(500))
    what = Column(String(500))
    when = Column(String(500))

class Naan(Base, TimestampMixin):
    __tablename__ = 'naan'

    naan = Column(Integer, primary_key=True, autoincrement=False)
    name = Column(String(500))
    description = Column(Text)
    url = Column(String(1000))

class Shoulder(Base, TimestampMixin):
    __tablename__ = 'shoulder'

    shoulder = Column(String(50), primary_key=True, autoincrement=False)
    naan = Column(Integer, ForeignKey('naan.naan'))
    name = Column(String(500))
    description = Column(Text)
    redirect_prefix = Column(String(1000))
    template = Column(String(50), default='.reedede')
