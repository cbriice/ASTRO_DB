import pandas as pd


def mcd_df_clean(mcd_df, hertz):
    #clear empty columns
    mcd_df = mcd_df.loc[:, ~mcd_df.isna().all()]

    mcd_repeat_col = ['Frame','Time (Seconds)']

    # Get all column names
    all_cols = mcd_df.columns.tolist()
    # Get the index of the last repeat column
    last_repeat_index = all_cols.index(mcd_repeat_col[-1])
    # Get all columns after the last repeat column
    mcd_interp_col = all_cols[last_repeat_index + 1:]


    # initiallizing counters and variables
    current_second = None
    mcd_second_counter={}
    i = -1
    mcd_initial_sec = 0
    mcd_final_sec = 0
    new_rows = []

     # main for loop that looks at each individual time in df
    for time in mcd_df["Time (Seconds)"]:

        i = i+1
        # find the current second
        second = time
        # grabs the very first initial values
        if int(second) != current_second and i == 0:
            current_second = int(second)
            mcd_second_counter = {int(second):0}
            mcd_initial_interp_value = mcd_df[mcd_interp_col].iloc[i]
            mcd_initial_sec = second
        # determines whether or not the second has ended or not
        if int(second) != current_second and i != 0:
            # if the second has ended, then it starts the interpolation
            mcd_final_interp_value = mcd_df[mcd_interp_col].iloc[i-1]

            mcd_slopes = (mcd_final_interp_value - mcd_initial_interp_value)/(mcd_final_sec - mcd_initial_sec)
            t = 0.0
            # while loop for new rows to add
            while t < 1:
                row = {}
                # repeats the initial values at the start of the second for each column that don't need interpolation
                for header in mcd_repeat_col:
                    if header == 'Time (Seconds)':
                        row[header] = str(int(second)) + str(t)
                    else:
                        row[header] = mcd_df[header].iloc[i]
                # calculates an equal spacing according to the hertz for each column that need interpolation
                for header in mcd_interp_col:
                    row[header] = round((mcd_slopes[header] * t + mcd_initial_interp_value[header]),2)

                new_rows.append(row)
                t = t + round((1/hertz), 3)

            current_second = int(second)
            mcd_second_counter = {int(second):1}

            mcd_initial_interp_value = mcd_df[mcd_interp_col].iloc[i]
            mcd_initial_sec = second

        else:
            # if the next row is within the same second then the new final values are made
            mcd_second_counter[int(second)] += 1
            mcd_final_sec = second
    mcd_new_df = pd.DataFrame(new_rows)


    mcd_start_index = 0
    j = 0
    k = 0
    # creates new columns to the new dataframe
    for i, row in mcd_new_df.iterrows():
        if i >= mcd_start_index:
            mcd_new_df.at[i, "Seconds into Build"] = round(j, 1)
            mcd_new_df.at[i, "On-Off"] = 1
            j = j + round((1/hertz), 3)
        else:
            mcd_new_df.at[i, "Seconds into Build"] = round(k - round(mcd_start_index/hertz,0),1)
            mcd_new_df.at[i, "On-Off"] = 0
            k = k + round((1/hertz), 3)

    cols = list(mcd_new_df.columns)
    cols.remove("Seconds into Build")
    cols.insert(2,"Seconds into Build")
    mcd_new_df = mcd_new_df[cols]

    return mcd_new_df


import numpy as np

#put the above function into chat gpt and told it to go nuts fixing it, and it seems to have worked pretty well so ima leave it and not take credit lol
#i did have to fix a bunch of shit myself though tbf
def gpt_clean(mcd_df, hertz):
    try:
        low_qual = False
        required_cols = ['Frame', 'Time (Seconds)']
        missing = [col for col in required_cols if col not in mcd_df.columns]
        if missing:
            raise ValueError(f"Missing required columns: {missing}")
        
        mcd_df = mcd_df.sort_values("Time (Seconds)").drop_duplicates(subset="Time (Seconds)").reset_index(drop=True)
        # Drop fully empty columns
        mcd_df = mcd_df.loc[:, ~mcd_df.isna().all()]

        mcd_repeat_col = ['Frame', 'Time (Seconds)']

        # Determine interpolation columns
        all_cols = mcd_df.columns.tolist()
        last_repeat_index = all_cols.index(mcd_repeat_col[-1])
        mcd_interp_col = all_cols[last_repeat_index + 1:]

        # Precompute values
        time_col = mcd_df["Time (Seconds)"].to_numpy()
        interp_data = mcd_df[mcd_interp_col].to_numpy()
        repeat_data = mcd_df[mcd_repeat_col].to_numpy()

        # Output collection
        new_rows = []
        i = 0

        while i < len(time_col):
            if i == 0:
                i += 1
                continue

            t_start = time_col[i - 1]
            t_end = time_col[i]
            dt = t_end - t_start

            if not np.isfinite(dt) or dt <= 0:
                i += 1
                continue
            
            #warning for low quality interpolation at low Hz where step values are forced
            raw_steps = hertz * dt
            steps = max(1, int(round(hertz * dt)))
            if steps == 1 and raw_steps < 0.5:
                low_qual = True
            if steps < 1:
                i += 1
                continue

            # Determine which columns are non-NaN across both rows
            valid_mask = np.isfinite(interp_data[i - 1]) & np.isfinite(interp_data[i])
            if not np.any(valid_mask):
                i += 1
                continue

            slopes = np.zeros_like(interp_data[i - 1])
            slopes[valid_mask] = (
                (interp_data[i] - interp_data[i - 1])[valid_mask] / dt
            )

            t_values = np.linspace(0, dt, steps, endpoint=False)
            for t_offset in t_values:
                row = {}
                for j, col in enumerate(mcd_interp_col):
                    if valid_mask[j]:
                        row[col] = round(interp_data[i - 1][j] + slopes[j] * t_offset, 2)
                # repeat cols (no interpolation, just assign current row)
                row["Frame"] = repeat_data[i][0]
                row["Time (Seconds)"] = round(t_start + t_offset, 6)
                new_rows.append(row)

            i += 1
        #debug
        if not new_rows:
            raise ValueError('No valid rows generated during interpolation - check time column or input df')
        # Construct final dataframe
        mcd_new_df = pd.DataFrame(new_rows)

        # Add time-from-start and on/off marker
        mcd_new_df["Seconds into Build"] = np.round(
            mcd_new_df["Time (Seconds)"] - mcd_new_df["Time (Seconds)"].iloc[0], 3
        )
        mcd_new_df["On-Off"] = 1

        # Reorder columns
        cols = list(mcd_new_df.columns)
        cols.remove("Seconds into Build")
        cols.insert(2, "Seconds into Build")
        mcd_new_df = mcd_new_df[cols]

        return mcd_new_df, low_qual
    
    except Exception as e:
        import traceback
        print(f'[ERROR] gpt_clean(): {e}')
        traceback.print_exc()
        raise