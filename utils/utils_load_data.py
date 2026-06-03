import streamlit as st
import pandas as pd
import geopandas as gpd
import os

from config.config_constants import (DATA_DIR, SSDB_REF_COLUMN, 
                                     GDF_SS_NAME, SS_ACTIVE_REFS, 
                                     SS_DATA_LOADED, DEBUG)
from utils.utils_security import load_encrypted_parquet


@st.cache_data
def initial_data_load(data_dict, password):
    """
    Load all encrypted data files from DATA_DIR based on DATA_DICT.
    Returns:
        - loaded_data: dict with session_state keys as keys and dataframes/gdfs as values
        - active_refs: set of unique SSDB_REF values from data files
    """
    loaded_data = {}
    active_refs = set()
    
    for ss_key, (filename, display_name, data_type) in data_dict.items():
        file_path = os.path.join(DATA_DIR, filename)
        
        try:
            # Universal load for both df and gdf
            loaded = load_encrypted_parquet(file_path, password)
            
            loaded_data[ss_key] = loaded
            
            # Extract SSDB_REF values from data files only (skip the GDF)
            if ss_key == GDF_SS_NAME:
                pass  # Skip - this is the geodataframe
            elif SSDB_REF_COLUMN in loaded.columns:
                active_refs.update(loaded[SSDB_REF_COLUMN].unique().tolist())
            else:
                st.error(f"Required column '{SSDB_REF_COLUMN}' not found in {display_name}")
                
                if DEBUG:
                    print(f"&&&&DEBUG: initial_data_load: missing {SSDB_REF_COLUMN} column from {display_name}")
                    print(f"&&&&DEBUG: Available columns: {loaded.columns.tolist()}")
                        
        except FileNotFoundError:
            st.warning(f"File not found: {file_path}")
            loaded_data[ss_key] = None
        except Exception as e:
            st.error(f"Error loading {filename}: {e}")
            loaded_data[ss_key] = None
    
    return loaded_data, active_refs


def init_session_state(data_dict, password):
    """Initialize session state with loaded data and filtered geodataframe"""
    
    # Load all data if not already loaded
    if SS_DATA_LOADED not in st.session_state or not st.session_state[SS_DATA_LOADED]:
        loaded_data, active_refs = initial_data_load(data_dict, password)
        
        if DEBUG:
            print(f"&&&&DEBUG: init_session_state Loaded {len(loaded_data)} items from data_dict")
            print(f"&&&&DEBUG: init_session_state Active refs found: {len(active_refs)}")
        
        # Store loaded data in session_state
        df_count = 0
        gdf_count = 0
        
        for ss_key, data in loaded_data.items():
            if data is not None:
                st.session_state[ss_key] = data
                
                if DEBUG:
                    if isinstance(data, gpd.GeoDataFrame):
                        gdf_count += 1
                        print(f"&&&&DEBUG:init_session_state Added GeoDataFrame '{ss_key}' with {len(data)} rows, CRS: {data.crs}")
                    else:
                        df_count += 1
                        print(f"&&&&DEBUG: init_session_state Added DataFrame '{ss_key}' with {len(data)} rows")
            else:
                if DEBUG:
                    print(f"&&&&DEBUG: init_session_state '{ss_key}' data is None - not added to session_state")
        
        if DEBUG:
            print(f"&&&&DEBUG: init_session_state Total added - {df_count} DataFrames, {gdf_count} GeoDataFrames")
            print(f"&&&&DEBUG: init_session_state Session_state keys after load: {list(st.session_state.keys())}")
        
        # Store active refs
        st.session_state[SS_ACTIVE_REFS] = active_refs
        
        # Filter the geodataframe using active refs
        if GDF_SS_NAME in st.session_state and st.session_state[GDF_SS_NAME] is not None:
            gdf_full = st.session_state[GDF_SS_NAME]
            
            if DEBUG:
                print(f"&&&&DEBUG: init_session_state Filtering GDF '{GDF_SS_NAME}' with {len(gdf_full)} rows")
            
            # Check column exists before filtering
            if SSDB_REF_COLUMN not in gdf_full.columns:
                st.warning(f"Column '{SSDB_REF_COLUMN}' not found in geodataframe. Using full dataset.")
                gdf_filtered = gdf_full
            elif active_refs:
                gdf_filtered = gdf_full[gdf_full[SSDB_REF_COLUMN].isin(active_refs)]
                if DEBUG:
                    print(f"&&&&DEBUG: init_session_state Filtered GDF from {len(gdf_full)} to {len(gdf_filtered)} rows")
            else:
                gdf_filtered = gdf_full.head(1000)  # fallback to first 1k points
                if DEBUG:
                    print(f"&&&&DEBUG: init_session_state No active refs - using full GDF ({len(gdf_filtered)} rows)")
                
            st.session_state[GDF_SS_NAME] = gdf_filtered
        
        st.session_state[SS_DATA_LOADED] = True

