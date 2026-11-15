import io
import json
import os
import uuid
from datetime import datetime, timedelta

import pandas as pd
import requests
import streamlit as st

from app_config import apply_custom_styling, setup_page_config
from data_store import init_session_state, load_master_harga, save_master_harga
from date_utils import format_date_indo, get_current_week_label

WEB_APP_URL = "https://script.google.com/macros/s/AKfycbxffkMrtnuezGBjgGYh6Bk3g0yADw0DZHSyxIliW_3_4_tHaCGwyKamKfLcVePLaj8/exec"


def refresh_master_rokok_data():
    """Muat ulang state master dari file JSON dan update variabel global UI."""
    st.session_state.master_rokok_data = load_master_harga()

    global master_rokok, list_merk, dict_master_detail
    master_rokok = st.session_state.master_rokok_data
    list_merk = [item["merk"] for item in master_rokok]
    dict_master_detail = {item["merk"]: item for item in master_rokok}


# Pastikan state master selalu ada dan terhubung ke JSON
init_session_state()
refresh_master_rokok_data()


def backup_to_google_sheets():
    try:
        if not WEB_APP_URL or "MASUKKAN_URL" in WEB_APP_URL:
            st.error("⚠️ URL Web App Google Apps Script belum diatur di dalam kode (`WEB_APP_URL`)!")
            return False, "URL belum diset."

        trx_data = []
        if not st.session_state.df_transaksi.empty:
            trx_data = [st.session_state.df_transaksi.columns.tolist()] + st.session_state.df_transaksi.astype(str).values.tolist()

        bon_data = []
        if not st.session_state.df_bon.empty:
            bon_data = [st.session_state.df_bon.columns.tolist()] + st.session_state.df_bon.astype(str).values.tolist()

        pre_data = []
        if not st.session_state.df_pre_entry_bon.empty:
            pre_data = [st.session_state.df_pre_entry_bon.columns.tolist()] + st.session_state.df_pre_entry_bon.astype(str).values.tolist()

        gudang_data = []
        if "df_penyelesaian_gudang" in st.session_state and not st.session_state.df_penyelesaian_gudang.empty:
            gudang_data = [st.session_state.df_penyelesaian_gudang.columns.tolist()] + st.session_state.df_penyelesaian_gudang.astype(str).values.tolist()

        payload = {
            "action": "backup",
            "transaksi": trx_data,
            "bon": bon_data,
            "pre_entry": pre_data,
            "penyelesaian_gudang": gudang_data,
        }

        response = requests.post(WEB_APP_URL, json=payload)
        result = response.json()

        if result.get("status") == "success":
            return True, "Data berhasil dibackup dan ditimpa (overwrite) ke Google Sheet!"
        return False, result.get("message", "Gagal backup.")
    except Exception as e:
        return False, f"Error koneksi: {e}"


def load_from_google_sheets():
    try:
        if not WEB_APP_URL or "MASUKKAN_URL" in WEB_APP_URL:
            return False, "URL Web App Google Apps Script belum diatur di dalam kode (`WEB_APP_URL`)!"

        payload = {"action": "load"}
        response = requests.post(WEB_APP_URL, json=payload)
        result = response.json()

        if result.get("status") == "success":
            db_data = result.get("data", {})

            trx_vals = db_data.get("transaksi", [])
            if len(trx_vals) > 1:
                df_trx_loaded = pd.DataFrame(trx_vals[1:], columns=trx_vals[0])
                if "Total Setoran Konsumen" in df_trx_loaded.columns and "Total Setoran" not in df_trx_loaded.columns:
                    df_trx_loaded = df_trx_loaded.rename(columns={"Total Setoran Konsumen": "Total Setoran"})
                num_cols_trx = [
                    "Stock Awal", "Stock Akhir", "Belum Selesai", "Rokok Lain-lain",
                    "Terjual", "Harga Kanvas", "Harga Konsumen", "Total Setoran Kanvas", "Total Setoran"
                ]
                for col in num_cols_trx:
                    if col in df_trx_loaded.columns:
                        df_trx_loaded[col] = pd.to_numeric(df_trx_loaded[col], errors="coerce").fillna(0)
                if "Total Setoran" not in df_trx_loaded.columns:
                    df_trx_loaded["Total Setoran"] = 0
                st.session_state.df_transaksi = df_trx_loaded
            else:
                st.session_state.df_transaksi = pd.DataFrame(columns=[
                    "ID", "No Bon", "Tanggal", "Minggu", "Team/Promotor", "Merk Rokok",
                    "Stock Awal", "Stock Akhir", "Belum Selesai", "Rokok Lain-lain",
                    "Terjual", "Harga Kanvas", "Harga Konsumen", "Total Setoran Kanvas", "Total Setoran"
                ])

            bon_vals = db_data.get("bon", [])
            if len(bon_vals) > 1:
                df_bon_loaded = pd.DataFrame(bon_vals[1:], columns=bon_vals[0])
                num_cols_bon = ["Ball", "Slop", "Bungkus", "Total Setara Bungkus"]
                for col in num_cols_bon:
                    if col in df_bon_loaded.columns:
                        df_bon_loaded[col] = pd.to_numeric(df_bon_loaded[col], errors="coerce").fillna(0)
                st.session_state.df_bon = df_bon_loaded
            else:
                st.session_state.df_bon = pd.DataFrame(columns=[
                    "ID", "Tanggal", "Team/Promotor", "Merk Rokok", "Ball", "Slop", "Bungkus",
                    "Total Setara Bungkus", "Keperluan", "Keterangan"
                ])

            pre_vals = db_data.get("pre_entry", [])
            if len(pre_vals) > 1:
                df_pre_loaded = pd.DataFrame(pre_vals[1:], columns=pre_vals[0])
                num_cols_pre = ["Ball", "Slop", "Bungkus", "Total Setara Bungkus"]
                for col in num_cols_pre:
                    if col in df_pre_loaded.columns:
                        df_pre_loaded[col] = pd.to_numeric(df_pre_loaded[col], errors="coerce").fillna(0)
                st.session_state.df_pre_entry_bon = df_pre_loaded
            else:
                st.session_state.df_pre_entry_bon = pd.DataFrame(columns=[
                    "ID Draft", "Tanggal", "Rencana Penyelesaian", "Team/Promotor", "Merk Rokok",
                    "Ball", "Slop", "Bungkus", "Total Setara Bungkus", "Keperluan", "Keterangan"
                ])

            gudang_vals = db_data.get("penyelesaian_gudang", [])
            if len(gudang_vals) > 1:
                df_gudang_loaded = pd.DataFrame(gudang_vals[1:], columns=gudang_vals[0])
                if "Jumlah Bungkus" in df_gudang_loaded.columns:
                    df_gudang_loaded["Jumlah Bungkus"] = pd.to_numeric(df_gudang_loaded["Jumlah Bungkus"], errors="coerce").fillna(0)
                st.session_state.df_penyelesaian_gudang = df_gudang_loaded
            else:
                st.session_state.df_penyelesaian_gudang = pd.DataFrame(columns=[
                    "ID Penyelesaian", "Tanggal", "Team/Promotor", "Merk Rokok", "Jumlah Bungkus", "Keterangan"
                ])

            return True, "Data berhasil ditarik dan dipulihkan dari Google Sheet!"
        return False, result.get("message", "Gagal memuat data.")
    except Exception as e:
        return False, f"Error koneksi: {e}"


# --- app setup ---
setup_page_config()
apply_custom_styling()

# existing app code continues below...
# add + edit master section should use refresh_master_rokok_data() and save_master_harga()

# Add this right after the initial app state is created:
if "master_rokok_data" not in st.session_state:
    st.session_state.master_rokok_data = load_master_harga()
refresh_master_rokok_data()

# In the form add merk block:
#   st.session_state.master_rokok_data.append({...})
#   if save_master_harga(st.session_state.master_rokok_data):
#       refresh_master_rokok_data()
#       st.session_state.trx_form_reset_id += 1
#       st.success(...)
#       st.rerun()

# In the edit harga block:
#   for item in st.session_state.master_rokok_data:
#       if item["merk"] == selected_edit_merk:
#           item["harga_kanvas"] = int(up_kanvas)
#           item["harga_konsumen"] = int(up_konsumen)
#           break
#   if save_master_harga(st.session_state.master_rokok_data):
#       refresh_master_rokok_data()
#       st.success(...)
#       st.rerun()

# Keep behavior consistent everywhere else.
# This ensures data master is linked to the JSON file instead of stale session-only values.
