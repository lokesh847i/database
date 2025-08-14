import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from greeks import calculate_greeks

def parse_date(date_str):
    """Parse date in format YYMMDD to datetime object"""
    return datetime.strptime(str(date_str), '%y%m%d')

def calculate_time_to_expiry(expiry_date, current_date=None):
    """Calculate time to expiry in years"""
    if current_date is None:
        current_date = datetime.now()
    
    # Parse expiry date
    if isinstance(expiry_date, str):
        expiry = parse_date(expiry_date)
    else:
        expiry = parse_date(str(expiry_date))
    
    # Calculate days to expiry
    days_to_expiry = (expiry - current_date).days
    
    # Convert to years (assuming 365 days per year)
    return max(days_to_expiry / 365.0, 0.001)  # Minimum 0.001 years to avoid division by zero

def calculate_greeks_for_options(csv_file, output_file, current_price=None, risk_free_rate=0.05, volatility=0.25):
    """
    Calculate Greeks for all options in the CSV file
    
    Parameters:
    csv_file (str): Path to input CSV file
    output_file (str): Path to output CSV file
    current_price (float): Current price of underlying (if None, will use close price)
    risk_free_rate (float): Risk-free interest rate (default 5%)
    volatility (float): Volatility estimate (default 25%)
    """
    
    # Read the CSV file
    print(f"Reading CSV file: {csv_file}")
    df = pd.read_csv(csv_file)
    
    # Display basic info
    print(f"Found {len(df)} options")
    print(f"Columns: {list(df.columns)}")
    
    # Initialize lists to store Greeks
    prices = []
    deltas = []
    gammas = []
    vegas = []
    thetas = []
    rhos = []
    
    # Process each option
    for index, row in df.iterrows():
        try:
            # Extract option parameters
            S = current_price if current_price is not None else row['close']  # Current price
            K = row['strike']  # Strike price
            T = calculate_time_to_expiry(row['expiry'])  # Time to expiry
            
            # Calculate Greeks
            greeks = calculate_greeks(
                S=S, 
                K=K, 
                T=T, 
                r=risk_free_rate, 
                sigma=volatility, 
                option_type='call'
            )
            
            # Store results
            prices.append(greeks['price'])
            deltas.append(greeks['delta'])
            gammas.append(greeks['gamma'])
            vegas.append(greeks['vega'])
            thetas.append(greeks['theta'])
            rhos.append(greeks['rho'])
            
            if index % 1000 == 0:
                print(f"Processed {index + 1} options...")
                
        except Exception as e:
            print(f"Error processing row {index}: {e}")
            # Add NaN values for failed calculations
            prices.append(np.nan)
            deltas.append(np.nan)
            gammas.append(np.nan)
            vegas.append(np.nan)
            thetas.append(np.nan)
            rhos.append(np.nan)
    
    # Add Greeks columns to the dataframe
    df['calculated_price'] = prices
    df['delta'] = deltas
    df['gamma'] = gammas
    df['vega'] = vegas
    df['theta'] = thetas
    df['rho'] = rhos
    
    # Add calculation parameters
    df['current_price'] = S
    df['risk_free_rate'] = risk_free_rate
    df['volatility'] = volatility
    df['time_to_expiry_years'] = [calculate_time_to_expiry(row['expiry']) for _, row in df.iterrows()]
    
    # Save to new CSV file
    print(f"Saving results to: {output_file}")
    df.to_csv(output_file, index=False)
    print(f"Successfully saved {len(df)} options with Greeks to {output_file}")
    
    # Display summary statistics
    print("\nSummary Statistics:")
    print(f"Average Delta: {np.nanmean(deltas):.4f}")
    print(f"Average Gamma: {np.nanmean(gammas):.6f}")
    print(f"Average Vega: {np.nanmean(vegas):.4f}")
    print(f"Average Theta: {np.nanmean(thetas):.4f}")
    print(f"Average Rho: {np.nanmean(rhos):.4f}")
    
    return df

if __name__ == "__main__":
    # Configuration
    input_csv = "active_df_call.csv"
    output_csv = "options_with_greeks.csv"
    
    # You can adjust these parameters based on your needs
    current_price = None  # Set to specific price if needed, otherwise uses close price
    risk_free_rate = 0.05  # 5% annual rate
    volatility = 0.25  # 25% annual volatility
    
    # Calculate Greeks
    result_df = calculate_greeks_for_options(
        csv_file=input_csv,
        output_file=output_csv,
        current_price=current_price,
        risk_free_rate=risk_free_rate,
        volatility=volatility
    )
    
    # Display first few rows
    print("\nFirst 5 rows of results:")
    print(result_df[['symbol', 'strike', 'close', 'calculated_price', 'delta', 'gamma', 'vega', 'theta', 'rho']].head()) 