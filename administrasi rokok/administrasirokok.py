import streamlit as st

def setup_page_config():
    st.set_page_config(
        page_title="Administrasi Stok & Penjualan Rokok",
        page_icon="🚬",
        layout="wide",
        initial_sidebar_state="expanded"
    )

def apply_custom_styling():
    st.markdown("""
        <style>
            /* Tema Background Warm Cream & Kartu Putih Bersih */
            .stApp {
                background-color: #FDFBF7;
                color: #2C2C2C;
            }
            
            /* Sidebar Styling */
            [data-testid="stSidebar"] {
                background-color: #F4EEDC;
                border-right: 1px solid #E6DFCD;
            }

            /* Kartu Dashboard / Metric Card */
            .metric-card {
                background-color: #FFFFFF;
                border: 1px solid #E6DFCD;
                border-radius: 10px;
                padding: 18px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.02);
                text-align: center;
            }
            
            /* Header Styling */
            h1, h2, h3 {
                color: #1A1A1A;
            }
        </style>
    """, unsafe_allow_html=True)
