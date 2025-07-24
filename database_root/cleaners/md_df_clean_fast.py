import pandas as pd
import numpy as np

def vectorized_md_df_clean(md_df: pd.DataFrame, hertz: float) -> pd.DataFrame:

    # Calculate total time of recording in seconds
    time_start = pd.Timestamp(f"{md_df['Date'].iloc[0]} {md_df['Time'].iloc[0]}")
    time_end = pd.Timestamp(f"{md_df['Date'].iloc[-1]} {md_df['Time'].iloc[-1]}")
    total_time = pd.Timedelta(time_end - time_start).total_seconds()

    # Calculate number of samples recorded
    num_samples = len(md_df)

    orig_secs = np.linspace(0, total_time, num_samples)     # Time from start based on original sample rate
    new_secs = np.arange(0, total_time, (1/hertz))          # Time from start for desired sample rate

    resample = pd.DataFrame()                  # Dataframe to store resampled data
    resample['Seconds into Build'] = new_secs     # Create column for seconds from start

    # Copy columns from original data and remove date/time columns as they cannot be interpolated
    columns = md_df.columns.tolist()
    columns.remove('Date')
    columns.remove('Time')

    resample['DateTime'] = time_start + pd.to_timedelta(new_secs * 10**9)  # Add new datetime column with updated sample frequency
    resample['DateTime'] = str(resample['DateTime'])

    # Interpolate each column to the new sample frequency
    for col in columns:
        resample[col] = np.interp(new_secs, orig_secs, md_df[col])

    # Round entire dataframe to 3 decimal places
    resample = resample.round(3)

    return resample