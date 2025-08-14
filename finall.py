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
import glob
from config import *  # Import all configuration

# ----------------------
# Section 1: Check Missing Dates
# ----------------------
def check_missing_dates(folder_path, start_date, end_date):
    """
    Check for missing dates by comparing database dates with CSV files in the specified folder.
    Returns a list of missing dates.
    """
    print("🔍 Checking for missing dates...")
    
    # Get all CSV files in the folder
    csv_files = glob.glob(os.path.join(folder_path, "*.csv"))
    print(f"📁 Found {len(csv_files)} CSV files in {folder_path}")
    
    # Extract dates from CSV filenames
    csv_dates = set()
    for csv_file in csv_files:
        filename = os.path.basename(csv_file)
        # Extract date from filename (assuming format: YYYY-MM-DD_tablename_processed.csv)
        try:
            date_part = filename.split('_')[0]
            if len(date_part) == 10 and date_part.count('-') == 2:
                csv_dates.add(date_part)
        except:
            continue
    
    print(f"📅 Dates found in CSV files: {len(csv_dates)}")
    
    # Get dates from database
    db_dates = set()
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Get all unique dates from the database tables
        tables = [TABLE_CONFIG["call_table"], TABLE_CONFIG["put_table"], TABLE_CONFIG["cash_table"]]
        for table in tables:
            cursor.execute(f"SELECT DISTINCT date FROM {table} WHERE date BETWEEN '{start_date.replace('-', '')}' AND '{end_date.replace('-', '')}'")
            table_dates = cursor.fetchall()
            for (date,) in table_dates:
                # Convert YYMMDD format to YYYY-MM-DD format
                try:
                    # Handle YYMMDD format (e.g., 241101 -> 2024-11-01)
                    if len(str(date)) == 6:
                        year = str(date)[:2]
                        month = str(date)[2:4]
                        day = str(date)[4:6]
                        # Convert YY to YYYY (assuming 20xx for years)
                        full_year = f"20{year}"
                        formatted_date = f"{full_year}-{month}-{day}"
                        db_dates.add(formatted_date)
                except:
                    continue
        
        cursor.close()
        conn.close()
        
        print(f"🗄️  Dates found in database: {len(db_dates)}")
        
    except Exception as e:
        print(f"❌ Error connecting to database: {e}")
        return []
    
    # Find missing dates (dates in database but not in CSV files)
    # Only dates that exist in database but not in CSV are considered missing
    missing_dates = db_dates - csv_dates
    missing_dates = sorted(list(missing_dates))
    
    print(f"❌ Missing dates: {len(missing_dates)}")
    if missing_dates:
        print("📋 Missing dates list (dates in database but no CSV file):")
        for date in missing_dates:
            print(f"   - {date}")
    else:
        print("✅ No missing dates found!")
    
    # Also show dates that exist in CSV but not in database (for reference)
    csv_only_dates = csv_dates - db_dates
    if csv_only_dates:
        print(f"\n⚠️  Note: {len(csv_only_dates)} dates exist in CSV files but not in database:")
        print("   (These are not considered missing, but you may want to investigate)")
        for date in sorted(list(csv_only_dates))[:10]:  # Show first 10
            print(f"   - {date}")
        if len(csv_only_dates) > 10:
            print(f"   ... and {len(csv_only_dates) - 10} more")
    
    return missing_dates

# ----------------------
# Section 2: Process Data and Generate CSV Files
# ----------------------
def process_data_for_dates(dates_to_process, output_folder):
    """
    Process data for the specified dates and save CSV files in the output folder.
    """
    print(f"🔄 Processing data for {len(dates_to_process)} dates...")
    
    for single_date_str in dates_to_process:
        print(f"🔄 Running for {single_date_str}...")
        
        try:
            def fetch_data(table):
                conn = mysql.connector.connect(**DB_CONFIG)
                cursor = conn.cursor()
                # Convert YYYY-MM-DD to YYMMDD format for database query
                db_date = single_date_str.replace("-", "")
                cursor.execute(f"SELECT * FROM {table} WHERE date = '{db_date}'")
                df = pd.DataFrame(cursor.fetchall(), columns=[desc[0] for desc in cursor.description])
                cursor.close()
                conn.close()
                if df.empty:
                    return df
                df['time'] = df['time'].apply(lambda x: PROCESSING_CONFIG["time_format"] % (x//3600, (x%3600)//60))
                for col in ['open', 'high', 'low', 'close']:
                    if col in df.columns:
                        df[col] = df[col] / PROCESSING_CONFIG["price_divisor"]
                return df

            df_call = fetch_data(TABLE_CONFIG["call_table"])
            df_put = fetch_data(TABLE_CONFIG["put_table"])
            df_cash = fetch_data(TABLE_CONFIG["cash_table"])

            if df_call.empty or df_put.empty or df_cash.empty:
                print(f"⚠️  Skipping {single_date_str} due to missing data.")
                continue

            df_cash.rename(columns={'close': 'spot'}, inplace=True)
            df_cash = df_cash[['time', 'date', 'spot']]

            df_call.rename(columns=COLUMN_MAPPINGS["call_columns"], inplace=True)
            df_put.rename(columns=COLUMN_MAPPINGS["put_columns"], inplace=True)

            df_merged = pd.merge(df_call, df_put, on=['time', 'expiry', 'strike', 'date'])
            all_df = pd.merge(df_merged, df_cash, on=['time', 'date'])

            all_df['index_name'] = INDEX_CONFIG["index_name"]
            all_df['atm_strike'] = round(all_df['spot'] / INDEX_CONFIG["strike_increment"]) * INDEX_CONFIG["strike_increment"]

            strike_increment = INDEX_CONFIG["strike_increment"]
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
            
            if ENABLE_EXPIRY_BUCKET_CLASSIFICATION:
                all_df['expiry_bucket'] = all_df['dte'].apply(get_expiry_bucket)
            
            if ENABLE_TIME_ZONE_CLASSIFICATION:
                zones = all_df['trade_time'].apply(lambda t: pd.Series(get_time_zone(t)))
                zones.columns = ['zone_id', 'zone_name']
                all_df[['zone_id', 'zone_name']] = zones

            if ENABLE_GREEKS_CALCULATION:
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

            if ENABLE_FUTURE_DATA:
                df_future = fetch_data(TABLE_CONFIG["future_table"])
                if not df_future.empty:
                    df_future.rename(columns=COLUMN_MAPPINGS["future_columns"], inplace=True)
                    df_future = df_future[['time', 'date', 'future_open', 'future_high', 'future_low', 'future_close', 'future_volume', 'future_oi', 'future_coi']]
                    all_df = pd.merge(all_df, df_future, on=['time', 'date'], how='left')

            final_columns = OUTPUT_COLUMNS
            if ENABLE_FUTURE_DATA:
                final_columns = OUTPUT_COLUMNS + [
                    'future_open', 'future_high', 'future_low', 'future_close',
                    'future_volume', 'future_oi', 'future_coi'
                ]
            
            # Create output folder if it doesn't exist
            os.makedirs(output_folder, exist_ok=True)
            
            output_file = os.path.join(output_folder, f"{single_date_str}_{OUTPUT_CONFIG['file_prefix']}_{OUTPUT_CONFIG['file_suffix']}")
            if os.path.exists(output_file):
                os.remove(output_file)

            final_df = all_df[final_columns]
            final_df.to_csv(output_file, index=False)
            print(f"✅ Done: {output_file}")

        except Exception as e:
            print(f"❌ Error for {single_date_str}: {e}")

# ----------------------
# Classification functions
# ----------------------
def get_expiry_bucket(dte):
    if pd.isna(dte) or dte < 0:
        return 'EXPIRED'
    elif dte <= EXPIRY_CONFIG["current_month"]:
        return 'CM'
    # elif dte <= EXPIRY_CONFIG.get("next_month", 60):
    #     return 'NM'
    else:
        return 'NM'

def get_time_zone(time_str):
    try:
        parts = time_str.split(':')
        hour = int(parts[0])
        minute = int(parts[1])
        time_num = hour * 100 + minute
        if time_num <= TIME_ZONE_CONFIG["open_time"]:
            return 1, 'OPEN'
        elif time_num <= TIME_ZONE_CONFIG["mid_morning"]:
            return 2, 'MID_MORN'
        elif time_num <= TIME_ZONE_CONFIG["lunch_time"]:
            return 3, 'LUNCH'
        elif time_num <= TIME_ZONE_CONFIG["afternoon"]:
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
        self.IV_LOWER_BOUND = GREEKS_CONFIG["iv_lower_bound"]

    def ImplVolWithBrent(self, OptionLtp, PricingFunction):
        try:
            ImplVol = brentq(
                lambda sigma: OptionLtp - PricingFunction(sigma),
                0,
                GREEKS_CONFIG["iv_upper_bound"],
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
        r = GREEKS_CONFIG["risk_free_rate"]
        if T <= 0 or pd.isna(S) or pd.isna(K):
            return [0]*12
        op = OptionPricing(S, K, r, T)
        return op.calculate_greeks(row['ce_close'], row['pe_close'])
    except:
        return [0]*12

# ----------------------
# Main execution
# ----------------------
if __name__ == "__main__":
    print("=" * 60)
    print(f"📊 {INDEX_CONFIG['index_name'].upper()} Data Processing Tool")
    print("=" * 60)
    
    # Section 1: Check for missing dates
    print("\n🔍 SECTION 1: Checking for missing dates...")
    missing_dates = check_missing_dates(
        FOLDER_CONFIG["csv_folder_path"], 
        DATE_CONFIG["start_date"], 
        DATE_CONFIG["end_date"]
    )
    
    # Section 2: Interactive prompt for processing
    print("\n🔄 SECTION 2: Processing decision...")
    
    if missing_dates:
        print(f"📅 Found {len(missing_dates)} missing dates:")
        for date in missing_dates:
            print(f"   - {date}")
        
        print(f"\n💡 These dates will be processed into {len(OUTPUT_COLUMNS) + 7} columns (including future data)")
        print(f"📁 Output will be saved to: {FOLDER_CONFIG['output_folder']}/")
        
        while True:
            user_input = input("\n❓ Do you want to process these missing dates? (yes/no): ").lower().strip()
            
            if user_input in ['yes', 'y', '1']:
                print(f"\n🚀 Starting to process {len(missing_dates)} missing dates...")
                process_data_for_dates(missing_dates, FOLDER_CONFIG["output_folder"])
                break
            elif user_input in ['no', 'n', '0']:
                print("⏸️  Processing cancelled by user.")
                break
            else:
                print("❌ Please enter 'yes' or 'no'")
    else:
        print("✅ All dates are already processed. No action needed.")
    
    print("\n🎉 Processing completed!")

