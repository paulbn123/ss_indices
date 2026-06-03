import streamlit as st

import pandas as pd
import geopandas as gpd 

## This module covers all the file decryption from the saved assets

# Crpytography imports
from cryptography.fernet import Fernet
import base64
import hashlib
import io
from shapely import wkb



# Generate key from password
def get_key(password):
    # Fernet require 32-byte keys in URL safe base64 format
    return base64.urlsafe_b64encode(hashlib.sha256(password.encode()).digest())


def load_encrypted_parquet(path, password):
    key = get_key(password)
    f = Fernet(key)
    
    with open(path, 'rb') as file:
        encrypted = file.read()
    
    decrypted = f.decrypt(encrypted)
    buffer = io.BytesIO(decrypted)
    df = pd.read_parquet(buffer)
    
    # Convert geometry bytes to shapely objects
    if 'geometry' in df.columns:
        from shapely import wkb
        df['geometry'] = df['geometry'].apply(lambda x: wkb.loads(x) if x is not None else None)
        return gpd.GeoDataFrame(df, geometry='geometry',  crs=4326)
    return df


