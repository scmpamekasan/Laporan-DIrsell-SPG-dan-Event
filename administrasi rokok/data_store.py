import streamlit as st
import pandas as pd
import json
import os

def load_master_harga():
    """
    Memuat data master harga dan satuan dari file 'master_harga_rokok.json'.
    Jika file belum ada, akan menggunakan data default dan membuat file JSON tersebut secara otomatis.
    """
    file_path = "master_harga_rokok.json"
    default_data = [
        {"merk": "Black Matcha K12", "harga_kanvas": 15000, "harga_konsumen": 18000, "ball": 1, "slop": 20, "bungkus": 200},
        {"merk": "D.Super 12", "harga_kanvas": 21000, "harga_konsumen": 25000, "ball": 1, "slop": 20, "bungkus": 200},
        {"merk": "D.76 Apel Royal", "harga_kanvas": 12000, "harga_konsumen": 15000, "ball": 1, "slop": 20, "bungkus": 200},
        {"merk": "D.76 Apel", "harga_kanvas": 12000, "harga_konsumen": 15000, "ball": 1, "slop": 20, "bungkus": 200},
        {"merk": "Djarum 76 Aksara", "harga_kanvas": 11000, "harga_konsumen": 14000, "ball": 1, "slop": 20, "bungkus": 200},
        {"merk": "Djarum Black Siro", "harga_kanvas": 22000, "harga_konsumen": 26000, "ball": 1, "slop": 20, "bungkus": 200},
        {"merk": "Djarum Black Kuro", "harga_kanvas": 22000, "harga_konsumen": 26000, "ball": 1, "slop": 20, "bungkus": 200}
    ]
    
    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list) and len(data) > 0:
                    return data
        except Exception:
            pass
            
    # Jika file belum ada atau kosong, buat file default-nya
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(default_data, f, indent=4)
    except Exception:
        pass
        
    return default_data

def save_master_harga(master_data):
    """
    Menyimpan perubahan master harga ke file 'master_harga_rokok.json'.
    """
    file_path = "master_harga_rokok.json"
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(master_data, f, indent=4)
        return True
    except Exception:
        return False

def init_session_state():
    """
    Menginisialisasi variabel-variabel default di st.session_state jika belum ada.
    """
    if "df_transaksi" not in st.session_state:
        st.session_state.df_transaksi = pd.DataFrame(columns=[
            "ID", "No Bon", "Tanggal", "Minggu", "Team/Promotor", "Merk Rokok", 
            "Stock Awal", "Stock Akhir", "Belum Selesai", "Rokok Lain-lain", 
            "Terjual", "Harga Kanvas", "Harga Konsumen", "Total Setoran Kanvas", "Total Setoran"
        ])

    if "df_bon" not in st.session_state:
        st.session_state.df_bon = pd.DataFrame(columns=[
            "ID", "Tanggal", "Team/Promotor", "Merk Rokok", "Ball", "Slop", "Bungkus", 
            "Total Setara Bungkus", "Keperluan", "Keterangan"
        ])

    if "df_pre_entry_bon" not in st.session_state:
        st.session_state.df_pre_entry_bon = pd.DataFrame(columns=[
            "ID Draft", "Tanggal", "Rencana Penyelesaian", "Team/Promotor", "Merk Rokok", 
            "Ball", "Slop", "Bungkus", "Total Setara Bungkus", "Keperluan", "Keterangan"
        ])

    if "df_penyelesaian_gudang" not in st.session_state:
        st.session_state.df_penyelesaian_gudang = pd.DataFrame(columns=[
            "ID Penyelesaian", "Tanggal", "Team/Promotor", "Merk Rokok", "Jumlah Bungkus", "Keterangan"
        ])
