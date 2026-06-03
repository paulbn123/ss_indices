import streamlit as st

import folium
from folium.plugins import Draw
from streamlit_folium import st_folium
from shapely.geometry import shape
import geopandas as gpd

from config.config_constants import (DEBUG, STORENAME_COLUMN)

def render_selection_map(gdf: gpd.GeoDataFrame, key: str = "selection_map"):
    """
    Render a folium map with drawing tools for polygon selection.
    
    Args:
        gdf: Filtered GeoDataFrame with points to display
        key: Unique key for the streamlit_folium component
    
    Returns:
        selected_polygon: Shapely polygon if drawn, otherwise None
    """
    if gdf is None or gdf.empty:
        st.warning("No points to display on map")
        return None
    
    # Get total bounds (minx, miny, maxx, maxy)
    bounds = gdf.total_bounds  # returns (minx, miny, maxx, maxy)
    center_lat = (bounds[1] + bounds[3]) / 2
    center_lon = (bounds[0] + bounds[2]) / 2

    m = folium.Map(tiles='CartoDB Positron',
                   location=[center_lat, center_lon])

    # Fit bounds
    m.fit_bounds([[bounds[1], bounds[0]], [bounds[3], bounds[2]]])
    
    # Add points to map
    for _, row in gdf.iterrows():
        folium.CircleMarker(
            location=[row.geometry.y, row.geometry.x],
            radius=3,
            popup=row.get(STORENAME_COLUMN, "No name found"),
            color="blue",
            fill=True
        ).add_to(m)
    
    # Add drawing controls
    draw_control = Draw(
        draw_options={
            "polygon": True,
            "rectangle": True,
            "circle": False,
            "circlemarker": False,
            "marker": False,
            "polyline": False,
        },
        edit_options={"edit": True, "remove": True}
    )
    draw_control.add_to(m)
    
    # Display map and capture drawings
    output = st_folium(
        m, 
        width=800, 
        height=600, 
        returned_objects=["all_drawings", "last_active_drawing"],
        key=key
    )
    
    # Extract polygon from drawings
    selected_polygon = None
    if output["all_drawings"] and len(output["all_drawings"]) > 0:
        latest_drawing = output["last_active_drawing"]
        if latest_drawing and latest_drawing["geometry"]["type"] in ["Polygon", "MultiPolygon"]:
            selected_polygon = shape(latest_drawing["geometry"])
    
    return selected_polygon