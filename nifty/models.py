from sqlalchemy import Column, Integer, String, Float, Date, UniqueConstraint
from sqlalchemy.orm import sessionmaker, declarative_base

Base = declarative_base()

class SQLAlchemyStockData(Base):
    __tablename__ = 'stock_data'
    id = Column(Integer, primary_key=True)
    date = Column(Date)
    symbol = Column(String)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    __table_args__ = (
        UniqueConstraint('date', 'symbol', name='unique_date_symbol'),
    )
