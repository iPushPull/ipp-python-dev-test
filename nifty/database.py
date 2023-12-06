import os
import pandas as pd
import logging
from datetime import date

from sqlalchemy import Column, Integer, String, Float, Date, create_engine, UniqueConstraint
from sqlalchemy.orm import sessionmaker, declarative_base

from .models import SQLAlchemyStockData, Base
from .serializers import StockData

DATABASE_PATH = "sqlite:///stock_market.db"
engine = create_engine(DATABASE_PATH)
Session = sessionmaker(bind=engine)


def setup_db():
    """If there is no database setup it will do so loading the CSV provided."""
    engine = create_engine(DATABASE_PATH)
    if not os.path.exists("stock_market.db"):
        Base.metadata.create_all(engine)
        dataframe = pd.read_csv('./data/nifty50_all.csv')
        dataframe['Symbol'] = dataframe['Symbol'].apply(lambda x: x.upper())
        dataframe['Date'] = pd.to_datetime(dataframe['Date'])
        Session = sessionmaker(bind=engine)
        session = Session()
        for el in dataframe.values:
            stock_data = StockData(date=el[0], symbol=el[1], open=el[2], high=el[3], low=el[4], close=el[5])
            db_model = SQLAlchemyStockData(**stock_data.model_dump())
            session.add(db_model)
        session.commit()
