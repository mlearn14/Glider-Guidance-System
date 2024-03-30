# =========================
# IMPORTS
# =========================

import cartopy.crs as ccrs
import cartopy.feature as cfeature
import cmocean.cm as cmo
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
import numpy as np
import os

from A_functions import calculate_gridpoint, plot_formatted_ticks, plot_bathymetry, plot_profile_thresholds, plot_add_gliders, plot_add_eez, plot_streamlines, plot_magnitude_contour, plot_threshold_zones, plot_advantage_zones, profile_rtofs, profile_cmems, profile_gofs, plot_glider_route, format_figure_titles, format_subplot_titles, format_subplot_headers, format_save_datetime, print_starttime, print_endtime, print_runtime

# =========================

### FUNCTION:
def GGS_plot_profiles(config, directory, datetime_index, model_datasets, latitude_qc=None, longitude_qc=None, threshold=0.5):
    
    '''
    Produce quality control profiles for 'u', 'v', 'magnitude', and 'direction' data at the specified point of interest.

    Args:
    - config (dict): The configuration dictionary.
    - directory (str): The directory to save the plot.
    - latitude_qc (float): The latitude of the point of interest.
    - longitude_qc (float): The longitude of the point of interest.
    - threshold (float): The threshold value for the shading.
    - model_datasets (tuple): Tuple containing the three model datasets.

    Returns:
    - None
    '''

    print(f"\n### CREATING PROFILE PLOT ###\n")
    start_time = print_starttime()

    valid_datasets = [dataset for dataset in model_datasets if dataset]
    num_datasets = len(valid_datasets)

    if num_datasets < 3:
        print("Insufficient datasets for plotting.")
        end_time = print_endtime()
        print_runtime(start_time, end_time)
        return
    if num_datasets == 0:
        print("No datasets provided for plotting.")
        end_time = print_endtime()
        print_runtime(start_time, end_time)
        return

    fig, axs = plt.subplots(num_datasets, 4, figsize=(20, 10 * num_datasets))
    if num_datasets == 1:
        axs = np.array([axs])

    profile_functions = {
        'RTOFS': profile_rtofs,
        'CMEMS': profile_cmems,
        'GOFS': profile_gofs
    }

    for i, dataset in enumerate(valid_datasets):
        model_name = dataset[0].attrs.get('model_name')
        profile_func = profile_functions.get(model_name)
        if profile_func:
            row_axes = axs[i, :]
            profile_func(row_axes, dataset, latitude_qc, longitude_qc, threshold)
    
    subplot_titles = [dataset[0].attrs.get('model_name') for dataset in valid_datasets if dataset]
    format_subplot_headers(axs, fig, subplot_titles)

    title_text = f"Vertical Profile Subplots - (Lat: {latitude_qc:.3f}, Lon: {longitude_qc:.3f})"
    format_subplot_titles(fig, config, datetime_index, title=title_text)

    file_datetime = format_save_datetime(datetime_index)
    fig_filename = f"DepthAverageProfiles_{config['MISSION']['max_depth']}m_{file_datetime}.png"
    fig_path = os.path.join(directory, fig_filename)
    fig.savefig(fig_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    
    end_time = print_endtime()
    print_runtime(start_time, end_time)

### FUNCTION:
def GGS_plot_magnitudes(config, directory, datetime_index, model_datasets, latitude_qc=None, longitude_qc=None, density=2, gliders=None, show_route=False, show_eez=False, show_qc=False, manual_extent=None):
    
    '''
    Plot the depth-averaged current fields from three datasets side by side.

    Args:
    - config (dict): Glider Guidance System mission configuration.
    - directory (str): Directory to save the plot.
    - datetime_index (int): Index of the datetime for the plot title.
    - model_datasets (tuple): Tuple containing the model datasets.
    - latitude_qc (float): Latitude for QC plotting.
    - longitude_qc (float): Longitude for QC plotting.
    - density (int): Density of the streamplot.
    - gliders (optional): DataFrame containing glider data for plotting.
    - show_route (bool): Flag to show the glider route.
    - show_qc (bool): Flag to show the QC sample point.
    - show_eez (bool): Flag to show the Exclusive Economic Zone (EEZ).
    - manual_extent (list or None): Manual specification of plot extent.

    Returns:
    - None
    '''

    # INITIALIZATION
    print(f"\n### CREATING MAGNITUDE PLOT ###\n")
    start_time = print_starttime()

    # DATASET EXTRACTION
    valid_datasets = [datasets for datasets in model_datasets if datasets is not None]
    num_datasets = len(valid_datasets)
    if num_datasets == 0:
        print("No datasets provided for plotting.")
        end_time = print_endtime()
        print_runtime(start_time, end_time)
        return

    # PLOTTING FUNCTION
    def plot_magnitude(ax, config, model_depth_average, latitude_qc, longitude_qc, density, gliders, show_route, show_qc, show_eez, manual_extent):
        
        # DATA EXTRACTION
        longitude = model_depth_average.lon.values.squeeze()
        latitude = model_depth_average.lat.values.squeeze()
        u_depth_avg = model_depth_average['u_depth_avg'].values.squeeze()
        v_depth_avg = model_depth_average['v_depth_avg'].values.squeeze()
        mag_depth_avg = model_depth_average['mag_depth_avg'].values.squeeze()
        
        # EXTENT SETUP
        if manual_extent is not None and len(manual_extent) == 2 and all(len(sublist) == 2 for sublist in manual_extent):
            map_extent = [manual_extent[0][1], manual_extent[1][1], manual_extent[0][0], manual_extent[1][0]]
        else:
            data_extent_lon = [float(longitude.min()), float(longitude.max())]
            data_extent_lat = [float(latitude.min()), float(latitude.max())]
            map_extent = data_extent_lon + data_extent_lat
        ax.set_extent(map_extent, crs=ccrs.PlateCarree())
        plot_formatted_ticks(ax, map_extent[:2], map_extent[2:], proj=ccrs.PlateCarree(), fontsize=16, label_left=True, label_right=False, label_bottom=True, label_top=False, gridlines=True)

        # PLOT ELEMENTS
        plot_magnitude_contour(ax, fig, longitude, latitude, mag_depth_avg, max_levels=10, extend_max=True)
        plot_streamlines(ax, longitude, latitude, u_depth_avg, v_depth_avg, density=density)

        # GLIDERS
        if gliders is not None:
            plot_add_gliders(ax, gliders, legend=True)
            glider_legend = ax.get_legend()
            if glider_legend:
                glider_legend.get_frame().set_alpha(0.5)
                glider_legend.get_frame().set_facecolor('white')
                ax.add_artist(glider_legend)
        
        # ROUTE
        if show_route:
            plot_glider_route(ax, config)
        
        # QUALITY CONTROL
        if show_qc:
            (y_index, x_index), (lat_index, lon_index) = calculate_gridpoint(model_depth_average, latitude_qc, longitude_qc)
            qc_lon = model_depth_average['lon'].isel(x=x_index, y=y_index).values
            qc_lat = model_depth_average['lat'].isel(x=x_index, y=y_index).values
            circle = Circle((qc_lon, qc_lat), radius=0.25, edgecolor='purple', facecolor='none', linewidth=2, transform=ccrs.PlateCarree(), zorder=95)
            ax.add_patch(circle)
        
        # EEZ
        if show_eez:
            plot_add_eez(ax, config, color='dimgrey', linewidth=3, zorder=90)
        
        # FEATURES
        ax.add_feature(cfeature.GSHHSFeature(scale='full'), edgecolor="black", facecolor="tan", linewidth=0.25, zorder=90)
        ax.add_feature(cfeature.RIVERS, edgecolor="steelblue", linewidth=0.25, zorder=90)
        ax.add_feature(cfeature.LAKES, edgecolor="black", facecolor="lightsteelblue", linewidth=0.25, zorder=90)
        ax.add_feature(cfeature.BORDERS, edgecolor="black", linewidth=0.25, zorder=90)

        plot_bathymetry(ax, config, model_depth_average, isobath1=-100, isobath2=-1000, downsample=True, show_legend=False)
        bathymetry_legend = ax.get_legend()
        if bathymetry_legend:
            bathymetry_legend.get_frame().set_alpha(0.5)
            ax.add_artist(bathymetry_legend)

    # PLOTTING
    fig, axs = plt.subplots(1, num_datasets, subplot_kw={'projection': ccrs.Mercator()}, figsize=(10*num_datasets, 10))
    if num_datasets == 1:
        axs = [axs]
    
    model_names = []
    for ax, (model_data, depth_average_data, bin_average_data) in zip(axs, valid_datasets):
        model_name = depth_average_data.attrs['model_name']
        model_names.append(model_name)
        plot_magnitude(ax, config, depth_average_data, latitude_qc, longitude_qc, density, gliders, show_route, show_qc, show_eez, manual_extent)
        ax.set_title(f"{model_name}", fontsize=14, fontweight='bold', pad=20)

    title_text = f"Depth Averaged Currents - Depth Range: {config['MISSION']['max_depth']}m"
    model_names_combined = " vs. ".join(model_names)
    format_figure_titles(axs[0], fig, config, datetime_index, model_name=model_names_combined, title=title_text)

    # SAVE & CLOSE
    file_datetime = format_save_datetime(datetime_index)
    fig_filename = f"DepthAverageMagnitude_{config['MISSION']['max_depth']}m_{file_datetime}.png"
    fig_path = os.path.join(directory, fig_filename)
    fig.savefig(fig_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    
    # LOGGING
    end_time = print_endtime()
    print_runtime(start_time, end_time)

### FUNCTION:
def GGS_plot_threshold(config, directory, datetime_index, model_datasets, latitude_qc=None, longitude_qc=None, density=2, mag1=0.0, mag2=0.2, mag3=0.3, mag4=0.4, mag5=0.5, gliders=None, show_route=False, show_eez=False, show_qc=False, manual_extent=None):
    
    '''
    Plot the depth-averaged current fields from three datasets side by side.

    Args:
    - config (dict): Glider Guidance System mission configuration.
    - directory (str): Directory to save the plot.
    - datetime_index (int): Index of the datetime for the plot title.
    - model_datasets (tuple): Tuple containing the model datasets.
    - latitude_qc (float): Latitude for QC plotting.
    - longitude_qc (float): Longitude for QC plotting.
    - density (int): Density of the streamplot.
    - mag1 (float): Threshold for the first magnitude level.
    - mag2 (float): Threshold for the second magnitude level.
    - mag3 (float): Threshold for the third magnitude level.
    - mag4 (float): Threshold for the fourth magnitude level.
    - mag5 (float): Threshold for the fifth magnitude level.
    - gliders (optional): DataFrame containing glider data for plotting.
    - show_route (bool): Flag to show the glider route.
    - show_qc (bool): Flag to show the QC sample point.
    - show_eez (bool): Flag to show the Exclusive Economic Zone (EEZ).
    - manual_extent (list or None): Manual specification of plot extent.

    Returns:
    - None
    '''

    # INITIALIZATION
    print(f"\n### CREATING THRESHOLD PLOT ###\n")
    start_time = print_starttime()

    # DATASET EXTRACTION
    valid_datasets = [datasets for datasets in model_datasets if datasets is not None]
    num_datasets = len(valid_datasets)
    if num_datasets == 0:
        print("No datasets provided for plotting.")
        end_time = print_endtime()
        print_runtime(start_time, end_time)
        return

    # PLOTTING FUNCTION
    def plot_threshold(ax, config, model_depth_average, latitude_qc, longitude_qc, density, mag1, mag2, mag3, mag4, mag5, gliders, show_route, show_qc, show_eez, manual_extent):
        
        # DATA EXTRACTION
        longitude = model_depth_average.lon.values.squeeze()
        latitude = model_depth_average.lat.values.squeeze()
        u_depth_avg = model_depth_average['u_depth_avg'].values.squeeze()
        v_depth_avg = model_depth_average['v_depth_avg'].values.squeeze()
        mag_depth_avg = model_depth_average['mag_depth_avg'].values.squeeze()
        
        # EXTENT SETUP
        if manual_extent is not None and len(manual_extent) == 2 and all(len(sublist) == 2 for sublist in manual_extent):
            map_extent = [manual_extent[0][1], manual_extent[1][1], manual_extent[0][0], manual_extent[1][0]]
        else:
            data_extent_lon = [float(longitude.min()), float(longitude.max())]
            data_extent_lat = [float(latitude.min()), float(latitude.max())]
            map_extent = data_extent_lon + data_extent_lat
        ax.set_extent(map_extent, crs=ccrs.PlateCarree())
        plot_formatted_ticks(ax, map_extent[:2], map_extent[2:], proj=ccrs.PlateCarree(), fontsize=16, label_left=True, label_right=False, label_bottom=True, label_top=False, gridlines=True)

        # PLOT ELEMENTS
        plot_threshold_zones(ax, longitude, latitude, mag_depth_avg, mag1, mag2, mag3, mag4, mag5, threshold_legend=True)
        plot_streamlines(ax, longitude, latitude, u_depth_avg, v_depth_avg, density=density)

        # GLIDERS
        if gliders is not None:
            plot_add_gliders(ax, gliders, legend=True)
            glider_legend = ax.get_legend()
            if glider_legend:
                glider_legend.get_frame().set_alpha(0.5)
                glider_legend.get_frame().set_facecolor('white')
                ax.add_artist(glider_legend)

        # ROUTE
        if show_route:
            plot_glider_route(ax, config)
        
        # QUALITY CONTROL
        if show_qc:
            (y_index, x_index), (lat_index, lon_index) = calculate_gridpoint(model_depth_average, latitude_qc, longitude_qc)
            qc_lon = model_depth_average['lon'].isel(x=x_index, y=y_index).values
            qc_lat = model_depth_average['lat'].isel(x=x_index, y=y_index).values
            circle = Circle((qc_lon, qc_lat), radius=0.25, edgecolor='purple', facecolor='none', linewidth=2, transform=ccrs.PlateCarree(), zorder=95)
            ax.add_patch(circle)

        # EEZ
        if show_eez:
            plot_add_eez(ax, config, color='dimgrey', linewidth=3, zorder=90)
        
        # FEATURES
        ax.add_feature(cfeature.GSHHSFeature(scale='full'), edgecolor="black", facecolor="tan", linewidth=0.25, zorder=90)
        ax.add_feature(cfeature.RIVERS, edgecolor="steelblue", linewidth=0.25, zorder=90)
        ax.add_feature(cfeature.LAKES, edgecolor="black", facecolor="lightsteelblue", linewidth=0.25, zorder=90)
        ax.add_feature(cfeature.BORDERS, edgecolor="black", linewidth=0.25, zorder=90)

        plot_bathymetry(ax, config, model_depth_average, isobath1=-100, isobath2=-1000, downsample=True, show_legend=False)
        bathymetry_legend = ax.get_legend()
        if bathymetry_legend:
            bathymetry_legend.get_frame().set_alpha(0.5)
            ax.add_artist(bathymetry_legend)
        
    # PLOT SETUP
    fig, axs = plt.subplots(1, num_datasets, subplot_kw={'projection': ccrs.Mercator()}, figsize=(10*num_datasets, 10))
    if num_datasets == 1:
        axs = [axs]

    model_names = []
    for ax, (model_data, depth_average_data, bin_average_data) in zip(axs, valid_datasets):
        model_name = depth_average_data.attrs['model_name']
        model_names.append(model_name)
        plot_threshold(ax, config, depth_average_data, latitude_qc, longitude_qc, density, mag1, mag2, mag3, mag4, mag5, gliders, show_route, show_qc, show_eez, manual_extent)
        ax.set_title(f"{model_name}", fontsize=14, fontweight='bold', pad=20)
    
    title_text = f"Depth Averaged Current Threshold Zones - Depth Range: {config['MISSION']['max_depth']}m"
    model_names_combined = " vs. ".join(model_names)
    format_figure_titles(axs[0], fig, config, datetime_index, model_name=model_names_combined, title=title_text)

    # SAVE & CLOSE
    file_datetime = format_save_datetime(datetime_index)
    fig_filename = f"DepthAverageThreshold_{config['MISSION']['max_depth']}m_{file_datetime}.png"
    fig_path = os.path.join(directory, fig_filename)
    fig.savefig(fig_path, dpi=300, bbox_inches='tight')
    plt.close(fig)

    # LOGGING
    end_time = print_endtime()
    print_runtime(start_time, end_time)

### FUNCTION:
def GGS_plot_advantage(config, directory, datetime_index, model_datasets, latitude_qc=None, longitude_qc=None, density=2, tolerance=15, mag1=0.0, mag2=0.2, mag3=0.3, mag4=0.4, mag5=0.5, gliders=None, show_route=False, show_eez=False, show_qc=False, manual_extent=None):
    
    '''
    Plot the depth-averaged current fields from three datasets side by side.

    Args:
    - config (dict): Glider Guidance System mission configuration.
    - directory (str): Directory to save the plot.
    - datetime_index (int): Index of the datetime for the plot title.
    - model_datasets (tuple): Tuple containing the model datasets.
    - latitude_qc (float): Latitude for QC plotting.
    - longitude_qc (float): Longitude for QC plotting.
    - density (int): Density of the streamplot.
    - tolerance (float): Tolerance for the bearing.
    - mag1 (float): Threshold for the first magnitude level.
    - mag2 (float): Threshold for the second magnitude level.
    - mag3 (float): Threshold for the third magnitude level.
    - mag4 (float): Threshold for the fourth magnitude level.
    - mag5 (float): Threshold for the fifth magnitude level.
    - gliders (optional): DataFrame containing glider data for plotting.
    - show_route (bool): Flag to show the glider route.
    - show_qc (bool): Flag to show the QC sample point.
    - show_eez (bool): Flag to show the Exclusive Economic Zone (EEZ).
    - manual_extent (list or None): Manual specification of plot extent.

    Returns:
    - None
    '''

    # INITIALIZATION
    print(f"\n### CREATING ADVANTAGE PLOT ###\n")
    start_time = print_starttime()

    # ADVANTAGE ZONE CHECK
    if not config['MISSION'].get('GPS_coords') or len(config['MISSION']['GPS_coords']) < 2:
        print("Insufficient GPS route coordinates provided. Skipping advantage zone plotting.")
        end_time = print_endtime()
        print_runtime(start_time, end_time)
        return
    
    # DATASET EXTRACTION
    valid_datasets = [datasets for datasets in model_datasets if datasets is not None]
    num_datasets = len(valid_datasets)
    if num_datasets == 0:
        print("No datasets provided for plotting.")
        end_time = print_endtime()
        print_runtime(start_time, end_time)
        return

    # PLOTTING FUNCTION
    def plot_advantage(ax, config, model_depth_average, latitude_qc, longitude_qc, density, tolerance, mag1, mag2, mag3, mag4, mag5, gliders, show_route, show_qc, show_eez, manual_extent):
        
        # DATA EXTRACTION
        longitude = model_depth_average.lon.values.squeeze()
        latitude = model_depth_average.lat.values.squeeze()
        u_depth_avg = model_depth_average['u_depth_avg'].values.squeeze()
        v_depth_avg = model_depth_average['v_depth_avg'].values.squeeze()
        mag_depth_avg = model_depth_average['mag_depth_avg'].values.squeeze()
        dir_depth_avg = model_depth_average['dir_depth_avg'].values[0, :, :].squeeze()
        
        # EXTENT SETUP
        if manual_extent is not None and len(manual_extent) == 2 and all(len(sublist) == 2 for sublist in manual_extent):
            map_extent = [manual_extent[0][1], manual_extent[1][1], manual_extent[0][0], manual_extent[1][0]]
        else:
            data_extent_lon = [float(longitude.min()), float(longitude.max())]
            data_extent_lat = [float(latitude.min()), float(latitude.max())]
            map_extent = data_extent_lon + data_extent_lat
        ax.set_extent(map_extent, crs=ccrs.PlateCarree())
        plot_formatted_ticks(ax, map_extent[:2], map_extent[2:], proj=ccrs.PlateCarree(), fontsize=16, label_left=True, label_right=False, label_bottom=True, label_top=False, gridlines=True)

        # PLOT ELEMENTS
        plot_threshold_zones(ax, longitude, latitude, mag_depth_avg, mag1, mag2, mag3, mag4, mag5, threshold_legend=True)
        plot_advantage_zones(ax, config, longitude, latitude, dir_depth_avg, tolerance, advantage_legend=True)
        plot_streamlines(ax, longitude, latitude, u_depth_avg, v_depth_avg, density=density)

        # GLIDERS
        if gliders is not None:
            plot_add_gliders(ax, gliders, legend=True)
            glider_legend = ax.get_legend()
            if glider_legend:
                glider_legend.get_frame().set_alpha(0.5)
                glider_legend.get_frame().set_facecolor('white')
                ax.add_artist(glider_legend)

        # ROUTE
        if show_route:
            plot_glider_route(ax, config)
        
        # QUALITY CONTROL
        if show_qc:
            (y_index, x_index), (lat_index, lon_index) = calculate_gridpoint(model_depth_average, latitude_qc, longitude_qc)
            qc_lon = model_depth_average['lon'].isel(x=x_index, y=y_index).values
            qc_lat = model_depth_average['lat'].isel(x=x_index, y=y_index).values
            circle = Circle((qc_lon, qc_lat), radius=0.25, edgecolor='purple', facecolor='none', linewidth=2, transform=ccrs.PlateCarree(), zorder=95)
            ax.add_patch(circle)

        # EEZ
        if show_eez:
            plot_add_eez(ax, config, color='dimgrey', linewidth=3, zorder=90)
        
        # FEATURES
        ax.add_feature(cfeature.GSHHSFeature(scale='full'), edgecolor="black", facecolor="tan", linewidth=0.25, zorder=90)
        ax.add_feature(cfeature.RIVERS, edgecolor="steelblue", linewidth=0.25, zorder=90)
        ax.add_feature(cfeature.LAKES, edgecolor="black", facecolor="lightsteelblue", linewidth=0.25, zorder=90)
        ax.add_feature(cfeature.BORDERS, edgecolor="black", linewidth=0.25, zorder=90)

        plot_bathymetry(ax, config, model_depth_average, isobath1=-100, isobath2=-1000, downsample=True, show_legend=False)
        bathymetry_legend = ax.get_legend()
        if bathymetry_legend:
            bathymetry_legend.get_frame().set_alpha(0.5)
            ax.add_artist(bathymetry_legend)
        
    # PLOT SETUP
    fig, axs = plt.subplots(1, num_datasets, subplot_kw={'projection': ccrs.Mercator()}, figsize=(10*num_datasets, 10))
    if num_datasets == 1:
        axs = [axs]

    model_names = []
    for ax, (model_data, depth_average_data, bin_average_data) in zip(axs, valid_datasets):
        model_name = depth_average_data.attrs['model_name']
        model_names.append(model_name)
        plot_advantage(ax, config, depth_average_data, latitude_qc, longitude_qc, density, tolerance, mag1, mag2, mag3, mag4, mag5, gliders, show_route, show_qc, show_eez, manual_extent)
        ax.set_title(f"{model_name}", fontsize=14, fontweight='bold', pad=20)
    
    title_text = f"Depth Averaged Current Advantage Zones - Depth Range: {config['MISSION']['max_depth']}m"
    model_names_combined = " vs. ".join(model_names)
    format_figure_titles(axs[0], fig, config, datetime_index, model_name=model_names_combined, title=title_text)

    # SAVE & CLOSE
    file_datetime = format_save_datetime(datetime_index)
    fig_filename = f"DepthAverageAdvantage_{config['MISSION']['max_depth']}m_{file_datetime}.png"
    fig_path = os.path.join(directory, fig_filename)
    fig.savefig(fig_path, dpi=300, bbox_inches='tight')
    plt.close(fig)

    # LOGGING
    end_time = print_endtime()
    print_runtime(start_time, end_time)
    