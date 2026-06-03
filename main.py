import streamlit as st
import os

from utils.utils_initialization import check_password_and_initialize
from utils.utils_render_app import render_app

##################################################################
##############MAIN APPLICATION CONFIG    #########################
st.set_page_config(
    page_title="Property Data Explorer",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)
###################################################################
###################################################################


# ============================================
# INITIALIZATION (runs once)
# ============================================

# Handle password verification ==>> Data load in utils_initialization
if not check_password_and_initialize():
    st.stop()

# ============================================
# IF INITIALISED CORRECTLY RENDER THE APP
# ============================================

render_app()