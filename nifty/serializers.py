from typing import Any, List
from datetime import date, datetime
from pydantic import BaseModel, Field, validator

class StockData(BaseModel):
    date: date
    symbol: str
    open: float
    high: float
    low: float
    close: float

    class Config:
        from_attributes = True
        json_schema_extra = {
            "properties": {
                "date": {"example": "18/02/1988"},
                "symbol": {"example": "tatamotors"},
                "open": {"example": 150.3},
                "high": {"example": 150.3},
                "low": {"example": 150.3},
                "close": {"example": 150.3}
            }
        }
        json_encoders = {
            date: lambda value: value.strftime("%d/%m/%Y")
        }

class StockUpdateData(BaseModel):
    date: str
    symbol: str
    open: float
    high: float
    low: float
    close: float

    class Config:
        from_attributes = True
        json_schema_extra = {
            "properties": {
                "date": {"example": "18/02/1988"},
                "symbol": {"example": "tatamotors"},
                "open": {"example": 150.3},
                "high": {"example": 150.3},
                "low": {"example": 150.3},
                "close": {"example": 150.3}
            }
        }

    @validator('date')
    def parse_date(cls, value: Any) -> Any:
        if not isinstance(value, str):
            raise ValueError('Date must be a string')

        try:
            return datetime.strptime(value, '%d/%m/%Y').date()
        except ValueError:
            raise ValueError('Invalid date format, should be dd/mm/YYYY')

class StockUpdateRequest(BaseModel):
    data: List[StockUpdateData]

class Symbol(BaseModel):
    symbol: str
    
    class Config:
        from_attributes = True