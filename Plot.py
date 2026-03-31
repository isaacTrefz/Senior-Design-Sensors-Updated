import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
import os

def parse_time(t_str):
    """
    Parses time string (HH:MM:SS.f or MM:SS.f) to total seconds.
    """
    try:
        if not isinstance(t_str, str):
            return np.nan
        parts = t_str.split(':')
        if len(parts) == 3:  # HH:MM:SS.f
            hours = float(parts[0])
            minutes = float(parts[1])
            seconds = float(parts[2])
            return hours * 3600 + minutes * 60 + seconds
        elif len(parts) == 2:  # MM:SS.f
            minutes = float(parts[0])
            seconds = float(parts[1])
            return minutes * 60 + seconds
        return np.nan
    except (ValueError, TypeError):
        return np.nan

def process_original_task():
    """
    Original functionality: Process single_scale_data.csv using Book 21(Sheet1).csv
    """
    print("--- Processing Original Task (Single Scale) ---")
    
    # Path handling for robustness
    calib_path = './CalibrationData/Book 21(Sheet1).csv'
    if not os.path.exists(calib_path):
        # Fallback to current directory if file not in folder
        if os.path.exists('Book 21(Sheet1).csv'):
            calib_path = 'Book 21(Sheet1).csv'
        else:
            print(f"Warning: Original calibration file '{calib_path}' not found. Skipping original task.")
            return

    try:
        df_book = pd.read_csv(calib_path)
    except Exception as e:
        print(f"Error reading {calib_path}: {e}")
        return

    # 'Reading' is the independent variable (x), 'Weight' is dependent (y)
    X = df_book[['Reading']].values
    y = df_book['Weight'].values

    # Fit Linear Regression Model to get the Slope
    reg = LinearRegression().fit(X, y)
    slope = reg.coef_[0]
    
    print(f"Original Mapping Model Established:")
    print(f"Calibration Slope: {slope:.8f}")
    print(f"R^2 Score: {reg.score(X, y):.4f}")

    # Process single_scale_data.csv
    data_file = 'single_scale_data.csv'
    if not os.path.exists(data_file):
        print(f"Warning: '{data_file}' not found. Skipping original task.")
        return

    try:
        df_single = pd.read_csv(data_file)
    except Exception as e:
        print(f"Error reading {data_file}: {e}")
        return

    # Clean and Process
    df_single.columns = df_single.columns.str.strip()
    df_single = df_single.dropna(subset=['Weight'])
    df_single['Reading_Raw'] = pd.to_numeric(df_single['Weight'], errors='coerce')
    df_single = df_single.dropna(subset=['Reading_Raw'])

    # Outlier Filtering (from original script logic)
    df_single = df_single[df_single['Reading_Raw'] < 0].copy()

    # Relative Tare
    if not df_single.empty:
        tare_value = df_single['Reading_Raw'].iloc[0]
        df_single['Mapped_Force'] = (df_single['Reading_Raw'] - tare_value) * slope
    else:
        print("Error: No valid data points found after filtering.")
        return

    # Time Parsing
    df_single['Seconds'] = df_single['Time'].apply(parse_time)
    df_single = df_single.dropna(subset=['Seconds'])
    
    if not df_single.empty:
        df_single['Relative_Seconds'] = df_single['Seconds'] - df_single['Seconds'].min()

    # Plotting
    if df_single.empty:
        print("Error: No data points found to plot.")
        return

    plt.figure(figsize=(12, 6))
    plt.plot(df_single['Relative_Seconds'], df_single['Mapped_Force'], label='Relative Force', color='blue')
    plt.title('Closed Connection Forces')
    plt.xlabel('Time (Seconds from start)')
    plt.ylabel('Force (Pounds)')
    plt.grid(True, which='both', linestyle='--', linewidth=0.5)
    plt.legend()
    plt.tight_layout()
    plt.savefig('Closed_Connection.png')
    print("Plot saved as 'Closed_Connection.png'")
    plt.show()

def process_new_task():
    """
    New functionality: Process multi_scale_data.csv using Book 21(Sheet2).csv
    """
    print("--- Processing New Task (Multi Scale) ---")
    
    calib_file = './CalibrationData/Book 21(Sheet2).csv'
    if not os.path.exists(calib_file):
        print(f"Error: '{calib_file}' not found. Skipping new task.")
        return

    try:
        df_book = pd.read_csv(calib_file)
    except Exception as e:
        print(f"Error reading {calib_file}: {e}")
        return
        
    # Check columns: Expected 'Force' and 'Reading'
    if 'Force' not in df_book.columns or 'Reading' not in df_book.columns:
        print("Error: Book 21(Sheet2).csv must contain 'Force' and 'Reading' columns.")
        return

    X = df_book[['Reading']].values
    y = df_book['Force'].values 

    # Establish Mapping
    reg = LinearRegression().fit(X, y)
    slope = reg.coef_[0]
    
    print(f"New Mapping Model Established:")
    print(f"Calibration Slope: {slope:.8f}")
    print(f"R^2 Score: {reg.score(X, y):.4f}")

    # Process multi_scale_data.csv
    data_file = 'multi_scale_data.csv'
    if not os.path.exists(data_file):
        print(f"Error: '{data_file}' not found. Skipping new task.")
        return

    try:
        # Header is on the 5th line (index 4) based on file inspection
        df_multi = pd.read_csv(data_file, header=4)
    except Exception as e:
        print(f"Error reading {data_file}: {e}")
        return

    df_multi.columns = df_multi.columns.str.strip()
    
    # Ensure columns exist
    if 'Scale1' not in df_multi.columns or 'Time' not in df_multi.columns:
        print("Error: 'multi_scale_data.csv' must contain 'Scale1' and 'Time' columns.")
        return

    # Convert Scale1 to numeric
    df_multi['Scale1_Raw'] = pd.to_numeric(df_multi['Scale1'], errors='coerce')
    df_multi = df_multi.dropna(subset=['Scale1_Raw'])

    # Relative Tare (Taring to the start of the session)
    if not df_multi.empty:
        tare_value = df_multi['Scale1_Raw'].iloc[0]
        df_multi['Mapped_Force'] = (df_multi['Scale1_Raw'] - tare_value) * slope
    else:
        print("Error: No valid data points found in multi_scale_data.csv.")
        return

    # Time Parsing
    df_multi['Seconds'] = df_multi['Time'].apply(parse_time)
    df_multi = df_multi.dropna(subset=['Seconds'])
    
    if not df_multi.empty:
        df_multi['Relative_Seconds'] = df_multi['Seconds'] - df_multi['Seconds'].min()

    # Plotting
    if df_multi.empty:
        print("Error: No data points found to plot for Multi Scale.")
        return

    plt.figure(figsize=(12, 6))
    plt.plot(df_multi['Relative_Seconds'], df_multi['Mapped_Force'], label='Scale1 Force', color='green')
    plt.title('Open Connection Forces')
    plt.xlabel('Time (Seconds from start)')
    plt.ylabel('Force (Pounds)')
    plt.grid(True, which='both', linestyle='--', linewidth=0.5)
    plt.legend()
    plt.tight_layout()
    plt.savefig('Open_Connection.png')
    print("Plot saved as 'Open_Connection.png'")
    plt.show()

    # --- New Plots ---
    
    # Check for Acceleration columns
    accel_cols = ['AccelX', 'AccelY', 'AccelZ']
    missing_cols = [col for col in accel_cols if col not in df_multi.columns]
    if missing_cols:
        print(f"Error: Missing acceleration columns {missing_cols}. Cannot plot UpForce and HorizontalForce.")
        return

    # Convert to numeric
    for col in accel_cols:
        df_multi[col] = pd.to_numeric(df_multi[col], errors='coerce')
    
    # Drop rows with NaN in Accel
    df_multi = df_multi.dropna(subset=accel_cols)
    
    # Calculate Magnitude of Acceleration Vector
    accel_mag = np.sqrt(df_multi['AccelX']**2 + df_multi['AccelY']**2 + df_multi['AccelZ']**2)
    
    # Calculate Unit Vector X component (since vector is [scale1, 0, 0])
    # unit_accel_x = AccelX / Magnitude
    # Handle division by zero
    unit_accel_x = df_multi['AccelX'] / accel_mag.replace(0, np.nan)
    
    # Calculate upForce (Dot Product)
    # upForce = scale1 * unit_accel_x
    df_multi['upForce'] = df_multi['Mapped_Force'] * unit_accel_x
    
    # Calculate Horizontal Force
    # Formula: sqrt(scale1^2 - upForce^2)
    # Note: User mentioned sqrt(M^2 - scale1^2) where M is vertical component, 
    # but mathematically for a component M of vector Scale1, scale1 >= M.
    # So we use sqrt(scale1^2 - M^2).
    
    # Use abs() to handle potential floating point errors resulting in slightly negative numbers close to zero
    df_multi['horizontalForce'] = np.sqrt((df_multi['Mapped_Force']**2 - df_multi['upForce']**2).abs())
    
    # Plot upForce
    plt.figure(figsize=(12, 6))
    plt.plot(df_multi['Relative_Seconds'], df_multi['upForce'], label='Up Force (Vertical Component)', color='red')
    plt.title('Up Force (Vertical Component)')
    plt.xlabel('Time (Seconds from start)')
    plt.ylabel('Force (Pounds)')
    plt.grid(True, which='both', linestyle='--', linewidth=0.5)
    plt.legend()
    plt.tight_layout()
    plt.savefig('Up_Force.png')
    print("Plot saved as 'Up_Force.png'")
    plt.show()
    
    # Plot Horizontal Force
    plt.figure(figsize=(12, 6))
    plt.plot(df_multi['Relative_Seconds'], df_multi['horizontalForce'], label='Horizontal Force', color='purple')
    plt.title('Horizontal Force')
    plt.xlabel('Time (Seconds from start)')
    plt.ylabel('Force (Pounds)')
    plt.grid(True, which='both', linestyle='--', linewidth=0.5)
    plt.legend()
    plt.tight_layout()
    plt.savefig('Horizontal_Force.png')
    print("Plot saved as 'Horizontal_Force.png'")
    plt.show()

def main():
    # Attempt Original Task
    process_original_task()
    print("\n" + "="*40 + "\n")
    # Attempt New Task
    process_new_task()

if __name__ == "__main__":
    main()