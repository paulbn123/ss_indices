import streamlit as st

import os
from utils.utils_security import load_encrypted_parquet
from config.config_constants import DATA_DICT, DATA_DIR, DEBUG, SS_DATA_LOADED
from utils.utils_load_data import init_session_state

def verify_password():
    """Handle password verification form. Returns True if password is verified."""
    
    with st.form("password_form"):
        password = st.text_input("Enter decryption password:", type="password")
        submitted = st.form_submit_button("Submit")
        
        if submitted:
            if not password:
                st.error("Please enter a password")
                return False
            else:
                # Get test file path
                test_file = os.path.join(DATA_DIR, list(DATA_DICT.values())[0][0])
                
                if DEBUG:
                    print(f'test_file: {test_file}')
                
                # Check if file exists first
                if not os.path.exists(test_file):
                    st.error(f"Data file not found: {test_file}. Please check installation.")
                    return False
                
                # Test password
                try:
                    load_encrypted_parquet(test_file, password)
                    st.session_state.decrypt_password = password
                    st.success("Password verified! Loading data...")
                    return True
                except Exception as e:
                    st.error(f"Incorrect password or corrupted file: {e}")
                    return False
    return False

def initialize_app():
    """Initialize session state with loaded data. Returns True if successful."""
    if "decrypt_password" not in st.session_state:
        return False
    
    if SS_DATA_LOADED not in st.session_state or not st.session_state[SS_DATA_LOADED]:
        try:
            init_session_state(DATA_DICT, st.session_state.decrypt_password)
            st.session_state.initialized = True
            return True
        except Exception as e:
            st.error(f"Failed to load data: {e}")
            # Clear password to force retry
            del st.session_state.decrypt_password
            return False
    
    return True

def check_password_and_initialize():
    """Main entry point for app initialization. Returns True if app should continue."""
    
    # No password - show form
    if "decrypt_password" not in st.session_state:
        if verify_password():
            st.rerun()
        return False
    
    # Has password but not initialized - try to initialize
    if "initialized" not in st.session_state:
        if not initialize_app():
            return False
    
    return True