import csv
import json
from datetime import datetime
from statistics import mean, stdev

from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.requests import Request
from starlette.routing import Route
import uvicorn


# Global variable to store the data
data = []
async def router(request: Request) -> JSONResponse:
    print(request.method)
    if (request.method == 'GET'):
         return await price_data(request)
    elif(request.method == "POST"):
         return await add_price_data(request)
    elif(request.method == "PUT"):
        print('hello world')
        # mehtod to update 
        
        
        

# Handler for GET /nifty/stocks/{Symbol}
async def price_data(request: Request) -> JSONResponse:
    # Extract the symbol from the path parameters
    symbol = request.path_params['symbol']
    # Extract the year from the query parameters
    year = request.query_params.get('year')
    
    with open('data/nifty50_all.csv', 'r') as file:
        reader = csv.DictReader(file)
        data = [row for row in reader]
    
    # Filter the data based on the symbol 
    filtered_data = [row for row in data if row['Symbol'] == symbol]
    if (len(filtered_data) == 0):
        return JSONResponse({'error': 'Invalid Symbol'}, status_code=400)

    
    # Filter the data based on the year if provided 
    if year:
       try:
           if len(year) != 4:
               return JSONResponse({"Error": "Invalid Year"}, status_code=400)
           
           year = int(year) 
       except ValueError:
            return JSONResponse({"Error": "Invalid Year"}, status_code=400)

    
       try:
            filtered_data = [row for row in filtered_data if datetime.strptime(row['Date'], '%Y-%m-%d').year == year]
       except ValueError:
            return JSONResponse([])
    
    # Sort the filtered data based on the date in descending order
    sorted_data = sorted(filtered_data, key=lambda row: datetime.strptime(row['Date'], '%Y-%m-%d'), reverse=False)
    
    formatted_data = [
        {
            'date': row['Date'],
            'Symbol': row['Symbol'],
            'open': float(row['Open']),
            'high': float(row['High']),
            'low': float(row['Low']),
            'close': float(row['Close'])
        }
        for row in sorted_data
    ]
    
    fieldnames = formatted_data[0].keys()
    
    with open('data/nifty50_all.csv', 'a') as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            for row in formatted_data:
                writer.writerow(row)
    
    # Return the sorted data as a JSON response 
    # return JSONResponse(list(sorted_data))
    return JSONResponse(formatted_data)



# Handler for POST /nifty/stocks/{Symobols}/add
async def add_price_data(request: Request):
    # Extract the symbol from the path parameters
    symbol = request.path_params['symbol']
    try:
        # Parse the JSON data frmo the request body
        new_data = await request.json()
    except json.JSONDecodeError:
        return JSONResponse({'error': 'Invalid JSON data'}, status_code=400)
    
        # Sort the existing data by date in descending order
    new_data.sort(key=lambda new_row: datetime.strptime(new_row['date'], '%d-%m-%Y'), reverse=False)

    for row in new_data:
        try:
            # Extract the necesary fields from the row 
            date = datetime.strptime(row['date'], '%d-%m-%Y').strftime('%Y-%m-%d')
            open_price = float(row['open'])
            close_price = float(row['close'])
            high_price = float(row['high'])
            low_price = float(row['low'])
        except (ValueError, TypeError):
            return JSONResponse({'error': 'Invalid data format'}, status_code=400)
        
        # Check if the new data violates any constrainst 
        prior_data = [d for d in data
                      if d['Symbol'] == symbol and
                      d['Date'] < date]
                        # datetime.strptime(d['Date'], '%Y-%m-%d') < datetime.strptime(date, '%Y-%m-%d')]
                        
        if len(prior_data) >= 50:
            prior_prices = [float(d['Close']) for d in prior_data[-50:]]
            if not (mean(prior_prices) - stdev(prior_prices) <= close_price <= mean(prior_prices) + stdev(prior_prices)):
                return JSONResponse({'error': 'Price is not within 1 standard deviation of the prior 50 values'}, status_code=400)
            
        # Add the new data to the global data list 
        new_row = {
        'Date': date,
        'Symbol': symbol,
        'Open': open_price,
        'Close': close_price,
        'High': high_price,
        'Low': low_price,
        
    }
        

        
        
        data.append(new_row)
        # Append the new data to the CSV file
        with open('data/nifty50_all.csv', 'a') as file:
            writer = csv.DictWriter(file, fieldnames=new_row.keys())
            writer.writerow(new_row)
    
    # Return a success message as a JSON response
    return JSONResponse(new_row)





# Create the Starlette application
app = Starlette(debug=True, routes=[
    Route('/nifty/stocks/{symbol}', router, methods=['GET', 'POST',]),
    # Route('/nifty/stocks/{symbol}/add', add_price_data, methods=['POST']) 
])

# Main function to run the application 
def main() -> None:
    global data
    # Load the initial data form the CVS file 
    with open('data/nifty50_all.csv', 'r') as file:
        reader = csv.DictReader(file)
        data = [row for row in reader]
    # Run the application using Uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8888)

if __name__ == "__main__":
    main()
