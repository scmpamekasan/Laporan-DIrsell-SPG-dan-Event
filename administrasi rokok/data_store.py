import json
import os

import pandas as pd
import streamlit as st


def _master_file_path():
    """Return the master JSON path in the same folder as this module."""
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "master_harga_rokok.json")


def load_master_harga():
    """Baca data master rokok dari JSON. Jika file tidak ada / rusak, buat file default."""
    file_path = _master_file_path()
    default_data = [
        {"merk": "Black Matcha K12", "harga_kanvas": 15000, "harga_konsumen": 18000, "ball": 1, "slop": 20, "bungkus": 200},
        {"merk": "D.Super 12", "harga_kanvas": 21000, "harga_konsumen": 25000, "ball": 1, "slop": 20, "bungkus": 200},
        {"merk": "D.76 Apel Royal", "harga_kanvas": 12000, "harga_konsumen": 15000, "ball": 1, "slop": 20, "bungkus": 200},
        {"merk": "D.76 Apel", "harga_kanvas": 12000, "harga_konsumen": 15000, "ball": 1, "slop": 20, "bungkus": 200},
        {"merk": "Djarum 76 Aksara", "harga_kanvas": 11000, "harga_konsumen": 14000, "ball": 1, "slop": 20, "bungkus": 200},
        {"merk": "Djarum Black Siro", "harga_kanvas": 22000, "harga_konsumen": 26000, "ball": 1, "slop": 20, "bungkus": 200},
        {"merk": "Djarum Black Kuro", "harga_kanvas": 22000, "harga_konsumen": 26000, "ball": 1, "slop": 20, "bungkus": 200},
    ]

    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list) and all(isinstance(item, dict) and str(item.get("merk", "")).strip() for item in data):
                return data
        except (OSError, json.JSONDecodeError) as e:
            st.error(f"⚠️ Gagal membaca file `master_harga_rokok.json`: {e}")

    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(default_data, f, indent=4, ensure_ascii=False)
    except OSError as e:
        st.error(f"⚠️ Gagal membuat file `master_harga_rokok.json`: {e}")

    return default_data


def save_master_harga(master_data):
    """Simpan data master ke file JSON."""
    file_path = _master_file_path()
    try:
        clean_data = [dict(item) for item in master_data]
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(clean_data, f, indent=4, ensure_ascii=False)
        return True
    except (OSError, TypeError) as e:
        st.error(f"⚠️ Gagal menyimpan file `master_harga_rokok.json`: {e}")
        return False


def init_session_state():
    """Initialize session state for app tables."""
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

    if "master_rokok_data" not in st.session_state:
        st.session_state.master_rokok_data = load_master_harga()

    if "is_data_loaded" not in st.session_state:
        st.session_state.is_data_loaded = False

    if "trx_form_reset_id" not in st.session_state:
        st.session_state.trx_form_reset_id = 0

    if "pre_form_reset_id" not in st.session_state:
        st.session_state.pre_form_reset_id = 0

    if "jumlah_baris_pre" not in st.session_state:
        st.session_state.jumlah_baris_pre = 5

    if "df_pre_entry_bon" in st.session_state and "Rencana Penyelesaian" not in st.session_state.df_pre_entry_bon.columns:
        st.session_state.df_pre_entry_bon["Rencana Penyelesaian"] = str(__import__("datetime").datetime.now().date())
