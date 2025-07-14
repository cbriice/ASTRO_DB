#constants. idk what else you expected

MASTER_FILE = 'master2.h5'

MACHINE_FILE_SAMPLE_DEFAULT = 20
ISD_FILE_SAMPLE_DEFAULT = 5
MCD_FILE_SAMPLE_DEFAULT = 20

EXPORT_DIR = 'temp_exports'

MAIN_MENU_OPS = ['Browse database', 'Upload initial machine file', 'Upload data', 'Add attributes', 'Edit database', 
                 'Search specific attributes', 'Graph interface', 'Analyze data', 'Admin']

COLUMN_MAP_STANDARD = {
    'SpinTrq': 'Spindle Torque (ft-lb)',
    'SpinPwr': 'Spindle Power (W)',
    'SpinVel': 'Spindle Speed (RPM)',
    'FeedVel': 'Feed Velocity (in/min)',
    'FeedTrq': 'Actuator Force (lbs)',
    'FRO': 'FRO',
    'Ktype1': 'Thermocouple 1 (deg C)',
    'Ktype2': 'Thermocouple 2 (deg C)',
    'Ktype3': 'Thermocouple 3 (deg C)',
    'Ktype4': 'Thermocouple 4 (deg C)',
    'O2': 'Oxygen Content',
    'ToolTemp': 'Tool Temperature (deg C)'
}

COLUMN_MAP_METRIC = {
    'SpinTrq': 'Spindle Torque (N·m)',
    'SpinPwr': 'Spindle Power (W)',
    'SpinVel': 'Spindle Speed (RPM)',
    'FeedVel': 'Feed Velocity (mm/s)',
    'FeedTrq': 'Actuator Force (N)',
    'FRO': 'FRO',
    'Ktype1': 'Thermocouple 1 (deg C)',
    'Ktype2': 'Thermocouple 2 (deg C)',
    'Ktype3': 'Thermocouple 3 (deg C)',
    'Ktype4': 'Thermocouple 4 (deg C)',
    'O2': 'Oxygen Content',
    'ToolTemp': 'Tool Temperature (deg C)'
}

AA_ALLOY_OPS = ['AA6061', 'AA7075', 'AA7050']

#shit you cant plot
INVALID_COLS = ['Timestamp', 'Time (Seconds)', 'Time', 'Date', 'Frame']

METRICS_MACHINEFILE = ['SpinPwr_min', 'SpinPwr_max', 'SpinPwr_avg', 'ToolTemp_min', 'ToolTemp_max', 'ToolTemp_avg', 
                       'SpinSP_min', 'SpinSP_max', 'SpinSP_avg', 'SpinTrq_min', 'SpinTrq_max', 'SpinTrq_avg', 'SpinVel_min', 'SpinVel_max', 'SpinVel_avg',
                       'FeedTrq_min', 'FeedTrq_max', 'FeedTrq_avg', 'FeedVel_min', 'FeedVel_max', 'FeedVel_avg', 
                       'PathVel_min', 'PathVel_max', 'PathVel_avg', 
                       'Ktype1_min', 'Ktype1_max', 'Ktype1_avg', 'Ktype2_min', 'Ktype2_max', 'Ktype2_avg', 
                       'Ktype3_min', 'Ktype3_max', 'Ktype3_avg', 'Ktype4_min', 'Ktype4_max', 'Ktype4_avg',
                       'XTrq_min', 'XTrq_max', 'XTrq_avg', 'YTrq_min', 'YTrq_max', 'YTrq_avg',
                       'ZTrq_min', 'ZTrq_max', 'ZTrq_avg']

MACHINEFILE_HEADERS = ['SpinPwr', 'SpinTrq', 'SpinVel', 'SpinSP', 'FeedVel', 'FeedTrq',
                       'Ktype1', 'Ktype2', 'Ktype3', 'Ktype4', 'ToolTemp',
                       'XTrq', 'YTrq', 'ZTrq', 'PathVel']

WHITELIST = ['login', 'auth_callback', 'static', 'healthcheck', 'generate_bypass']

MAT_TESTING_TABLES = ['Tension Test Data', 'Fracture Toughness Results', 'Smooth Fatigue Results']

FORCE_METS = ['Force_1_Force_min', 'Force_1_Force_max', 'Force_1_Force_avg',
    'Force_2_Force_min', 'Force_2_Force_max', 'Force_2_Force_avg',
    'Force_3_Force_min', 'Force_3_Force_max', 'Force_3_Force_avg',
    'Force_4_Force_min', 'Force_4_Force_max', 'Force_4_Force_avg',
    'Force_5_Force_min', 'Force_5_Force_max', 'Force_5_Force_avg', 
    'Total_Force_min', 'Total_Force_max', 'Total_Force_avg']

HTHFS_METS = ['HTHFS_1_Average_Temperature_min', 'HTHFS_1_Average_Temperature_max', 'HTHFS_1_Average_Temperature_avg',
    'HTHFS_1_Bottom_Temperature_min', 'HTHFS_1_Bottom_Temperature_max', 'HTHFS_1_Bottom_Temperature_avg',
    'HTHFS_1_HeatFlux_min', 'HTHFS_1_HeatFlux_max', 'HTHFS_1_HeatFlux_avg',
    'HTHFS_1_Top_Temperature_min', 'HTHFS_1_Top_Temperature_max', 'HTHFS_1_Top_Temperature_avg']

LTHFS_METS = ['LTHFS_1_HeatFlux_min', 'LTHFS_1_HeatFlux_max', 'LTHFS_1_HeatFlux_avg',
    'LTHFS_1_Temperature_min', 'LTHFS_1_Temperature_max', 'LTHFS_1_Temperature_avg',
    'LTHFS_2_HeatFlux_min', 'LTHFS_2_HeatFlux_max', 'LTHFS_2_HeatFlux_avg',
    'LTHFS_2_Temperature_min', 'LTHFS_2_Temperature_max', 'LTHFS_2_Temperature_avg',
    'LTHFS_3_HeatFlux_min', 'LTHFS_3_HeatFlux_max', 'LTHFS_3_HeatFlux_avg',
    'LTHFS_3_Temperature_min', 'LTHFS_3_Temperature_max', 'LTHFS_3_Temperature_avg',
    'LTHFS_4_HeatFlux_min', 'LTHFS_4_HeatFlux_max', 'LTHFS_4_HeatFlux_avg',
    'LTHFS_4_Temperature_min', 'LTHFS_4_Temperature_max', 'LTHFS_4_Temperature_avg',
    'LTHFS_5_HeatFlux_min', 'LTHFS_5_HeatFlux_max', 'LTHFS_5_HeatFlux_avg',
    'LTHFS_5_Temperature_min', 'LTHFS_5_Temperature_max', 'LTHFS_5_Temperature_avg']

TC_METS = ['TC_10_Temperature_min', 'TC_10_Temperature_max', 'TC_10_Temperature_avg',
    'TC_11_Temperature_min', 'TC_11_Temperature_max', 'TC_11_Temperature_avg',
    'TC_12_Temperature_min', 'TC_12_Temperature_max', 'TC_12_Temperature_avg',
    'TC_13_Temperature_min', 'TC_13_Temperature_max', 'TC_13_Temperature_avg',
    'TC_14_Temperature_min', 'TC_14_Temperature_max', 'TC_14_Temperature_avg',
    'TC_5_Temperature_min', 'TC_5_Temperature_max', 'TC_5_Temperature_avg',
    'TC_6_Temperature_min', 'TC_6_Temperature_max', 'TC_6_Temperature_avg',
    'TC_7_Temperature_min', 'TC_7_Temperature_max', 'TC_7_Temperature_avg',
    'TC_8_Temperature_min', 'TC_8_Temperature_max', 'TC_8_Temperature_avg',
    'TC_9_Temperature_min', 'TC_9_Temperature_max', 'TC_9_Temperature_avg']

INSITU_METS = [FORCE_METS, HTHFS_METS, LTHFS_METS, TC_METS]

#------------------------------------------------------------------ attribute constants. dont even try to read or interpret this mess gang just trust me
#for demo but mimicking real 
X_OPS = [f'X{i}' for i in range(0, 7)]
Y_OPS = [f'Y{i}' for i in range(0, 7)]
Z_OPS = [f'Z{i}' for i in range(0, 7)]

#categories for rigid attribute adding
ATT_CATEGORIES_HIGHEST = ['Build', 'Exsitu', 'Manually add']

#---------build
ATT_SUB_BUILD = ['Context', 'Build details', 'Parameters', 'Deflection/etc'] ###
CONTEXT_K = ['date', 'time', 'temp(C)', 'humidity(%)']
BUILD_DETAILS_K = ['tool_serial', 'tool_path', 'tool_type', 'machine_type', 'experiment_id', 'mat_batch']
PARAMETERS_K = ['heat_plate_setpoint(C)', 'PID_setpoint', 'bead_size', 'feed_rate_comp']
IDK = ['x_total_deflection', 'y_total_deflection', 'z_total_deflection', 'shear_force', 'strain', 'flow_stress']
BUILD_KEYS = [CONTEXT_K, BUILD_DETAILS_K, PARAMETERS_K, IDK]

#---------exsitu
ATT_SUB_EXSITU = ['Temper', 'Thermal Practice', 'Air Thermocouples', 'Load Thermocouples', 
                  'Material Spec', 'Tensile', 'Fracture Toughness', 'Smooth Fatigue', 'PIP', 'Metallography']      
#above are categories, below are attribute keys to be entered into db
TEMPER_K = ['temper']
THERM_PRAC_K = ['heat_treat', 'age1', 'age2', 'age3', 'anneal', 'homogenization']
AIR_TC_K = [f'ATC{i}' for i in range (0, 10)]
LOAD_TC_K = [f'LTC{i}' for i in range (0, 10)]
MAT_SPEC_K = [f'placeholder{i}' for i in range (0, 7)]      ###
TENSILE_K = ['ultimate_d1', 'ultimate_d2', 'ultimate_d3',
             'yield_d1', 'yield_d2', 'yield_d3',
             'elongation_d1', 'elongation_d2', 'elongation_d3']
FRAC_TOUGH_K = ['d1', 'd2', 'd3']                           ###         little d stands for "direction" idk what directions jacob was talking abt yet
SMOOTH_FAT_K = ['d1']                                       ###
PIP_K = ['ultimate_d1', 'ultimate_d2',                      ###
         'yield_d1', 'yield_d2',
         'elongation_d1', 'elongation_d2',
         'hardness_d1', 'hardness_d2']
METALLOG_K = ['metallog_traverse', 'metallog_crosstrack', 'metallog_build'] ###???
EXSITU_KEYS = [TEMPER_K, THERM_PRAC_K, AIR_TC_K, LOAD_TC_K, MAT_SPEC_K, TENSILE_K, FRAC_TOUGH_K, SMOOTH_FAT_K, PIP_K, METALLOG_K]
#attribute values to each key

ATT_SUBCATEGORIES_3 = [f'placeholder{i}' for i in range (0, 3)]
ALL_ATT_SUBCATEGORIES = [ATT_SUB_BUILD, ATT_SUB_EXSITU, ATT_SUBCATEGORIES_3]
