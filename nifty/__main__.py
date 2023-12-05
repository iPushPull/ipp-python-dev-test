from datetime import datetime, date
from typing import Any, List

import numpy as np
import uvicorn
from fastapi import FastAPI, Query, HTTPException, responses, requests
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import create_engine, extract

from .database import DATABASE_PATH, SQLAlchemyStockData, setup_db, Session
from .models import SQLAlchemyStockData
from .serializers import StockData, StockUpdateRequest, Symbol

session = Session()
app = FastAPI(debug=True)

@app.get('/nifty/stocks/{symbol}', response_model=List[StockData])
async def price_data(symbol: str, year: int = Query(None, description="Filter data by year")) -> Any:
    """
    Return price data for the requested symbol.
    """
    symbol = symbol.upper()
    
    query = session.query(SQLAlchemyStockData).filter(SQLAlchemyStockData.symbol == symbol)
    if query.count() == 0:
        raise HTTPException(status_code=400, detail="Bad Request: incorrect Symbol.")

    # anything before would not make sense
    if year and year < 1800:
        return []

    if year:
        query = query.filter(extract('year', SQLAlchemyStockData.date) == year)

    data = query.order_by(extract('year', SQLAlchemyStockData.date).desc())
    return data

@app.get('/nifty/allowed-symbols/', response_model=List[Symbol])
async def allowed_symbols() -> Any:
    """
    Return the existing symbols in the database by alphabetic order.
    """
    symbols = session.query(SQLAlchemyStockData.symbol).distinct().order_by(SQLAlchemyStockData.symbol.asc()).all()
    return symbols

def calculate_std_dev(session: Session, symbol: str, before_date: date) -> tuple:
    last_fifty_records = session.query(SQLAlchemyStockData).filter(
        SQLAlchemyStockData.symbol == symbol.upper(),
        SQLAlchemyStockData.date < before_date
    ).order_by(SQLAlchemyStockData.date.desc()).limit(50).all()

    open_price_values = [getattr(record, "open") for record in last_fifty_records if getattr(record, "open") is not None]
    close_price_values = [getattr(record, "close") for record in last_fifty_records if getattr(record, "close") is not None]
    high_price_values = [getattr(record, "high") for record in last_fifty_records if getattr(record, "high") is not None]
    low_price_values = [getattr(record, "low") for record in last_fifty_records if getattr(record, "low") is not None]

    std_open = np.std(open_price_values)
    std_close = np.std(close_price_values)
    std_high = np.std(high_price_values)
    std_low = np.std(low_price_values)

    return std_open, std_close, std_high, std_low

@app.post('/nifty/stocks/')
async def price_data(request: StockUpdateRequest) -> dict:
    """
    Add price data for the requested symbol.
    """
    stock_data = request.data.copy()

    for data in stock_data:
        exists = session.query(
            SQLAlchemyStockData
        ).filter(
            SQLAlchemyStockData.date == data.date,
            SQLAlchemyStockData.symbol == data.symbol.upper()
        ).first() is not None

        open_price = data.open
        close_price = data.close
        high_price = data.high
        low_price = data.high

        std_open, std_close, std_high, std_low = calculate_std_dev(session, data.symbol, data.date)

        open_valid = np.abs(open_price) < std_open
        close_valid = np.abs(close_price) < std_close
        high_valid = np.abs(high_price) < std_high
        low_valid = np.abs(low_price) < std_low

        if not exists and open_valid and close_valid and high_valid and low_valid:
            new_stock_data = SQLAlchemyStockData(
                date=data.date,
                symbol=data.symbol.upper(),
                open=data.open,
                high=data.high,
                low=data.low,
                close=data.close
            )
            session.add(new_stock_data)

    session.commit()
    return {"message": "Stock data updated successfully"}

def main() -> None:
    """
    Start the server.
    """
    setup_db()
    uvicorn.run(app, host='0.0.0.0', port=8888)

engine = create_engine(DATABASE_PATH)
main()
