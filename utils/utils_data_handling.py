import streamlit as st

from config.config_constants import (SS_ACTIVE_REFS, DEBUG, 
                                     SS_SELECTED_PROPS,
                                     GDF_SS_NAME, SSDB_STORENAME_ADDITION_COLUMN,
                                    SSDB_REF_COLUMN, STORENAME_COLUMN
                                    )


def clear_ssdb_ref_data():
    """Clear all SSDB reference data from session state"""
    if SS_ACTIVE_REFS in st.session_state:
        st.session_state[SS_ACTIVE_REFS] = set()
    if SS_SELECTED_PROPS in st.session_state:
        st.session_state[SS_SELECTED_PROPS] = []


def add_ssdb_ref_values(new_values):
    """
    Add new SSDB_REF values to the active set (ensuring uniqueness)
    
    Args:
        new_values: list or set of SSDB_REF values to add
    """
    if SS_ACTIVE_REFS not in st.session_state:
        st.session_state[SS_ACTIVE_REFS] = set()
    
    if isinstance(new_values, (list, set)):
        st.session_state[SS_ACTIVE_REFS].update(new_values)
    else:
        st.session_state[SS_ACTIVE_REFS].add(new_values)


def get_list_of_ssdb_ref_data():
    """Return the current list of active SSDB_REF values"""
    if SS_ACTIVE_REFS in st.session_state:
        return list(st.session_state[SS_ACTIVE_REFS])
    return []


def add_selected_properties(property_refs):
    """
    Add property references to selected_properties_list (ensuring uniqueness)
    
    Args:
        property_refs: list or set of SSDB_REF values from polygon selection
    """
    if SS_SELECTED_PROPS not in st.session_state:
        st.session_state[SS_SELECTED_PROPS] = []
    
    current_set = set(st.session_state[SS_SELECTED_PROPS])
    current_set.update(property_refs)
    st.session_state[SS_SELECTED_PROPS] = list(current_set)


def clear_selected_properties():
    """Clear the selected properties list"""
    if SS_SELECTED_PROPS in st.session_state:
        st.session_state[SS_SELECTED_PROPS] = []


def get_selected_properties():
    """Return the current selected properties list"""
    if SS_SELECTED_PROPS in st.session_state:
        return st.session_state[SS_SELECTED_PROPS]
    return []

def get_selected_properties_count():
    """Return the count of selected properties"""
    props = get_selected_properties()
    return len(props)

def remove_properties(properties_to_remove):
    """Remove properties from session_state"""
    current_props = get_selected_properties()
    updated_props = [p for p in current_props if p not in properties_to_remove]
    st.session_state[SS_SELECTED_PROPS] = updated_props
    return updated_props

def get_filtered_geodataframe():
    """Return the filtered geodataframe from session_state"""
    return st.session_state.get(GDF_SS_NAME, None)

def enhance_storename_with_gdf(df_selected):
    """
    Enhance the storename column from data dfs by joining with GDF to get better store names.
    If ssdb_storename exists from GDF, use it; otherwise keep existing storename.
    """
    if df_selected is None or df_selected.empty:
        return df_selected
    
    # Check if GDF exists in session_state
    if GDF_SS_NAME not in st.session_state:
        if DEBUG:
            print(f"$$$$$DEBUG enhance_storename_with_gdf: {GDF_SS_NAME} not found in session_state")
        return df_selected
    
    gdf_ssdb = st.session_state[GDF_SS_NAME]
    
    # Check if GDF has storename column
    if STORENAME_COLUMN not in gdf_ssdb.columns:
        if DEBUG:
            print(f"$$$$DEBUG enhance_storename_with_gdf: {STORENAME_COLUMN} not found in gdf_ssdb")
        return df_selected
    
    # Create mapping from ssdb_ref to storename from GDF (keep first occurrence only)
    storename_mapping = gdf_ssdb[[SSDB_REF_COLUMN, STORENAME_COLUMN]].copy()
    # Makes sure there are no duplicates - which there should not be
    storename_mapping = storename_mapping.drop_duplicates(subset=[SSDB_REF_COLUMN, STORENAME_COLUMN])
    # Rename so that there is no conflict on the merge
    storename_mapping.rename(columns={STORENAME_COLUMN: SSDB_STORENAME_ADDITION_COLUMN}, inplace=True)
    
    # Merge the enhanced storename into df_selected
    df_enhanced = df_selected.merge(storename_mapping, on=SSDB_REF_COLUMN, how='left')
    
    # Create final storename column: use ssdb_storename if available, otherwise existing storename
    if SSDB_STORENAME_ADDITION_COLUMN in df_enhanced.columns:
        df_enhanced[STORENAME_COLUMN] = df_enhanced[SSDB_STORENAME_ADDITION_COLUMN].fillna(df_enhanced[STORENAME_COLUMN])
        # Drop the temporary column only if it exists
        df_enhanced = df_enhanced.drop(columns=[SSDB_STORENAME_ADDITION_COLUMN])
    
    if DEBUG:
        print(f"$$$$DEBUG enhance_storename_with_gdf: Enhanced storename column. Unique stores: {df_enhanced[STORENAME_COLUMN].nunique()}")
    
    return df_enhanced