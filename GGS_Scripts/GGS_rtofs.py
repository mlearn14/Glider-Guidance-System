# =========================
# FUNCTIONS
# =========================

from GGS_Scripts.X_functions import *

# =========================
# GGS CONFIGURATION
# =========================

from GGS_Scripts.X_config import *

# =========================
# ROUTE ANALYSIS
# =========================

from GGS_Scripts.X_route_analysis import *

# =========================
# [RTOFS] MODEL DATA PROCESSING
# =========================

from GGS_Scripts.X_rtofs import *

# =========================
# QUALITY CONTROL CHECKS
# =========================

from GGS_Scripts.X_quality_control import *

# =========================
# PLOTS
# =========================

from GGS_Scripts.X_plots import *

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
    calculated_data, bin_data = interp_depth_average(config, directory, rtofs_data)

    qc_latitude = '21.100'
    qc_longitude = '-86.425'
    qc_uv_profile(config, directory, rtofs_qc, calculated_data, bin_data, qc_latitude, qc_longitude)

    GGS_plot_currents(config, directory, waypoints, rtofs_data, calculated_data, qc_latitude, qc_longitude, extent='data', map_lons=[0, 0], map_lats=[0, 0], show_route=False, show_qc=False)
    GGS_plot_threshold(config, directory, waypoints, rtofs_data, calculated_data, qc_latitude, qc_longitude, mag1=0.25, mag2=0.5, mag3=0.75, extent='data', map_lons=[0, 0], map_lats=[0, 0], show_route=False, show_qc=False)

if __name__ == "__main__":
    main()

# =========================
# ///// END OF SCRIPT \\\\\
# =========================