# =========================
# X - Imports
# =========================

### /// PLOTS ///
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import cmocean.cm as cmo
from datetime import datetime
import matplotlib.pyplot as plt
import numpy as np
import os
import plotly.graph_objects as go
import plotly.io as pio
from SUB_functions import set_ticks
from SUP_route_analysis import route_analysis_output

# =========================
# PLOTTING
# =========================

### FUNCTION:
def GGS_plot_currents(config, waypoints, directory, model_data, currents_data, extent='data', map_lons=[0, 0], map_lats=[0, 0], show_route=False):
    
    '''
    Plot the glider's mission route along with the depth-averaged current fields using currents_data.

    Args:
    - config (dict): dictionary of configuration parameters
    - waypoints (list): list of waypoints
    - directory (str): directory to save the figure
    - model_data (xarray.Dataset): ocean model data
    - currents_data (xarray.Dataset): dataset with the computed variables and layer information
    - extent (str): extent of the plot, either 'map' or 'data'
    - map_lons (list): longitude bounds of the map, if extent='map'
    - map_lats (list): latitude bounds of the map, if extent='map'
    - show_route (bool): whether or not to show the route on the plot

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
        set_ticks(ax, map_lons, map_lats)
    elif extent == 'data':
        ax.set_extent([np.min(data_lons), np.max(data_lons), np.min(data_lats), np.max(data_lats)], crs=ccrs.PlateCarree())
        set_ticks(ax, data_lons, data_lats)
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

    ax.add_feature(cfeature.GSHHSFeature(scale='full'), edgecolor="black", facecolor="tan", zorder=2)
    ax.add_feature(cfeature.LAND, edgecolor="black", facecolor="tan", zorder=2)
    ax.add_feature(cfeature.OCEAN, zorder=0, edgecolor='k', facecolor='lightblue')
    ax.add_feature(cfeature.BORDERS, linestyle=':')
    ax.add_feature(cfeature.NaturalEarthFeature('cultural', 'admin_0_boundary_lines_land', '10m', edgecolor='k', linestyle=':'))

    box = ax.get_position()
    ax.set_position([box.x0, box.y0, box.width * 0.85, box.height])
    cbar_ax = fig.add_axes([box.x0 + box.width + 0.01, box.y0, 0.03, box.height])
    fig.colorbar(contour, cax=cbar_ax, orientation='vertical', label='Depth Averaged Current Magnitude (m/s)')
    
    title = f"{config['glider_name']} Mission - {config['max_depth']}m Depth-Averaged Currents"
    ax.set_title(title, pad=20)
    subtitle = f"Generated the Glider Guidance System (GGS) on {datetime.utcnow().strftime('%m-%d-%Y')} at {datetime.utcnow().strftime('%H:%M')} UTC"
    fig.suptitle(subtitle, fontsize='smaller', x=0.5, y=0.01, ha='center', va='bottom', color='gray')

    fig_filename = f"{config['glider_name']}_{config['max_depth']}m_currents.png"
    fig_path = os.path.join(directory, fig_filename)
    fig.savefig(fig_path, dpi=300, bbox_inches='tight')

    plt.close(fig)

### FUNCTION: (DEPRECATED)
def GGS_plot_gauge(config, directory, analysis_results):

    '''
    Plot a gauge showing the remaining battery capacity estimate for the configured mission.

    Args:
    - config (dict): The GGS configuration dictionary.
    - directory (str): The directory path where the configuration is saved.
    - analysis_results (list): List of dictionaries containing data for each leg of the route.

    Returns:
    - None
    '''
    
    total_distance, total_time_seconds, total_time_hours, total_battery_drain = route_analysis_output(config, directory, analysis_results)
    battery_remaining = config["battery_capacity"] - total_battery_drain

    fig_gauge = go.Figure(go.Indicator(
        mode = "gauge+number+delta",
        value = battery_remaining,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': "Battery Remaining (Amperage)", 'font': {'size': 24}},
        delta = {'reference': config["battery_capacity"], 'increasing': {'color': "RebeccaPurple"}},
        gauge = {
            'axis': {'range': [0, config["battery_capacity"]], 'tickwidth': 1, 'tickcolor': "darkblue"},
            'bar': {'color': "yellow"},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "gray",
            'steps': [
                {'range': [0, 0.5*config["battery_capacity"]], 'color': 'lightgray'},
                {'range': [0.5*config["battery_capacity"], config["battery_capacity"]], 'color': 'gray'}]
            }))

    fig_gauge.update_layout(paper_bgcolor = "lavender", font = {'color': "darkblue", 'family': "Arial"})

    gauge_filename = f"{config['glider_name']}_battery_gauge.png"
    gauge_path = os.path.join(directory, gauge_filename)
    
    pio.write_image(fig_gauge, gauge_path, format='png')

# =========================
#
# GGS_plot_currents(config, waypoints, directory, rtofs_data, currents_data, extent='data', map_lons=[0, 0], map_lats=[0, 0], show_route=False)
#
# GGS_plot_gauge(config, directory, analysis_results)

# =========================