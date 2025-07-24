import numpy as np
import pandas as pd

def isd_df_clean(isd_df, hertz):

    time_start = pd.Timestamp(isd_df['Date&Time'].iloc[0])
    time_end = pd.Timestamp(isd_df['Date&Time'].iloc[-1])
    total_time = pd.Timedelta(time_end - time_start).total_seconds()

    num_samples = len(isd_df)

    orig_secs = np.linspace(0, total_time, num_samples)     # Time from start based on original sample rate
    new_secs = np.arange(0, total_time, (1/hertz))       # Time from start for desired sample rate

    resample = pd.DataFrame()                  # Dataframe to store resampled data

    # Copy columns from original data and remove date/time columns as they cannot be interpolated
    columns = isd_df.columns.tolist()
    columns.remove('Date&Time')
    columns.remove('Time')
    columns.remove('S.No.')

    resample['Seconds into Build'] = new_secs      # Create time from start column based on desired sample rate

    # Interpolate each column to the new sample frequency
    for col in columns:
        resample[col] = np.interp(new_secs, orig_secs, isd_df[col])

    resample['DateTime'] = time_start + pd.to_timedelta(new_secs * 10**9)  # Add new datetime column with updated sample frequency
    resample['DateTime'] = str(resample['DateTime'])

    # Align time from start column with machine data start
    start_button_index = resample['Start_Button_Voltage (V)'].ne(0).idxmax()
    resample['Seconds into Build'] = resample['Seconds into Build'] - (start_button_index / hertz)

    # Round entire dataframe to 3 decimal places
    resample = resample.round(3)

    return resample