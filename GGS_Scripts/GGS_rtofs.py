# =========================
# FUNCTIONS
# =========================

### IMPORT:
from SUB_functions import *

### NOTES:
# N/A

# =========================
# GGS CONFIGURATION
# =========================

### IMPORT:
from SUP_config import *

### NOTES:
# N/A

# =========================
# ROUTE ANALYSIS
# =========================

### IMPORT:
from SUP_route_analysis import *

### NOTES:
# N/A

# =========================
# [RTOFS] MODEL DATA PROCESSING
# =========================

### IMPORT:
from MOD_rtofs import *

### NOTES:
# N/A

# =========================
# QUALITY CONTROL CHECKS
# =========================

### IMPORT:
from SUP_qualitycontrol import *

### NOTES:
# N/A

# =========================
# PLOTS
# =========================

### IMPORT:
from SUP_plots import *

### NOTES:
# N/A

# =========================
# X - MAIN
# =========================

### RUN:
EXIT_KEYWORD = "EXIT"
def main():
    
    '''
    GGS main function.
    '''

    config, waypoints = GGS_config_static() # Manual
    # config, waypoints = GGS_config() # Automatic
    directory = GGS_config_output(config)

    analysis_results = route_analysis(config, waypoints)
    route_analysis_output(config, directory, analysis_results)

    rtofs = RTOFS()
    rtofs.rtofs_subset(config, waypoints, subset=True)
    rtofs_data = rtofs.data
    rtofs_qc = rtofs.rtofs_qc
    rtofs.rtofs_save(config, directory)

    calculated_data, bin_data = interp_average(config, directory, rtofs_data)

    latitude = '21.5'
    longitude = '-85.5'
    qc_currents_comparison(config, directory, rtofs_data, rtofs_qc, latitude, longitude)
    qc_currents_profile(config, directory, rtofs_data, calculated_data, bin_data, latitude, longitude)

    GGS_plot_currents(config, waypoints, directory, rtofs_data, calculated_data, extent='data', map_lons=[0, 0], map_lats=[0, 0], show_route=False)

if __name__ == "__main__":
    main()

# =========================
# ///// END OF SCRIPT \\\\\
# =========================