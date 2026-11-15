import streamlit as st
import pandas as pd
import json
import os

TRANSAKSI_COLUMNS = [
    "ID",
    "Tanggal",
    "Minggu",
    "Team/Promotor",
    "Merk Rokok",
    "Stok Awal",
    "Stok Akhir",
    "Belum Selesai",
    "Rokok Lain-lain",
    "Terjual",
    "Harga Kanvas",
    "Harga Konsumen",
    "Total Setoran Kanvas",
    "Total Setoran",
]

BON_COLUMNS = [
    "ID",
    "Tanggal",
    "Team/Promotor",
    "Merk Rokok",
    "Ball",
    "Slop",
    "Bungkus",
    "Total Setara Bungkus",
    "Keperluan",
    "Keterangan",
]


def init_session_state():
    """Initialize empty transaction and bon tables for the current Streamlit session."""
    if "df_transaksi" not in st.session_state:
        st.session_state.df_transaksi = pd.DataFrame(columns=TRANSAKSI_COLUMNS)

    if "df_bon" not in st.session_state:
        st.session_state.df_bon = pd.DataFrame(columns=BON_COLUMNS)


def load_master_harga():
    # Cek apakah file berada di dalam folder reportspg/ atau di root
    possible_paths = [
        "master_harga_rokok.json",
        os.path.join("administrasi rokok", "master_harga_rokok.json"),
    ]

    for path in possible_paths:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)

    # Fallback jika benar-benar tidak ketemu
    return [
        {"merk": "D 76 12", "harga_kanvas": 15500, "ball": 1, "slop": 20, "bungkus": 200},
        {"merk": "LA Bold 16", "harga_kanvas": 29300, "ball": 1, "slop": 10, "bungkus": 100},
    ]
