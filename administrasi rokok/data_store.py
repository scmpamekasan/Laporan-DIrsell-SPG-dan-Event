import streamlit as st
import pandas as pd
import json
import os

MASTER_HARGA_FILE = "master_harga_rokok.json"

def load_master_harga():
    if os.path.exists(MASTER_HARGA_FILE):
        with open(MASTER_HARGA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    else:
        # Fallback dummy data jika file belum ada
        return [
            {"merk": "D 76 12", "harga_kanvas": 15500, "ball": 1, "slop": 20, "bungkus": 200},
            {"merk": "LA Bold 16", "harga_kanvas": 29300, "ball": 1, "slop": 10, "bungkus": 100}
        ]

def init_session_state():
    # Inisialisasi DataFrame Transaksi Utama
    if "df_transaksi" not in st.session_state:
        st.session_state.df_transaksi = pd.DataFrame(columns=[
            "ID", "Tanggal", "Minggu", "Team/Promotor", "Merk Rokok", 
            "Stok Awal", "Stok Akhir", "Belum Selesai", 
            "Bon Qty", "Keperluan Bon", "Terjual", 
            "Harga Kanvas", "Harga Konsumen", "Total Setoran Kanvas", "Total Setoran Konsumen"
        ])

    # Inisialisasi DataFrame Bon Rokok Terperinci
    if "df_bon" not in st.session_state:
        st.session_state.df_bon = pd.DataFrame(columns=[
            "ID", "Tanggal", "Team/Promotor", "Merk Rokok", "Jumlah Bon", "Keperluan", "Keterangan"
        ])
