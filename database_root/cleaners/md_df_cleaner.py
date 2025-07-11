import pandas as pd

def md_df_clean(md_df, hertz):

    # written out header to distinguish which should be interpolated and which should be repeated
    md_interp_col = ['SpinVel','SpinTrq','SpinPwr','SpinSP','FeedVel','FeedPos','FeedTrq','FRO','PathVel','XPos','XVel','XTrq','YPos','YVel','YTrq',
                    'ZPos','ZVel','ZTrq','Low','High','Ktype1','Ktype2','Ktype3','Ktype4','O2','ToolTemp','Zscale']
    md_repeat_col = ['Date','Time','Gcode']

    # initiallizing counters and variables
    current_second = None
    md_second_counter={}
    i = -1
    md_initial_sec = 0
    md_final_sec = 0
    new_rows = []

    # main for loop that looks at each individual time in df
    for time in md_df["Time"]:
        i = i+1
        # find the current second
        time_split = time.split(":")
        second = float(time_split[2])
        # grabs the very first initial values
        if int(second) != current_second and i == 0:
            current_second = int(second)
            md_second_counter = {int(second):0}
            md_initial_interp_value = md_df[md_interp_col].iloc[i]
            md_initial_sec = second
        # determines whether or not the second has ended or not
        if int(second) != current_second and i != 0:
            # if the second has ended, then it starts the interpolation
            md_final_interp_value = md_df[md_interp_col].iloc[i-1]
            md_slopes = (md_final_interp_value - md_initial_interp_value)/(md_final_sec - md_initial_sec)
            t = 0.0
            # while loop for new rows to add
            while t < 1:
                row = {}
                # repeats the initial values at the start of the second for each column that don't need interpolation
                for header in md_repeat_col:
                    if header == 'Time':
                        row[header] = time_split[0] + ':' + time_split[1] + ':' + str(int(second) + t)
                    else:
                        row[header] = md_df[header].iloc[i]
                # calculates an equal spacing according to the hertz for each column that need interpolation
                for header in md_interp_col:
                    row[header] = round((md_slopes[header] * t + md_initial_interp_value[header]),2)
                new_rows.append(row)
                t = t + (1/hertz)
            current_second = int(second)
            md_second_counter = {int(second):1}

            md_initial_interp_value = md_df[md_interp_col].iloc[i]
            md_initial_sec = second
        else:
            # if the next row is within the same second then the new final values are made
            md_second_counter[int(second)] += 1
            md_final_sec = second
    md_new_df = pd.DataFrame(new_rows)

    # finds where the machine starts
    md_Gcode = md_new_df["Gcode"]
    Gcode_initial_value = md_Gcode[0]
    md_start_index = md_Gcode.ne(Gcode_initial_value).idxmax()
    k = 0
    j = 0
    # creates new columns to the new dataframe
    for i, row in md_new_df.iterrows():
        if i >= md_start_index:
            md_new_df.at[i, "Seconds into Build"] = round(j, 2)
            md_new_df.at[i, "On-Off"] = 1
            j = j + (1/hertz)
        else:
            md_new_df.at[i, "Seconds into Build"] = round(k - round(md_start_index/hertz,0),2)
            md_new_df.at[i, "On-Off"] = 0
            k = k + (1/hertz)
    cols = list(md_new_df.columns)
    cols.remove("Seconds into Build")
    cols.insert(2,"Seconds into Build")
    md_new_df = md_new_df[cols]

    return md_new_df

#Brett's code is way too slow because it's not vectorized. I don't have time to rewrite his code so this is a gpt generated block of code mimicking his
import numpy as np

def vectorized_md_df_clean(md_df: pd.DataFrame, hertz: float) -> pd.DataFrame:
    md_interp_col = ['SpinVel','SpinTrq','SpinPwr','SpinSP','FeedVel','FeedPos','FeedTrq','FRO','PathVel','XPos','XVel','XTrq',
                     'YPos','YVel','YTrq','ZPos','ZVel','ZTrq','Low','High','Ktype1','Ktype2','Ktype3','Ktype4','O2','ToolTemp','Zscale']
    md_repeat_col = ['Date','Time','Gcode']

    time_split = md_df["Time"].str.split(":", expand=True).astype(float)
    time_sec = time_split[0]*3600 + time_split[1]*60 + time_split[2]

    full_seconds = time_sec.astype(int)
    md_df["second"] = full_seconds
    grouped = md_df.groupby("second")

    rows = []

    for sec, group in grouped:
        if len(group) < 2:
            continue

        start = group.iloc[0]
        end = group.iloc[-1]
        dt = time_sec.loc[end.name] - time_sec.loc[start.name]
        steps = max(1, int(round(hertz * dt)))
        t = np.linspace(0, dt, steps, endpoint=False)

        interp_array = (start[md_interp_col].values[None, :] + 
                        ((end[md_interp_col] - start[md_interp_col]) / dt).values[None, :] * t[:, None])
        interp_df = pd.DataFrame(interp_array, columns=md_interp_col)

        repeat_vals = {col: [start[col]] * steps for col in md_repeat_col}
        block = pd.concat([pd.DataFrame(repeat_vals), interp_df], axis=1)
        block["Time (Seconds)"] = start["Time"]
        rows.append(block)

    md_new_df = pd.concat(rows, ignore_index=True)
    #force correct datatypes to avoid object bullshit
    numeric_cols = [col for col in md_new_df.columns if col not in md_repeat_col + ['Time (Seconds)']]
    for col in numeric_cols:
        md_new_df[col] = pd.to_numeric(md_new_df[col], errors='coerce')

    for col in md_repeat_col + ['Time (Seconds)']:
        md_new_df[col] = md_new_df[col].astype(str)

    # Determine when the build starts
    gcode_initial = md_new_df["Gcode"].iloc[0]
    start_index = md_new_df["Gcode"].ne(gcode_initial).idxmax()
    total_rows = len(md_new_df)

    seconds_into_build = np.arange(total_rows) / hertz
    seconds_into_build = seconds_into_build - seconds_into_build[start_index]
    md_new_df["Seconds into Build"] = seconds_into_build.round(2)

    md_new_df["On-Off"] = 0
    md_new_df.loc[start_index:, "On-Off"] = 1

    cols = list(md_new_df.columns)
    cols.remove("Seconds into Build")
    cols.insert(2, "Seconds into Build")
    md_new_df = md_new_df[cols]
    
    print(md_new_df.dtypes[md_new_df.dtypes == 'object'])

    return md_new_df