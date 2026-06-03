# utils/utils_render_app.py
import streamlit as st

from utils.utils_data_handling import (get_selected_properties, 
                                        add_selected_properties,
                                        get_filtered_geodataframe)
from utils.utils_map import render_selection_map
from utils.utils_display_selected_properties import display_selected_stores_table
from utils.utils_data_graphing import display_data_graph
from utils.utils_add_image import add_savills_logo
from utils.utils_sidebar import render_conditional_sidebar

from config.config_constants import DEBUG, SSDB_REF_COLUMN


def render_app():
    """Main app render function
    Map state- ie showing map when no properties have been selected
    Data State - shows the data for when properties have been selected    
    """
    
    selected_properties = get_selected_properties()
    
    if DEBUG:
        print(f'$$$$DEBUG render_app selected_properties: {len(selected_properties)}')
    
    gdf_filtered = get_filtered_geodataframe()
    
    if DEBUG:
        if gdf_filtered is not None:
            print(f'$$$$DEBUG render_app gdf_filtered: {gdf_filtered.shape} {gdf_filtered.crs.name}')
        else:
            print(f'$$$$DEBUG render_app gdf_filtered: EMPTY')
    
    if not selected_properties:
        render_map_state(gdf_filtered)
    else:
        render_data_state(gdf_filtered, selected_properties)

###############################################
# Map State - if no properties selected
###############################################

def render_map_state(gdf_filtered):
    """Render the map selection state"""
    st.title("Property Data Explorer")
    st.markdown("Draw a polygon on the map to select properties")
    
    selection_count = st.session_state.get("map_selection_count", 0)
    selected_polygon = render_selection_map(gdf_filtered, key=f"main_selection_map_{selection_count}")
    
    with st.sidebar:
        add_savills_logo()
        st.divider()
        
        if st.button("📊 View Data", type="primary", width='stretch'):
            if selected_polygon is not None:
                mask = gdf_filtered.intersects(selected_polygon)
                filtered_props = gdf_filtered[mask][SSDB_REF_COLUMN].tolist()
                add_selected_properties(filtered_props)
                st.rerun()
            else:
                st.error("Please draw a polygon on the map first")
        
        if st.button("🗑️ Clear Polygon", width='stretch'):
            st.session_state.map_selection_count = selection_count + 1
            st.rerun()
    
    if selected_polygon is not None:
        st.session_state.last_drawn_polygon = selected_polygon

def render_sidebar_conditional(gdf_filtered, selected_properties):
    """Render conditional sidebar elements and return selected view info"""
    # result will comprise display name, col name   OR None
    result = render_conditional_sidebar(gdf_filtered, selected_properties)
    if result and len(result) == 2:
        return result[0], result[1]
    return None, None

###############################################
# Data State - if properties have been selected
###############################################

def render_data_state(gdf_filtered, selected_properties):
    """Render the data view state with tabs"""

    if DEBUG:
        print('*'*20)
        print('$$$$DEBUG')
        print(gdf_filtered.head(2))
        print('*'*20)

    # Sidebar - get selected view
    with st.sidebar:
        add_savills_logo()
        result = render_conditional_sidebar(gdf_filtered, selected_properties)
        if result and len(result) == 2:
            selected_view_display_name, selected_value_col = result
        else:
            selected_view_display_name = None
            selected_value_col = None
    
    # Tabs
    tab_graph, tab_selected_stores = st.tabs(["📈 Graph", "📋 Selected Stores"])
    
    with tab_graph:
        if selected_properties and selected_view_display_name and selected_value_col:
            display_data_graph(selected_view_display_name, 
                               selected_properties, 
                               value_col=selected_value_col)
        else:
            st.info("Select properties from the map and a data view from the sidebar to display graphs")
    
    with tab_selected_stores:
        if gdf_filtered is not None and selected_properties:
            display_selected_stores_table(selected_properties, gdf_filtered)
        elif gdf_filtered is None:
            st.warning("No properties match criteria")
        else:
            st.info("No stores selected")

