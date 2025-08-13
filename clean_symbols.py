import pandas as pd
import re
import sys
import zipfile
import os
from pathlib import Path

def process_zip_file(zip_path, output_dir=None):
    """
    Extract and process all CSV files in a zip file
    
    Args:
        zip_path (str): Path to the zip file
        output_dir (str): Directory to save processed files
    """
    if output_dir is None:
        output_dir = f"{Path(zip_path).stem}_symbols_cleaned"
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    processed_files = []
    
    print(f"Processing zip file: {zip_path}")
    print(f"Output directory: {output_dir}")
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            # Get list of CSV files in the zip
            csv_files = [f for f in zip_ref.namelist() if f.lower().endswith('.csv')]
            
            if not csv_files:
                print("No CSV files found in the zip file!")
                return []
            
            print(f"Found {len(csv_files)} CSV files in zip:")
            for csv_file in csv_files:
                print(f"  - {csv_file}")
            
            # Process each CSV file
            for csv_file in csv_files:
                print(f"\n--- Processing: {csv_file} ---")
                
                try:
                    # Read CSV from zip
                    with zip_ref.open(csv_file) as file:
                        df = pd.read_csv(file)
                    
                    print(f"Original shape: {df.shape}")
                    print(f"Sample original symbols:")
                    print(df['symbol'].head(5).tolist())
                    
                    # Clean the symbol column - remove all suffixes (dash + Roman numerals, .NSE, .BE.NSE, etc.)
                    # This pattern matches dash followed by Roman numerals OR any dot followed by letters
                    df['symbol'] = df['symbol'].str.replace(r'-[IVX]+$|\.\w+(\.\w+)*$', '', regex=True)
                    
                    print(f"Sample cleaned symbols:")
                    print(df['symbol'].head(5).tolist())
                    
                    # Save processed file
                    output_filename = f"{Path(csv_file).stem}_symbols_cleaned.csv"
                    output_path = os.path.join(output_dir, output_filename)
                    df.to_csv(output_path, index=False)
                    
                    processed_files.append(output_path)
                    print(f"Saved: {output_path}")
                
                except Exception as e:
                    print(f"Error processing {csv_file}: {e}")
                    continue
    
    except Exception as e:
        print(f"Error reading zip file: {e}")
        return []
    
    print(f"\n=== SUMMARY ===")
    print(f"Successfully processed {len(processed_files)} files:")
    for file_path in processed_files:
        print(f"  - {file_path}")
    
    return processed_files

def process_directory(dir_path, output_dir=None):
    """
    Process all CSV files in a directory
    
    Args:
        dir_path (str): Path to the directory
        output_dir (str): Directory to save processed files
    """
    if output_dir is None:
        output_dir = f"{Path(dir_path).stem}_symbols_cleaned"
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    processed_files = []
    
    print(f"Processing directory: {dir_path}")
    print(f"Output directory: {output_dir}")
    
    # Get list of CSV files in the directory
    csv_files = [f for f in os.listdir(dir_path) if f.lower().endswith('.csv')]
    
    if not csv_files:
        print("No CSV files found in the directory!")
        return []
    
    print(f"Found {len(csv_files)} CSV files:")
    for csv_file in csv_files:
        print(f"  - {csv_file}")
    
    # Process each CSV file
    for csv_file in csv_files:
        print(f"\n--- Processing: {csv_file} ---")
        
        try:
            # Read CSV file
            file_path = os.path.join(dir_path, csv_file)
            df = pd.read_csv(file_path)
            
            print(f"Original shape: {df.shape}")
            print(f"Sample original symbols:")
            print(df['symbol'].head(5).tolist())
            
            # Clean the symbol column - remove all suffixes (dash + Roman numerals, .NSE, .BE.NSE, etc.)
            # This pattern matches dash followed by Roman numerals OR any dot followed by letters
            df['symbol'] = df['symbol'].str.replace(r'-[IVX]+$|\.\w+(\.\w+)*$', '', regex=True)
            
            print(f"Sample cleaned symbols:")
            print(df['symbol'].head(5).tolist())
            
            # Save processed file
            output_filename = f"{Path(csv_file).stem}_symbols_cleaned.csv"
            output_path = os.path.join(output_dir, output_filename)
            df.to_csv(output_path, index=False)
            
            processed_files.append(output_path)
            print(f"Saved: {output_path}")
        
        except Exception as e:
            print(f"Error processing {csv_file}: {e}")
            continue
    
    print(f"\n=== SUMMARY ===")
    print(f"Successfully processed {len(processed_files)} files:")
    for file_path in processed_files:
        print(f"  - {file_path}")
    
    return processed_files

def clean_symbol_names(input_file=None, output_dir=None):
    """
    Remove Roman numerals and dashes from symbol names in CSV file, zip file, or directory
    Example: AARTIIND-I becomes AARTIIND
    
    Args:
        input_file (str): Path to the input CSV/ZIP file or directory. If None, will prompt for input.
        output_dir (str): Directory to save processed files (for zip/directory processing)
    """
    # Get input file name
    if input_file is None:
        input_file = input("Enter the file/directory name (CSV, ZIP, or directory): ").strip()
    
    # Check if input is a zip file
    if input_file.lower().endswith('.zip'):
        print("Detected ZIP file - processing all CSV files inside...")
        return process_zip_file(input_file, output_dir)
    
    # Check if input is a directory
    if os.path.isdir(input_file):
        print("Detected directory - processing all CSV files inside...")
        return process_directory(input_file, output_dir)
    
    # Read the CSV file (original functionality)
    print(f"Reading {input_file}...")
    try:
        df = pd.read_csv(input_file)
    except FileNotFoundError:
        print(f"Error: File '{input_file}' not found!")
        return None
    except Exception as e:
        print(f"Error reading file: {e}")
        return None
    
    # Display original shape and sample symbols
    print(f"Original shape: {df.shape}")
    print(f"Sample original symbols:")
    print(df['symbol'].head(10).tolist())
    
    # Clean the symbol column - remove all suffixes (dash + Roman numerals, .NSE, .BE.NSE, etc.)
    # This pattern matches dash followed by Roman numerals OR any dot followed by letters
    df['symbol'] = df['symbol'].str.replace(r'-[IVX]+$|\.\w+(\.\w+)*$', '', regex=True)
    
    # Display cleaned symbols
    print(f"\nSample cleaned symbols:")
    print(df['symbol'].head(10).tolist())
    
    # Check unique symbols before and after cleaning
    print(f"\nUnique symbols after cleaning: {df['symbol'].nunique()}")
    print(f"Unique symbol values: {df['symbol'].unique()}")
    
    # Save the cleaned data to a new file
    # Generate output filename based on input filename
    base_name = input_file.replace('.csv', '')
    output_file = f'{base_name}_symbols_cleaned.csv'
    df.to_csv(output_file, index=False)
    print(f"\nCleaned data saved to: {output_file}")
    
    return df

if __name__ == "__main__":
    # Check if filename was provided as command line argument
    if len(sys.argv) > 1:
        input_filename = sys.argv[1]
        print(f"Using command line argument: {input_filename}")
        
        # Check if output directory was specified
        output_directory = None
        if len(sys.argv) > 2:
            output_directory = sys.argv[2]
            print(f"Output directory: {output_directory}")
        
        result = clean_symbol_names(input_filename, output_directory)
    else:
        # Run the function with interactive input
        result = clean_symbol_names()
    
    # Handle different return types (DataFrame for single CSV, list for ZIP/directory)
    if result is not None:
        if isinstance(result, list):
            # ZIP/Directory processing - result is list of processed files
            if result:
                print(f"\n=== PROCESSING COMPLETE ===")
                print(f"Successfully processed {len(result)} files")
            else:
                print("No files were processed.")
        else:
            # Single CSV file processing - result is DataFrame
            print("\nFirst 5 rows of cleaned data:")
            print(result.head())
    else:
        print("Script failed to process the file.")