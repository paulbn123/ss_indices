import streamlit as st

from utils.utils_data_handling import (clear_selected_properties, get_selected_properties_count)
from config.config_constants import (DATA_DICT, DEBUG,
                                     GDF_SS_NAME, SSDB_REF_COLUMN)

def render_conditional_sidebar(gdf_filtered, selected_properties):
    """Render sidebar based on whether properties are selected.

    If properties have been selected then it will return:
    either:
        selected_display_name - the name of the data factor in the radio list 
        selected_value_col - the name of the column in the df 

        Comes from Data_dict:
        ss_name (<<fname>>, <<display_name>>, data_type) - the column name is the filename excl. '.parquet' 

    or: 

        None

    """
       
    # Show metrics -  if required
    active_refs = st.session_state.get("active_ssdb_refs", set())
    # st.metric("Active Properties", len(active_refs))
    
    if gdf_filtered is not None:
        # st.metric("Data Points", len(gdf_filtered))
        if DEBUG:
            gdf_full = st.session_state.get(GDF_SS_NAME)
            if gdf_full is not None and SSDB_REF_COLUMN in gdf_full.columns:
                active_not_in_gdf = set(active_refs - set(gdf_full[SSDB_REF_COLUMN].unique()))
                if active_not_in_gdf:
                    print(f"$$$$DEBUG - {len(active_not_in_gdf)} active refs missing from GDF entirely: {active_not_in_gdf}")

    # Show this instead as the table header    
    # selected_count = get_selected_properties_count()
    # st.metric("Selected Properties", selected_count)
    st.divider()
    
    if selected_properties:
        
        # Radio buttons for data selection (exclude 'ssdb')
        data_options = {}
        for k, v in DATA_DICT.items():
            if k != 'ssdb' and v[1] != 'SSDB':
                filename = v[0]  # e.g., 'ebitda.parquet'
                value_col = filename.replace('.parquet', '')  # e.g., 'ebitda'
                display_name = v[1]  # e.g., 'EBITDA'
                data_options[k] = (display_name, value_col)
        
        selected_view_key = st.radio(
            "Select data to display:",
            options=list(data_options.keys()),
            format_func=lambda x: data_options[x][0],  # Show display_name
            key="selected_data_view"
        )
        
        # Get display name and value column
        selected_display_name, selected_value_col = data_options[selected_view_key]
        
        st.divider()

        selected_count = len(selected_properties)
        st.write(f"Selected stores ({selected_count})")

        # STATE: Properties selected
        if st.button("🗺️ Back to Map Selection", width='content'):
            st.session_state.map_selection_count = 0
            clear_selected_properties()
            st.rerun()
        

        return selected_display_name, selected_value_col
    
    else:
        # STATE: No properties selected - Show map controls
        selection_count = st.session_state.get("map_selection_count", 0)
        
        if st.button("📊 View Data", type="primary", width='content'):
            return "view_data_clicked"
        
        if st.button("🗑️ Clear Polygon", width='content'):
            st.session_state.map_selection_count = selection_count + 1
            st.rerun()
        
        return None