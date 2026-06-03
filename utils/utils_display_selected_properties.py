import streamlit as st

from utils.utils_data_handling import remove_properties
from utils.utils_data_graphing import display_data_graph


from config.config_constants import (DEBUG, SSDB_REF_COLUMN,
                                    DF_DISPLAY_COLS)


## This module adds the data from the selected properties to the two tabs on the main page when there are selected properties


def display_selected_stores_graph(selected_view_display_name, selected_properties, value_col):

        if selected_properties and selected_view_display_name:
            display_data_graph(selected_view_display_name, selected_properties, value_col)
        else:
            st.info("Select properties from the map and a data view from the sidebar to display graphs")
    
def display_selected_stores_table(selected_properties, gdf_filtered):
    """Display selected stores table with remove functionality"""
    
    
    if gdf_filtered is not None and selected_properties:
        # Use passed selected_properties, not get_selected_properties()
        selected_gdf = gdf_filtered[gdf_filtered[SSDB_REF_COLUMN].isin(selected_properties)]
        
        # Create a copy for display
        display_df = selected_gdf[DF_DISPLAY_COLS].copy()
        
        # Add checkbox column
        display_df.insert(0, "Remove", False)
        
        # Display with edited data
        edited_df = st.data_editor(
            display_df,
            width='stretch',
            hide_index=True,
            column_config={
                "Remove": st.column_config.CheckboxColumn(
                    "Remove",
                    help="Check stores to remove",
                    default=False,
                )
            },
            disabled=[col for col in display_df.columns if col != "Remove"],
            key="store_removal_editor"
        )
        
        # Remove button
        if st.button("Remove Selected Stores", type="primary"):
            to_remove = edited_df[edited_df["Remove"] == True][SSDB_REF_COLUMN].tolist()
            
            if to_remove:
                # This function should modify session_state
                remove_properties(to_remove)
                st.success(f"Removed {len(to_remove)} stores")
                st.rerun()
            else:
                st.warning("No stores selected for removal")

    elif gdf_filtered is not None and not selected_properties:
        st.info("No stores selected. Use the map or sidebar to select stores.")
    else:
        st.warning("No filtered geodataframe available")