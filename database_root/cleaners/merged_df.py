import pandas as pd

def merge_isd_mcd_md_df(isd_new_df, mcd_new_df, md_new_df):

    isd_new_df = isd_new_df.groupby("Seconds into Build").mean(numeric_only=True).reset_index()
    mcd_new_df = mcd_new_df.groupby("Seconds into Build").mean(numeric_only=True).reset_index()
    md_new_df = md_new_df.groupby("Seconds into Build").mean(numeric_only=True).reset_index()

    # merge dataframes
    merged_df = isd_new_df.merge(
        md_new_df, on="Seconds into Build", how="outer", suffixes=("_isd", "_md"))
    merged_df = merged_df.merge(
        mcd_new_df, on="Seconds into Build", how="outer", suffixes=("", "_mcd"))

    # Sort and reset index
    merged_df = merged_df.sort_values(by="Seconds into Build").reset_index(drop=True)

    for i, row in merged_df.iterrows():
        if merged_df["Seconds into Build"][i] >= 0:
            merged_df.at[i, "Final_On-Off"] = 1
        else:
            merged_df.at[i, "Final_On-Off"] = 0

    cols = list(merged_df.columns)
    cols.remove("Final_On-Off")
    cols.insert(1,"Final_On-Off")
    merged_df = merged_df[cols]

    return merged_df