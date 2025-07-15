import pandas as pd

def merge_dataframes(isd, mcd, md):
    if md is None:
        print('No machine file found')
        return None
    
    if isd is not None and md is not None and mcd is None:
        print('Reconstructing build data without motion capture data')
        return isd.merge(md, on="Seconds into Build", how="outer", suffixes=("_isd", "_md"))
    elif mcd is not None and md is not None and isd is None:
        print('Reconstructing build data without in-situ data')
        return mcd.merge(md, on="Seconds into Build", how="outer", suffixes=("_isd", "_md"))
    

def merge_isd_mcd_md_df(isd_new_df, mcd_new_df, md_new_df):
    isd_new_df = isd_new_df.groupby("Seconds into Build").mean(numeric_only=True).reset_index() if isd_new_df is not None else None
    mcd_new_df = mcd_new_df.groupby("Seconds into Build").mean(numeric_only=True).reset_index() if mcd_new_df is not None else None
    md_new_df = md_new_df.groupby("Seconds into Build").mean(numeric_only=True).reset_index()   if md_new_df is not None else None

    # merge dataframes
    merged_df = merge_dataframes(isd_new_df, mcd_new_df, md_new_df)

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