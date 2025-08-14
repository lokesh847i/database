import numpy as np
from scipy.stats import norm
from math import log, sqrt, exp

def calculate_greeks(S, K, T, r, sigma, option_type='call'):
    """
    Calculate option Greeks using Black-Scholes model
    
    Parameters:
    S (float): Current price of the underlying asset (SPX)
    K (float): Strike price of the option
    T (float): Time to expiration in years
    r (float): Risk-free interest rate (annualized)
    sigma (float): Volatility of the underlying (annualized)
    option_type (str): 'call' or 'put'
    
    Returns:
    dict: Dictionary containing price and Greeks
    """
    
    d1 = (log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * sqrt(T))
    d2 = d1 - sigma * sqrt(T)
    
    if option_type == 'call':
        price = S * norm.cdf(d1) - K * exp(-r * T) * norm.cdf(d2)
        delta = norm.cdf(d1)
    elif option_type == 'put':
        price = K * exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)
        delta = -norm.cdf(-d1)
    else:
        raise ValueError("option_type must be 'call' or 'put'")
    
    # Common Greeks for both call and put
    gamma = norm.pdf(d1) / (S * sigma * sqrt(T))
    vega = S * norm.pdf(d1) * sqrt(T) / 100  # per 1% change in volatility
    theta = (-S * norm.pdf(d1) * sigma / (2 * sqrt(T)) - 
             r * K * exp(-r * T) * norm.cdf(d2 if option_type == 'call' else -d2)) / 365
    rho = K * T * exp(-r * T) * norm.cdf(d2 if option_type == 'call' else -d2) / 100  # per 1% change in rate
    
    if option_type == 'put':
        theta = (-S * norm.pdf(d1) * sigma / (2 * sqrt(T)) + 
                 r * K * exp(-r * T) * norm.cdf(-d2)) / 365
        rho = -K * T * exp(-r * T) * norm.cdf(-d2) / 100
    
    return {
        'price': price,
        'delta': delta,
        'gamma': gamma,
        'vega': vega,
        'theta': theta,  # daily theta
        'rho': rho
    }