import streamlit as st
import pandas as pd
import json
import os


def _master_file_path():
    """Return the JSON path alongside this module."""
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "master_harga_rokok.json")


def _master_file_signature():
    """Return a signature that changes when the JSON file is updated."""
    try:
        stat = os.stat(_master_file_path())
        return (stat.st_mtime_ns, stat.st_size)
    except OSError:
        return None


def load_master_harga():
    """
    Muat data master dari master_harga_rokok.json di folder yang sama.
    """
    file_path = _master_file_path()

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
            if isinstance(data, list) and all(isinstance(item, dict) and item.get("merk") for item in data):
                return data
            st.error("⚠️ Format master_harga_rokok.json tidak valid. Pastikan isinya berupa daftar objek dengan kolom 'merk'.")
        except (OSError, json.JSONDecodeError) as e:
            st.error(f"⚠️ Gagal membaca file `master_harga_rokok.json`: {e}")

    # Buat file default hanya jika belum ada atau file tidak dapat dibaca.
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(default_data, f, indent=4, ensure_ascii=False)
    except OSError as e:
        st.error(f"⚠️ Gagal membuat file master_harga_rokok.json: {e}")

    return default_data


def save_master_harga(master_data):
    """Simpan perubahan master ke master_harga_rokok.json."""
    try:
        with open(_master_file_path(), "w", encoding="utf-8") as f:
            json.dump(master_data, f, indent=4, ensure_ascii=False)
        return True
    except (OSError, TypeError) as e:
        st.error(f"⚠️ Gagal menyimpan file JSON: {e}")
        return False


def _sync_master_file():
    """
    Sinkronkan session state dengan file:
    - file berubah di luar aplikasi: baca ulang file agar dropdown merk ikut diperbarui;
    - session state berubah lewat UI: simpan perubahan ke JSON.
    """
    file_path = _master_file_path()
    current_signature = _master_file_signature()
    previous_signature = st.session_state.get("master_rokok_file_signature")

    # Pada sesi baru, JSON adalah sumber kebenaran. Ini juga mencegah data
    # lama yang tertinggal di session_state menimpa isi JSON yang lebih baru.
    if previous_signature is None or current_signature != previous_signature:
        st.session_state.master_rokok_data = load_master_harga()
        st.session_state.master_rokok_file_signature = _master_file_signature()
        return

    master_data = st.session_state.get("master_rokok_data")
    if not isinstance(master_data, list):
        st.session_state.master_rokok_data = load_master_harga()
        st.session_state.master_rokok_file_signature = _master_file_signature()
        return

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            saved_data = json.load(f)
    except (OSError, json.JSONDecodeError):
        saved_data = None

    # Add/edit dari sidebar terjadi sebelum rerun berikutnya. Persist perubahan
    # itu tanpa menimpa file bila file JSON sendiri baru saja berubah.
    if saved_data != master_data and save_master_harga(master_data):
        st.session_state.master_rokok_file_signature = _master_file_signature()


def init_session_state():
    """Inisialisasi data aplikasi dan sinkronkan master merk/harga."""
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

    _sync_master_file()
