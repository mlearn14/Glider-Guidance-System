# =========================
# X - Imports
# =========================

import cartopy.crs as ccrs
import cartopy.feature as cfeature
import cmocean.cm as cmo
from datetime import datetime
from erddapy import ERDDAP
import matplotlib.pyplot as plt
import numpy as np
import os
from SUB_functions import calculate_gridpoint, set_map_ticks, set_cbar_ticks

# =========================
# PLOTTING
# =========================

### FUNCTION:
def GGS_plot_currents(config, directory, waypoints, model_data, currents_data, qc_latitude, qc_longitude, extent='data', map_lons=[0, 0], map_lats=[0, 0], show_route=False, show_qc=False):
    
    '''
    Plot the depth-averaged current fields.
    Optionally display the mission route and/or QC sample point.

    Args:
    - config (dict): Glider Guidance System mission configuration.
    - directory (str): Glider Guidance System mission directory.
    - waypoints (list): Glider Guidance System mission waypoints.
    - model_data (xarray.Dataset): Ocean model dataset.
    - currents_data (xarray.Dataset): Dataset with the computed variables and layer information.
    - extent (str): Extent of the plot.
        - if 'map', use the map_lons and map_lats.
        - if 'data', use the model_data extent.
    - map_lons (list): Longitude bounds of the map, if extent='map'.
    - map_lats (list): Latitude bounds of the map, if extent='map'.
    - show_route (bool): Show the route on the plot.
        - default: 'False'
        - if True, show the route.
        - if False, do not show the route.
    - show_qc (bool): Whow the QC sample point.
        - default: 'False'
        - if True, show the QC sample point.
        - if False, do not show the QC sample point.
    - qc_latitude (float): Latitude of the QC sample point.
    - qc_longitude (float): Longitude of the QC sample point.

    Returns:
    - None
    '''

    u_avg = currents_data['u_avg'].values
    v_avg = currents_data['v_avg'].values
    magnitude = currents_data['magnitude'].values
    
    data_lons = model_data.lon.values
    data_lats = model_data.lat.values

    fig, ax = plt.subplots(subplot_kw={'projection': ccrs.PlateCarree()})

    if extent == 'map':
        ax.set_extent([min(map_lons), max(map_lons), min(map_lats), max(map_lats)], crs=ccrs.PlateCarree())
        set_map_ticks(ax, map_lons, map_lats)
    elif extent == 'data':
        ax.set_extent([np.min(data_lons), np.max(data_lons), np.min(data_lats), np.max(data_lats)], crs=ccrs.PlateCarree())
        set_map_ticks(ax, data_lons, data_lats)
    else:
        raise ValueError("Invalid extent option. Use 'map' or 'data'.")

    contour = ax.contourf(data_lons, data_lats, magnitude, cmap=cmo.speed, transform=ccrs.PlateCarree())
    ax.streamplot(data_lons, data_lats, u_avg, v_avg, color='black', transform=ccrs.PlateCarree(), density=2)

    if show_route:
        lats, lons = zip(*waypoints)
        ax.plot(lons, lats, 'w-', transform=ccrs.PlateCarree(), linewidth=2.5, zorder=1)
        ax.plot(lons, lats, 'k', transform=ccrs.PlateCarree(), linewidth=1.0, linestyle='--', alpha=0.6, zorder=2)
        
        start_coords = config["waypoints"][0]
        end_coords = config["waypoints"][-1]
        ax.scatter(*start_coords[::-1], color='green', s=100, transform=ccrs.PlateCarree(), zorder=3)
        for waypoint in config["waypoints"][1:-1]:
            ax.scatter(*waypoint[::-1], color='blue', s=100, transform=ccrs.PlateCarree(), zorder=3)
        ax.scatter(*end_coords[::-1], color='red', s=100, transform=ccrs.PlateCarree(), zorder=3)

    if show_qc:
        (y_index, x_index), (lat_index, lon_index) = calculate_gridpoint(model_data, qc_latitude, qc_longitude)
        qc_lon = model_data['lon'].isel(x=x_index, y=y_index).values
        qc_lat = model_data['lat'].isel(x=x_index, y=y_index).values
        ax.scatter(qc_lon, qc_lat, color='red', s=100, transform=ccrs.PlateCarree(), zorder=5)

    ax.add_feature(cfeature.GSHHSFeature(scale='full'), edgecolor="black", facecolor="tan", zorder=2)
    ax.add_feature(cfeature.LAND, edgecolor="black", facecolor="tan", zorder=2)
    ax.add_feature(cfeature.OCEAN, zorder=0, edgecolor='k', facecolor='lightblue')
    ax.add_feature(cfeature.BORDERS, linestyle=':')
    ax.add_feature(cfeature.NaturalEarthFeature('cultural', 'admin_0_boundary_lines_land', '10m', edgecolor='k', linestyle=':'))

    # if extent == 'map':
    #     bbox = [min(map_lons), max(map_lons), min(map_lats), max(map_lats)]
    # elif extent == 'data':
    #     bbox = [np.min(data_lons), np.max(data_lons), np.min(data_lats), np.max(data_lats)]
    # add_bathymetry(ax, bbox, isobath_levels=(-100, -1000), zorder=5, transform=ccrs.PlateCarree())

    box = ax.get_position()
    ax.set_position([box.x0, box.y0, box.width * 1, box.height])
    cbar_ax = fig.add_axes([box.x0 + box.width + 0.005, box.y0, 0.03, box.height])
    cbar = fig.colorbar(contour, cax=cbar_ax, orientation='vertical')
    cbar.set_label('Depth Averaged Current Magnitude (m/s)', labelpad=10)
    set_cbar_ticks(cbar, magnitude)

    title_text = f"{config['glider_name']} Mission - Depth-Averaged Currents"
    ax.set_title(title_text, pad=20)
    subtitle_text = f"Depth Range: {config['max_depth']}m"
    fig.text(0.5, 0.9, subtitle_text, ha='center', va='center', fontsize=10)
    suptitle_text = f"Generated the Glider Guidance System (GGS) on {datetime.utcnow().strftime('%m-%d-%Y')} at {datetime.utcnow().strftime('%H:%M')} UTC"
    fig.suptitle(suptitle_text, fontsize='smaller', x=0.5, y=0.01, ha='center', va='bottom', color='gray')
    
    fig_filename = f"{config['glider_name']}_{config['max_depth']}m_currents.png"
    fig_path = os.path.join(directory, fig_filename)
    fig.savefig(fig_path, dpi=300, bbox_inches='tight')

    plt.close(fig)
