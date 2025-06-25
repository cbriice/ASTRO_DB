import h5rdmtoolbox as h5tbx
from utils.helpers import get_all_att_keys

MASTER_FILE = 'master2.h5'

keys = get_all_att_keys()
print(keys)

#debug ---------------------------------------------------------
def collect_visititems(f):
    results = []
    def visitor(name, obj):
        results.append((name, obj))
    f.visititems(visitor)  # returns None, just fills results
    return results

def to_native_float(val):
    # Handle numpy types, scalars, etc.
    if isinstance(val, (float, int)):
        return float(val)
    elif isinstance(val, np.generic):
        return float(val.item())
    elif isinstance(val, np.ndarray) and val.size == 1:
        return float(val[0])
    elif isinstance(val, str):
        return float(val.strip())
    else:
        raise ValueError(f"Unrecognized type: {type(val)}")

def brute_force_att_search(f, att, lowerbound):
    print('running debug pt 2')
    results = []
    for name, obj in collect_visititems(f):
        if att in obj.attrs:
            raw_val = obj.attrs[att]
            print(f"TYPE DEBUG: {obj.name} → {raw_val} ({type(raw_val)})")
            if isinstance(raw_val, np.ndarray):
                print(f"Array shape: {raw_val.shape}, dtype: {raw_val.dtype}, value: {raw_val}")
            elif isinstance(raw_val, np.generic):
                print(f"Numpy scalar value: {raw_val}, type: {type(raw_val)}")
            try:
                val = to_native_float(raw_val)
                if val >= lowerbound:
                    print(f"HIT: {obj.name} → {val}")
                    results.append(obj)
            except Exception as e:
                print(f"ERR: {obj.name} → {val} (not float?)")
    return results

test = brute_force_att_search(master, att, lowerbound)
print(test)

#end debug ----------------------------------------------------------