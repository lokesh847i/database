import pandas as pd
import math
import scipy.stats
from scipy.stats import norm
from scipy.optimize import brentq
import numpy as np
from numpy import abs as ABS, exp as EXP, log as LOG, sqrt as SQRT
import datetime
import mysql.connector
import os

# ----------------------
# Classification functions
# ----------------------
def get_expiry_bucket(dte):
    if pd.isna(dte) or dte < 0:
        return 'EXPIRED'
    elif dte <= 30:
        return 'CM'
    # elif dte <= 60:
    #     return 'NM'
    # elif dte <= 30:
    #     return 'CM'
    else:
        return 'NM'

def get_time_zone(time_str):
    try:
        parts = time_str.split(':')
        hour = int(parts[0])
        minute = int(parts[1])
        time_num = hour * 100 + minute
        if time_num <= 1030:
            return 1, 'OPEN'
        elif time_num <= 1200:
            return 2, 'MID_MORN'
        elif time_num <= 1330:
            return 3, 'LUNCH'
        elif time_num <= 1500:
            return 4, 'AFTERNOON'
        else:
            return 5, 'CLOSE'
    except:
        return 1, 'OPEN'

# ----------------------
# OptionPricing class for Greeks
# ----------------------
class OptionPricing:
    def __init__(self, S, K, r, T):
        self.S = S
        self.K = K
        self.r = r
        self.T = T
        self.IV_LOWER_BOUND = 0.0001

    def ImplVolWithBrent(self, OptionLtp, PricingFunction):
        try:
            ImplVol = brentq(
                lambda sigma: OptionLtp - PricingFunction(sigma),
                0,
                10,
            )
            return max(ImplVol, self.IV_LOWER_BOUND)
        except Exception:
            return self.IV_LOWER_BOUND

    def BS_d1(self, sigma):
        if sigma > self.IV_LOWER_BOUND:
            return (LOG(self.S / self.K) + (self.r + sigma**2 / 2) * self.T) / (sigma * SQRT(self.T))
        return np.inf if self.S > self.K else -np.inf

    def BS_d2(self, sigma):
        return self.BS_d1(sigma) - sigma * SQRT(self.T)

    def BS_CallPricing(self, sigma):
        return norm.cdf(self.BS_d1(sigma)) * self.S - norm.cdf(self.BS_d2(sigma)) * self.K * EXP(-self.r * self.T)

    def BS_PutPricing(self, sigma):
        return norm.cdf(-self.BS_d2(sigma)) * self.K * EXP(-self.r * self.T) - norm.cdf(-self.BS_d1(sigma)) * self.S

    def ThetaCall(self, sigma):
        return -self.S * sigma * norm.pdf(self.BS_d1(sigma)) / (2 * SQRT(self.T)) - self.r * self.K * EXP(-self.r * self.T) * norm.cdf(self.BS_d2(sigma))

    def ThetaPut(self, sigma):
        return -self.S * sigma * norm.pdf(self.BS_d1(sigma)) / (2 * SQRT(self.T)) + self.r * self.K * EXP(-self.r * self.T) * norm.cdf(-self.BS_d2(sigma))

    def Gamma(self, sigma):
        if sigma > self.IV_LOWER_BOUND:
            return norm.pdf(self.BS_d1(sigma)) / (self.S * sigma * SQRT(self.T))
        return 0

    def Vega(self, sigma):
        return norm.pdf(self.BS_d1(sigma)) * self.S * SQRT(self.T)

    def RhoCall(self, sigma):
        return self.K * self.T * EXP(-self.r * self.T) * norm.cdf(self.BS_d2(sigma))

    def RhoPut(self, sigma):
        return -self.K * self.T * EXP(-self.r * self.T) * norm.cdf(-self.BS_d2(sigma))

    def calculate_greeks(self, call_option_ltp, put_option_ltp):
        call_iv = self.ImplVolWithBrent(call_option_ltp, self.BS_CallPricing)
        put_iv = self.ImplVolWithBrent(put_option_ltp, self.BS_PutPricing)

        put_delta = round(norm.cdf(self.BS_d1(put_iv)) - 1, 4)
        call_delta = round(1 + put_delta, 4)

        call_theta = round(self.ThetaCall(call_iv) / 365, 4)
        put_theta = round(self.ThetaPut(put_iv) / 365, 4)

        call_vega = round(self.Vega(call_iv) / 100, 4)
        put_vega = round(self.Vega(put_iv) / 100, 4)

        return [
            round(call_iv * 100, 2), round(put_iv * 100, 2), call_delta, put_delta,
            call_theta, put_theta, round(self.Gamma(call_iv), 4), round(self.Gamma(put_iv), 4),
            call_vega, put_vega, round(self.RhoCall(call_iv), 4), round(self.RhoPut(put_iv), 4)
        ]

def calculate_greeks(row):
    try:
        S = row['spot']
        K = row['strike']
        T = row['dte'] / 365
        r = 0.1
        if T <= 0 or pd.isna(S) or pd.isna(K):
            return [0]*12
        op = OptionPricing(S, K, r, T)
        return op.calculate_greeks(row['ce_close'], row['pe_close'])
    except:
        return [0]*12

output_columns = [
    'trade_date', 'trade_time', 'expiry_date', 'index_name', 'spot', 'atm_strike',
    'strike', 'dte', 'expiry_bucket', 'zone_id', 'zone_name', 'call_strike_type',
    'put_strike_type', 'ce_symbol', 'ce_open', 'ce_high', 'ce_low', 'ce_close',
    'ce_volume', 'ce_oi', 'ce_coi', 'ce_iv', 'ce_delta', 'ce_gamma', 'ce_theta',
    'ce_vega', 'ce_rho', 'pe_symbol', 'pe_open', 'pe_high', 'pe_low', 'pe_close',
    'pe_volume', 'pe_oi', 'pe_coi', 'pe_iv', 'pe_delta', 'pe_gamma', 'pe_theta',
    'pe_vega', 'pe_rho'
]

start_date = '2025-05-01'
end_date = '2025-07-31'
date_range = pd.date_range(start=start_date, end=end_date)

for single_date in date_range:
    single_date_str = single_date.strftime('%Y-%m-%d')
    print(f"🔄 Running for {single_date_str}...")

    try:
        def fetch_data(table):
            conn = mysql.connector.connect(
                host="106.51.63.60",
                user="mahesh",
                password="mahesh_123",
                database="historicaldb"
            )
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM {table} WHERE DATE(date) = '{single_date_str}'")
            df = pd.DataFrame(cursor.fetchall(), columns=[desc[0] for desc in cursor.description])
            cursor.close()
            conn.close()
            if df.empty:
                return df
            df['time'] = df['time'].apply(lambda x: f"{x//3600:02}:{(x%3600)//60:02}")
            for col in ['open', 'high', 'low', 'close']:
                if col in df.columns:
                    df[col] = df[col] / 100
            return df

        df_call = fetch_data("zyduslife_call")
        df_put = fetch_data("zyduslife_put")
        df_cash = fetch_data("zyduslife_cash")

        if df_call.empty or df_put.empty or df_cash.empty:
            print(f"⚠️  Skipping {single_date_str} due to missing data.")
            continue

        df_cash.rename(columns={'close': 'spot'}, inplace=True)
        df_cash = df_cash[['time', 'date', 'spot']]

        df_call.rename(columns={
            'symbol': 'ce_symbol', 'open': 'ce_open', 'high': 'ce_high', 'low': 'ce_low', 'close': 'ce_close',
            'volume': 'ce_volume', 'oi': 'ce_oi', 'coi': 'ce_coi'
        }, inplace=True)
        df_put.rename(columns={
            'symbol': 'pe_symbol', 'open': 'pe_open', 'high': 'pe_high', 'low': 'pe_low', 'close': 'pe_close',
            'volume': 'pe_volume', 'oi': 'pe_oi', 'coi': 'pe_coi'
        }, inplace=True)

        df_merged = pd.merge(df_call, df_put, on=['time', 'expiry', 'strike', 'date'])
        all_df = pd.merge(df_merged, df_cash, on=['time', 'date'])

        all_df['index_name'] = 'zyduslife'
        all_df['atm_strike'] = round(all_df['spot'] / 100) * 100

        strike_increment = 100
        distance = ((all_df['strike'] - all_df['atm_strike']) / strike_increment).round()

        mask_itm = distance < 0
        mask_otm = distance > 0

        all_df['call_strike_type'] = 'ATM'
        all_df.loc[mask_itm, 'call_strike_type'] = 'ITM' + abs(distance[mask_itm]).astype(int).astype(str)
        all_df.loc[mask_otm, 'call_strike_type'] = 'OTM' + distance[mask_otm].astype(int).astype(str)

        all_df['put_strike_type'] = 'ATM'
        all_df.loc[mask_itm, 'put_strike_type'] = 'OTM' + abs(distance[mask_itm]).astype(int).astype(str)
        all_df.loc[mask_otm, 'put_strike_type'] = 'ITM' + distance[mask_otm].astype(int).astype(str)

        all_df['trade_date'] = all_df['date'].apply(lambda x: datetime.datetime.strptime(str(x), '%y%m%d').strftime('%d-%m-%Y'))
        all_df['trade_time'] = all_df['time']
        all_df['expiry_date'] = all_df['expiry'].apply(lambda x: datetime.datetime.strptime(str(x), '%y%m%d').strftime('%d-%m-%Y'))

        def safe_dte(row):
            try:
                expiry_str = str(int(row['expiry']))
                date_str = str(int(row['date']))
                return (datetime.datetime.strptime(expiry_str, '%y%m%d') - datetime.datetime.strptime(date_str, '%y%m%d')).days
            except Exception as e:
                return None
        all_df['dte'] = all_df.apply(safe_dte, axis=1)
        all_df['expiry_bucket'] = all_df['dte'].apply(get_expiry_bucket)
        zones = all_df['trade_time'].apply(lambda t: pd.Series(get_time_zone(t)))
        zones.columns = ['zone_id', 'zone_name']
        all_df[['zone_id', 'zone_name']] = zones

        greek_columns = [
            'call_iv', 'put_iv',
            'call_delta', 'put_delta',
            'call_theta', 'put_theta',
            'call_gamma', 'put_gamma',
            'call_vega', 'put_vega',
            'call_rho', 'put_rho'
        ]

        all_df[greek_columns] = all_df.apply(calculate_greeks, axis=1, result_type='expand')

        greek_map = {
            'call_iv': 'ce_iv', 'call_delta': 'ce_delta', 'call_gamma': 'ce_gamma', 'call_theta': 'ce_theta', 'call_vega': 'ce_vega', 'call_rho': 'ce_rho',
            'put_iv': 'pe_iv', 'put_delta': 'pe_delta', 'put_gamma': 'pe_gamma', 'put_theta': 'pe_theta', 'put_vega': 'pe_vega', 'put_rho': 'pe_rho',
        }
        all_df = all_df.rename(columns=greek_map)

        df_future = fetch_data("zyduslife_future")
        if not df_future.empty:
            df_future.rename(columns={
                'open': 'future_open', 'high': 'future_high', 'low': 'future_low', 'close': 'future_close',
                'volume': 'future_volume', 'oi': 'future_oi', 'coi': 'future_coi'
            }, inplace=True)
            df_future = df_future[['time', 'date', 'future_open', 'future_high', 'future_low', 'future_close', 'future_volume', 'future_oi', 'future_coi']]
            all_df = pd.merge(all_df, df_future, on=['time', 'date'], how='left')

        final_columns = output_columns + [
            'future_open', 'future_high', 'future_low', 'future_close',
            'future_volume', 'future_oi', 'future_coi'
        ]
        output_file = f"{single_date_str}_zyduslife_processed.csv"
        if os.path.exists(output_file):
            os.remove(output_file)

        final_df = all_df[final_columns]
        final_df.to_csv(output_file, index=False)
        print(f"✅ Done: {output_file}")

    except Exception as e:
        print(f"❌ Error for {single_date_str}: {e}")

