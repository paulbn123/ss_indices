import streamlit as st
import os


# ============================================
# CONSTANTS
# ============================================

DEBUG = True


DATA_DIR = os.path.join('assets', 'import_data')
GDF_SS_NAME = 'ssdb'

# List all data (excluding the gdf_ssdb file)
# This comprise dictionary of key = ss_name (fname, display_name, data_type) 
DATA_DICT = {
    'ebitda': ('ebitda.parquet', 'EBITDA', 'line_total'), 
    'ebitdar': ('ebitdar.parquet', 'EBITDAR', 'line_total'), 
    'occ_area_ann': ('occ_area_ann.parquet', 'Occ Area (Ann)', 'occupancy'),
    'occ_area_mth': ('occ_area_mth.parquet', 'Occ Area (Mth)', 'occupancy'), 
    'occ_perc_ann': ('occ_perc_ann.parquet', 'Occ Perc CLA (Ann)', 'occupancy'), 
    'occ_perc_mth': ('occ_perc_mth.parquet', 'Occ Perc CLA (Mth)', 'occupancy'), 
    'opex_marketing': ('opex_marketing.parquet', 'Opex Marketing', 'opex'), 
    'opex_rates': ('opex_rates.parquet', 'Opex Rates', 'opex'), 
    'opex_rent': ('opex_rent.parquet', 'Opex Rent', 'opex'), 
    'opex_staff': ('opex_staff.parquet', 'Opex Staff', 'opex'), 
    'opex_utils': ('opex_utils.parquet', 'Operating Utils', 'opex'), 
    'opex_total': ('opex_total.parquet', 'Total Opex', 'line_total'), 
    # The new CLA lines
    'opex_marketing_per_CLA': ('opex_marketing_per_CLA.parquet', 'Opex Marketing', 'opex'), 
    'opex_rates_per_CLA': ('opex_rates_per_CLA.parquet', 'Opex Rates psf', 'opex'), 
    'opex_rent_per_CLA': ('opex_rent_per_CLA.parquet', 'Opex Rent psf', 'opex'), 
    'opex_staff_per_CLA': ('opex_staff_per_CLA.parquet', 'Opex Staff psf', 'opex'), 
    'opex_utils_per_CLA': ('opex_utils_per_CLA.parquet', 'Operating Utils psf', 'opex'), 
    'opex_total_per_CLA': ('opex_total_per_CLA.parquet', 'Total Opex psf', 'opex'), 
    #
    
    'rent_ann': ('rent_ann.parquet', 'Annual Rent', 'rent'), 
    'rent_mth': ('rent_mth.parquet', 'Monthly Rent', 'rent'), 
    'rev_bulk': ('rev_bulk.parquet', 'Bulk Rev', 'revenue'), 
    'rev_ins': ('rev_ins.parquet', 'Ins Rev', 'revenue'), 
    'rev_merch': ('rev_merch.parquet', 'Merch Rev', 'revenue'), 
    'rev_ss': ('rev_ss.parquet', 'Self Storage Rev', 'revenue'), 
    'rev_total': ('rev_total.parquet', 'Total Rev', 'line_total'),
    'ssdb': ('gdf_ssdb.parquet', 'SSDB', 'geodataframe')
}

# Column names
SSDB_REF_COLUMN = 'ssdb_ref'
DATE_COLUMN = 'date'
STORENAME_COLUMN = 'storename'
SSDB_STORENAME_ADDITION_COLUMN = 'ssdb_storename'

# Cols names for selected stores
DF_DISPLAY_COLS = [SSDB_REF_COLUMN, STORENAME_COLUMN, 'address', 'city', 'ss_type', 'store_cla_sqft']


# Session state keys
SS_ACTIVE_REFS = "active_ssdb_refs"
SS_SELECTED_PROPS = "selected_properties_list"
SS_DATA_LOADED = "data_loaded"


# Graphing constants
MAX_LABELS_TO_SHOW_ON_GRAPH  = 10
