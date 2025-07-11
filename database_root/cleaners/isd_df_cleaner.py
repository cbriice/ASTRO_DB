#cleaners coded by Brett, implemented by me
import pandas as pd

def isd_df_clean(isd_df, hertz):

    # written out header to distinguish which should be interpolated and which should be repeated
    isd_interp_col = ['TC_5_Temperature (°C)','TC_6_Temperature (°C)','TC_7_Temperature (°C)','TC_8_Temperature (°C)','TC_9_Temperature (°C)','TC_10_Temperature (°C)',
                    'TC_11_Temperature (°C)','TC_12_Temperature (°C)','TC_13_Temperature (°C)','TC_14_Temperature (°C)','LTHFS_1_HeatFlux (W/m²)','LTHFS_1_Temperature (°C)',
                    'LTHFS_2_HeatFlux (W/m²)','LTHFS_2_Temperature (°C)','LTHFS_3_HeatFlux (W/m²)','LTHFS_3_Temperature (°C)','LTHFS_4_HeatFlux (W/m²)','LTHFS_4_Temperature (°C)',
                    'LTHFS_5_HeatFlux (W/m²)','LTHFS_5_Temperature (°C)','Force_1_Force (lbs.)','Force_2_Force (lbs.)','Force_3_Force (lbs.)','Force_4_Force (lbs.)','Force_5_Force (lbs.)',
                    'HTHFS_1_HeatFlux (W/m²)','HTHFS_1_Top_Temperature (°C)','HTHFS_1_Bottom_Temperature (°C)','HTHFS_1_Average_Temperature (°C)','Total_Force (lbs.)']
    isd_repeat_col = ['S.No.','Date&Time','Time','Start_Button_Voltage (V)']

    # initiallizing counters and variables
    current_second = None
    isd_second_counter={}
    i = -1
    j = 0
    isd_initial_sec = 0
    isd_final_sec = 0
    new_rows = []

    # main for loop that looks at each individual time in df
    for time in isd_df["Time"]:
        i = i+1
        # find the current second
        time_split = time.split(":")
        second = float(time_split[2])
        # grabs the very first initial values
        if int(second) != current_second and i == 0:
            current_second = int(second)
            isd_second_counter = {int(second):0}
            isd_initial_interp_value = isd_df[isd_interp_col].iloc[i]
            isd_initial_sec = second
        # determines whether or not the second has ended or not
        if int(second) != current_second and i != 0:
            # if the second has ended, then it starts the interpolation
            isd_final_interp_value = isd_df[isd_interp_col].iloc[i-1]
            isd_slopes = (isd_final_interp_value - isd_initial_interp_value)/(isd_final_sec - isd_initial_sec)
            t = 0.0
            # while loop for new rows to add
            while t < 1:
                row = {}
                # repeats the initial values at the start of the second for each column that don't need interpolation
                for header in isd_repeat_col:
                    if header == 'Time':
                        row[header] = time_split[0] + ':' + time_split[1] + ':' + str(int(second) + t)
                    else:
                        row[header] = isd_df[header].iloc[i]
                # calculates an equal spacing according to the hertz for each column that need interpolation
                for header in isd_interp_col:
                    #cleaned_header = header.replace("/",".per.")
                    #carson change: get rid of unit labels, makes databasing more streamlined
                    split = header.split('(', 1)
                    new_header = split[0].strip()

                    row[new_header] = round((isd_slopes[header] * t + isd_initial_interp_value[header]),2)  #new_header instead of cleaned_header
                new_rows.append(row)
                t = t + (1/hertz)
            current_second = int(second)
            isd_second_counter = {int(second):1}
            isd_initial_interp_value = isd_df[isd_interp_col].iloc[i]
            isd_initial_sec = second
        else:
            # if the next row is within the same second then the new final values are made
            isd_second_counter[int(second)] += 1
            isd_final_sec = second
    isd_new_df = pd.DataFrame(new_rows)

    # finds where the machine starts
    isd_Start_Voltage = isd_new_df["Start_Button_Voltage (V)"]
    Voltage_initial_value = 0
    isd_start_index = isd_Start_Voltage.ne(Voltage_initial_value).idxmax()
    k = 0
    j = 0
    # creates new columns to the new dataframe
    for i, row in isd_new_df.iterrows():
        if i >= isd_start_index:
            isd_new_df.at[i, "Seconds into Build"] = round(j, 2)
            isd_new_df.at[i, "On-Off"] = 1
            j = j + (1/hertz)
        else:
            isd_new_df.at[i, "Seconds into Build"] = round(k - round(isd_start_index/hertz,0),2)
            isd_new_df.at[i, "On-Off"] = 0
            k = k + (1/hertz)
    cols = list(isd_new_df.columns)
    cols.remove("Seconds into Build")
    cols.insert(3,"Seconds into Build")
    isd_new_df = isd_new_df[cols]

    return isd_new_df
    
#same thing as in md cleaner. rewritten to be vectorized
import numpy as np

def vectorized_isd_df_clean(isd_df: pd.DataFrame, hertz: float) -> pd.DataFrame:
    isd_interp_col = ['TC_5_Temperature (°C)','TC_6_Temperature (°C)','TC_7_Temperature (°C)','TC_8_Temperature (°C)','TC_9_Temperature (°C)',
                      'TC_10_Temperature (°C)','TC_11_Temperature (°C)','TC_12_Temperature (°C)','TC_13_Temperature (°C)','TC_14_Temperature (°C)',
                      'LTHFS_1_HeatFlux (W/m²)','LTHFS_1_Temperature (°C)','LTHFS_2_HeatFlux (W/m²)','LTHFS_2_Temperature (°C)',
                      'LTHFS_3_HeatFlux (W/m²)','LTHFS_3_Temperature (°C)','LTHFS_4_HeatFlux (W/m²)','LTHFS_4_Temperature (°C)',
                      'LTHFS_5_HeatFlux (W/m²)','LTHFS_5_Temperature (°C)','Force_1_Force (lbs.)','Force_2_Force (lbs.)',
                      'Force_3_Force (lbs.)','Force_4_Force (lbs.)','Force_5_Force (lbs.)','HTHFS_1_HeatFlux (W/m²)',
                      'HTHFS_1_Top_Temperature (°C)','HTHFS_1_Bottom_Temperature (°C)','HTHFS_1_Average_Temperature (°C)','Total_Force (lbs.)']
    isd_repeat_col = ['S.No.','Date&Time','Time','Start_Button_Voltage (V)']

    time_split = isd_df["Time"].str.split(":", expand=True).astype(float)
    time_sec = time_split[0]*3600 + time_split[1]*60 + time_split[2]

    full_seconds = time_sec.astype(int)
    isd_df["second"] = full_seconds
    grouped = isd_df.groupby("second")

    rows = []

    for sec, group in grouped:
        if len(group) < 2:
            continue

        start = group.iloc[0]
        end = group.iloc[-1]
        dt = time_sec.loc[end.name] - time_sec.loc[start.name]
        steps = max(1, int(round(hertz * dt)))
        t = np.linspace(0, dt, steps, endpoint=False)

        interp_array = (start[isd_interp_col].values[None, :] + 
                        ((end[isd_interp_col] - start[isd_interp_col]) / dt).values[None, :] * t[:, None])
        col_names_cleaned = [c.split('(')[0].strip() for c in isd_interp_col]
        interp_df = pd.DataFrame(interp_array, columns=col_names_cleaned)

        repeat_vals = {col: [start[col]] * steps for col in isd_repeat_col}
        block = pd.concat([pd.DataFrame(repeat_vals), interp_df], axis=1)
        block["Time (Seconds)"] = start["Time"]
        rows.append(block)

    isd_new_df = pd.concat(rows, ignore_index=True)
    #force correct datatypes to avoid object bullshit
    numeric_cols = [col for col in isd_new_df.columns if col not in isd_repeat_col + ['Time (Seconds)']]
    for col in numeric_cols:
        isd_new_df[col] = pd.to_numeric(isd_new_df[col], errors='coerce')

    for col in isd_repeat_col + ['Time (Seconds)']:
        isd_new_df[col] = isd_new_df[col].astype(str)

    # Determine when machine starts
    start_voltage = isd_new_df["Start_Button_Voltage (V)"]
    start_index = start_voltage.ne(0).idxmax()
    total_rows = len(isd_new_df)

    seconds_into_build = np.arange(total_rows) / hertz
    seconds_into_build = seconds_into_build - seconds_into_build[start_index]
    isd_new_df["Seconds into Build"] = seconds_into_build.round(2)

    isd_new_df["On-Off"] = 0
    isd_new_df.loc[start_index:, "On-Off"] = 1

    cols = list(isd_new_df.columns)
    cols.remove("Seconds into Build")
    cols.insert(3, "Seconds into Build")
    isd_new_df = isd_new_df[cols]

    return isd_new_df
