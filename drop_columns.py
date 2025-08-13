import pandas as pd
import sys
import zipfile
import os
from pathlib import Path

def process_zip_file(zip_path, columns_to_drop=None, output_dir=None):
    """
    Extract and process all CSV files in a zip file
    
    Args:
        zip_path (str): Path to the zip file
        columns_to_drop (list): List of column names to drop
        output_dir (str): Directory to save processed files
    """
    if columns_to_drop is None:
        columns_to_drop = ['volume', 'oi', 'coi']
    
    if output_dir is None:
        output_dir = f"{Path(zip_path).stem}_processed"
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    processed_files = []
    
    print(f"Processing zip file: {zip_path}")
    print(f"Output directory: {output_dir}")
    print(f"Columns to drop: {columns_to_drop}")
    
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
                    print(f"Original columns: {list(df.columns)}")
                    
                    # Check which columns exist before dropping
                    existing_columns = [col for col in columns_to_drop if col in df.columns]
                    missing_columns = [col for col in columns_to_drop if col not in df.columns]
                    
                    if missing_columns:
                        print(f"Warning: These columns don't exist: {missing_columns}")
                    
                    if existing_columns:
                        print(f"Dropping columns: {existing_columns}")
                        df_cleaned = df.drop(columns=existing_columns)
                        
                        print(f"New shape: {df_cleaned.shape}")
                        print(f"Remaining columns: {list(df_cleaned.columns)}")
                        
                        # Save processed file
                        output_filename = f"{Path(csv_file).stem}_columns_dropped.csv"
                        output_path = os.path.join(output_dir, output_filename)
                        df_cleaned.to_csv(output_path, index=False)
                        
                        processed_files.append(output_path)
                        print(f"Saved: {output_path}")
                    else:
                        print(f"No specified columns found in {csv_file}, skipping...")
                
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

def drop_columns_from_csv(input_file=None, columns_to_drop=None):
    """
    Drop specified columns from CSV file or process all CSV files in a zip file
    
    Args:
        input_file (str): Path to the input CSV/ZIP file. If None, will prompt for input.
        columns_to_drop (list): List of column names to drop. If None, will use default ['volume', 'oi', 'coi']
    """
    # Get input file name
    if input_file is None:
        input_file = input("Enter the file name (CSV or ZIP, e.g., 'data.csv' or 'data.zip'): ").strip()
    
    # Set default columns to drop if not specified
    if columns_to_drop is None:
        columns_to_drop = ['volume', 'oi', 'coi']
        print(f"Using default columns to drop: {columns_to_drop}")
    
    # Check if input is a zip file
    if input_file.lower().endswith('.zip'):
        print("Detected ZIP file - processing all CSV files inside...")
        return process_zip_file(input_file, columns_to_drop)
    
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
    
    # Display original shape and columns
    print(f"Original shape: {df.shape}")
    print(f"Original columns: {list(df.columns)}")
    
    # Check which columns exist before dropping
    existing_columns = [col for col in columns_to_drop if col in df.columns]
    missing_columns = [col for col in columns_to_drop if col not in df.columns]
    
    if missing_columns:
        print(f"Warning: These columns don't exist in the file: {missing_columns}")
    
    if not existing_columns:
        print("Error: None of the specified columns exist in the file!")
        return None
    
    print(f"Dropping columns: {existing_columns}")
    
    # Drop the existing columns
    df_cleaned = df.drop(columns=existing_columns)
    
    # Display new shape and columns
    print(f"New shape: {df_cleaned.shape}")
    print(f"Remaining columns: {list(df_cleaned.columns)}")
    
    # Save the cleaned data to a new file
    # Generate output filename based on input filename
    base_name = input_file.replace('.csv', '')
    output_file = f'{base_name}_columns_dropped.csv'
    df_cleaned.to_csv(output_file, index=False)
    print(f"Cleaned data saved to: {output_file}")
    
    return df_cleaned

if __name__ == "__main__":
    # Check if filename was provided as command line argument
    if len(sys.argv) > 1:
        input_filename = sys.argv[1]
        print(f"Using command line argument: {input_filename}")
        
        # Check if columns were specified as additional arguments
        if len(sys.argv) > 2:
            columns_list = sys.argv[2:]
            print(f"Columns to drop: {columns_list}")
            result = drop_columns_from_csv(input_filename, columns_list)
        else:
            # Use default columns
            result = drop_columns_from_csv(input_filename)
    else:
        # Run the function with interactive input
        result = drop_columns_from_csv()
    
    # Handle different return types (DataFrame for single CSV, list for ZIP)
    if result is not None:
        if isinstance(result, list):
            # ZIP file processing - result is list of processed files
            if result:
                print(f"\n=== ZIP PROCESSING COMPLETE ===")
                print(f"Successfully processed {len(result)} files from ZIP")
            else:
                print("No files were processed from the ZIP file.")
        else:
            # Single CSV file processing - result is DataFrame
            print("\nFirst 5 rows of cleaned data:")
            print(result.head())
    else:
        print("Script failed to process the file.")