import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import uuid
import io
import os
import requests
import json

from app_config import setup_page_config, apply_custom_styling
from date_utils import get_current_week_label, format_date_indo
from data_store import load_master_harga, init_session_state

# ==========================================
# GANTI DENGAN URL WEB APP GOOGLE APPS SCRIPT ANDA
# ==========================================
WEB_APP_URL = "https://script.google.com/macros/s/AKfycbxffkMrtnuezGBjgGYh6Bk3g0yADw0DZHSyxIliW_3_4_tHaCGwyKamKfLcVePLaj8/exec"


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
            "penyelesaian_gudang": gudang_data
        }

        response = requests.post(WEB_APP_URL, json=payload)
        result = response.json()

        if result.get("status") == "success":
            return True, "Data berhasil dibackup dan ditimpa (overwrite) ke Google Sheet!"
        else:
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

            # 1. Load Transaksi
            trx_vals = db_data.get("transaksi", [])
            if len(trx_vals) > 1:
                df_trx_loaded = pd.DataFrame(trx_vals[1:], columns=trx_vals[0])
                num_cols_trx = [
                    "Stock Awal", "Stock Akhir", "Belum Selesai", "Rokok Lain-lain",
                    "Terjual", "Harga Kanvas", "Harga Konsumen", "Total Setoran Kanvas", "Total Setoran Konsumen"
                ]
                for col in num_cols_trx:
                    if col in df_trx_loaded.columns:
                        df_trx_loaded[col] = pd.to_numeric(df_trx_loaded[col], errors='coerce').fillna(0)
                st.session_state.df_transaksi = df_trx_loaded
            else:
                st.session_state.df_transaksi = pd.DataFrame(columns=[
                    "ID", "No Bon", "Tanggal", "Minggu", "Team/Promotor", "Merk Rokok", 
                    "Stock Awal", "Stock Akhir", "Belum Selesai", "Rokok Lain-lain", 
                    "Terjual", "Harga Kanvas", "Harga Konsumen", "Total Setoran Kanvas", "Total Setoran Konsumen"
                ])

            # 2. Load Bon Resmi
            bon_vals = db_data.get("bon", [])
            if len(bon_vals) > 1:
                df_bon_loaded = pd.DataFrame(bon_vals[1:], columns=bon_vals[0])
                num_cols_bon = ["Ball", "Slop", "Bungkus", "Total Setara Bungkus"]
                for col in num_cols_bon:
                    if col in df_bon_loaded.columns:
                        df_bon_loaded[col] = pd.to_numeric(df_bon_loaded[col], errors='coerce').fillna(0)
                st.session_state.df_bon = df_bon_loaded
            else:
                st.session_state.df_bon = pd.DataFrame(columns=[
                    "ID", "Tanggal", "Team/Promotor", "Merk Rokok", "Ball", "Slop", "Bungkus", 
                    "Total Setara Bungkus", "Keperluan", "Keterangan"
                ])

            # 3. Load Pre Entry Bon
            pre_vals = db_data.get("pre_entry", [])
            if len(pre_vals) > 1:
                df_pre_loaded = pd.DataFrame(pre_vals[1:], columns=pre_vals[0])
                num_cols_pre = ["Ball", "Slop", "Bungkus", "Total Setara Bungkus"]
                for col in num_cols_pre:
                    if col in df_pre_loaded.columns:
                        df_pre_loaded[col] = pd.to_numeric(df_pre_loaded[col], errors='coerce').fillna(0)
                st.session_state.df_pre_entry_bon = df_pre_loaded
            else:
                st.session_state.df_pre_entry_bon = pd.DataFrame(columns=[
                    "ID Draftt", "Tanggal", "Rencana Penyelesaian", "Team/Promotor", "Merk Rokok", 
                    "Ball", "Slop", "Bungkus", "Total Setara Bungkus", "Keperluan", "Keterangan"
                ])

            # 4. Load Penyelesaian Gudang
            gudang_vals = db_data.get("penyelesaian_gudang", [])
            if len(gudang_vals) > 1:
                df_gudang_loaded = pd.DataFrame(gudang_vals[1:], columns=gudang_vals[0])
                if "Jumlah Bungkus" in df_gudang_loaded.columns:
                    df_gudang_loaded["Jumlah Bungkus"] = pd.to_numeric(df_gudang_loaded["Jumlah Bungkus"], errors='coerce').fillna(0)
                st.session_state.df_penyelesaian_gudang = df_gudang_loaded
            else:
                st.session_state.df_penyelesaian_gudang = pd.DataFrame(columns=[
                    "ID Penyelesaian", "Tanggal", "Team/Promotor", "Merk Rokok", "Jumlah Bungkus", "Keterangan"
                ])

            return True, "Data berhasil ditarik dan dipulihkan dari Google Sheet!"
        else:
            return False, result.get("message", "Gagal memuat data.")
    except Exception as e:
        return False, f"Error koneksi: {e}"


def get_active_remaining_stocks():
    """
    Menghitung sisa stok aktif terkini dari df_transaksi (yang juga diedit di Tabel Rekap & Edit)
    dikurangi total yang sudah diselesaikan ke gudang pada df_penyelesaian_gudang.
    """
    if st.session_state.df_transaksi.empty:
        return pd.DataFrame(columns=["Team/Promotor", "Merk Rokok", "Sisa Stock Akhir", "No Bon Terakhir", "Tanggal Terakhir"])

    df_sorted = st.session_state.df_transaksi.sort_values(by="Tanggal", ascending=False)
    df_latest = df_sorted.drop_duplicates(subset=["Team/Promotor", "Merk Rokok"], keep="first").copy()

    df_gudang_all = st.session_state.get("df_penyelesaian_gudang", pd.DataFrame())
    col_stock_akhir = "Stock Akhir" if "Stock Akhir" in df_latest.columns else "Stok Akhir"

    active_list = []
    for _, row in df_latest.iterrows():
        team = str(row["Team/Promotor"])
        merk = str(row["Merk Rokok"])
        sisa_awal = int(float(row[col_stock_akhir]))

        total_selesai_gudang = 0
        if not df_gudang_all.empty:
            gudang_filter = df_gudang_all[
                (df_gudang_all["Team/Promotor"].astype(str).str.lower() == team.lower()) &
                (df_gudang_all["Merk Rokok"].astype(str) == merk)
            ]
            if not gudang_filter.empty:
                total_selesai_gudang = int(pd.to_numeric(gudang_filter["Jumlah Bungkus"], errors='coerce').fillna(0).sum())

        sisa_aktual = max(0, sisa_awal - total_selesai_gudang)
        if sisa_aktual > 0:
            active_list.append({
                "Team/Promotor": team,
                "Merk Rokok": merk,
                "Sisa Stock Akhir": sisa_aktual,
                "No Bon Terakhir": str(row.get("No Bon", "-")),
                "Tanggal Terakhir": str(row.get("Tanggal", "-"))
            })

    return pd.DataFrame(active_list)


# Konfigurasi Awal
setup_page_config()
apply_custom_styling()
init_session_state()

if "trx_form_reset_id" not in st.session_state:
    st.session_state.trx_form_reset_id = 0

if "master_rokok_data" not in st.session_state:
    st.session_state.master_rokok_data = load_master_harga()

if "df_pre_entry_bon" not in st.session_state:
    st.session_state.df_pre_entry_bon = pd.DataFrame(columns=[
        "ID Draftt", "Tanggal", "Rencana Penyelesaian", "Team/Promotor", "Merk Rokok", 
        "Ball", "Slop", "Bungkus", "Total Setara Bungkus", "Keperluan", "Keterangan"
    ])
elif "Rencana Penyelesaian" not in st.session_state.df_pre_entry_bon.columns:
    st.session_state.df_pre_entry_bon["Rencana Penyelesaian"] = str(datetime.now().date())

if "df_penyelesaian_gudang" not in st.session_state:
    st.session_state.df_penyelesaian_gudang = pd.DataFrame(columns=[
        "ID Penyelesaian", "Tanggal", "Team/Promotor", "Merk Rokok", "Jumlah Bungkus", "Keterangan"
    ])

# ==========================================
# OTOMATIS LOAD DATA SAAT PERTAMA KALI DIBUKA
# ==========================================
if "is_data_loaded" not in st.session_state:
    st.session_state.is_data_loaded = False

if not st.session_state.is_data_loaded:
    with st.spinner("⏳ Menghubungkan dan menarik data awal dari Google Sheet..."):
        success, msg = load_from_google_sheets()
        st.session_state.is_data_loaded = True
        if success:
            st.toast("✅ Data berhasil dimuat otomatis dari Google Sheet!", icon="🚀")

master_rokok = st.session_state.master_rokok_data
list_merk = [item["merk"] for item in master_rokok]
dict_master_detail = {item["merk"]: item for item in master_rokok}

# Header Utama
st.title("🚬 Sistem Administrasi Stock & Penjualan Rokok")
st.markdown("Pencatatan Stock Rokok - Bon Rokok - Rokok Gantung/Belum Selesai - Setoran Hasil Penjualan")

# --- SIDEBAR: NAVIGASI & ROLE ---
try:
    col1, col2, col3 = st.sidebar.columns([1, 2, 1])
    with col2:
        dir_path = os.path.dirname(os.path.abspath(__file__))
        logo_path = os.path.join(dir_path, "SCMlogo.png")
        st.image(logo_path, width=120)
except Exception:
    col1, col2, col3 = st.sidebar.columns([1, 2, 1])
    with col2:
        st.image("https://img.icons8.com/color/96/wooden-crate.png", width=120)

st.sidebar.header("Menu")
role = st.sidebar.selectbox("User Login", ["Promotor", "PIC Dirsell & Event", "Admin"])

# --- MENU MASTER ROKOK DI SIDEBAR ---
with st.sidebar.expander("🛠️ Master Harga & Merk Rokok", expanded=False):
    st.markdown("### Update Harga & Merk")
    
    with st.form("form_tambah_merk_baru", clear_on_submit=True):
        st.markdown("**Tambah Merk Baru**")
        new_merk_name = st.text_input("Nama Merk Baru")
        new_harga_kanvas = st.number_input("Harga Kanvas", min_value=0, value=10000, step=100)
        new_harga_konsumen = st.number_input("Harga Konsumen", min_value=0, value=0, step=100)
        new_ball = st.number_input("Ball", min_value=1, value=1)
        new_slop = st.number_input("Slop per Ball", min_value=1, value=20)
        new_bungkus = st.number_input("Bungkus per Ball", min_value=1, value=200)
        
        btn_add_merk = st.form_submit_button("➕ Tambah Merk")
        if btn_add_merk:
            clean_name = new_merk_name.strip()
            if not clean_name:
                st.error("Nama merk tidak boleh kosong!")
            elif clean_name in list_merk:
                st.error("Merk tersebut sudah ada!")
            else:
                st.session_state.master_rokok_data.append({
                    "merk": clean_name,
                    "harga_kanvas": int(new_harga_kanvas),
                    "harga_konsumen": int(new_harga_konsumen),
                    "ball": int(new_ball),
                    "slop": int(new_slop),
                    "bungkus": int(new_bungkus)
                })
                st.session_state.trx_form_reset_id += 1
                st.success(f"Berhasil menambah merk {clean_name}!")
                st.rerun()

    st.markdown("---")
    st.markdown("**Edit Harga Cepat**")
    selected_edit_merk = st.selectbox("Pilih Merk untuk Diedit", options=list_merk, key="sidebar_edit_merk_select")
    
    if selected_edit_merk:
        current_detail = dict_master_detail[selected_edit_merk]
        with st.form(f"form_edit_harga_{selected_edit_merk}"):
            up_kanvas = st.number_input("Harga Kanvas Baru", min_value=0, value=int(current_detail.get("harga_kanvas", 0)), step=100)
            up_konsumen = st.number_input("Harga Konsumen Baru", min_value=0, value=int(current_detail.get("harga_konsumen", 0)), step=100)
            
            btn_save_harga = st.form_submit_button("💾 Simpan Perubahan Harga")
            if btn_save_harga:
                for item in st.session_state.master_rokok_data:
                    if item["merk"] == selected_edit_merk:
                        item["harga_kanvas"] = int(up_kanvas)
                        item["harga_konsumen"] = int(up_konsumen)
                        break
                
                harga_widget_key = f"harga_konsumen_{st.session_state.trx_form_reset_id}_{selected_edit_merk}"
                if harga_widget_key in st.session_state:
                    st.session_state[harga_widget_key] = int(up_konsumen)
                
                st.success(f"Harga {selected_edit_merk} berhasil diperbarui!")
                st.rerun()

st.sidebar.divider()
selected_date = st.sidebar.date_input("Pilih Tanggal Laporan", datetime.now())
current_week = get_current_week_label(selected_date)
st.sidebar.info(f"📅 Periode: **{current_week}**")

# --- MENU UTAMA ---
tab_pre_entry, tab_stock, tab1, tab2, tab_lap_team, tab3, tab_gudang, tab4 = st.tabs([
    "📥 Pre Entry Draft Bon",
    "📦 Stock Rokok", 
    "📝 Input Transaksi", 
    "📊 Tabel Rekap Penjualan", 
    "👥 Laporan Per Team",
    "📋 Management Bon", 
    "📥 Penyelesaian ke Gudang",
    "⚙️ Backup & Reset Data"
])

# ================= TAB 0: PRE ENTRY Draft BON =================
with tab_pre_entry:
    st.subheader("📥 Pre Entry Draft Bon Rokok")
    st.markdown("Buat Draft permintaan bon terlebih dahulu sebelum mendapatkan No Bon resmi dari Admin. Sertakan tanggal rencana penyelesaian bon.")

    if "pre_form_reset_id" not in st.session_state:
        st.session_state.pre_form_reset_id = 0

    with st.expander("➕ Buat Draft Bon Baru (Multi-Merk)", expanded=True):
        with st.form(f"form_pre_entry_{st.session_state.pre_form_reset_id}", clear_on_submit=True):
            st.markdown("#### Informasi Draft Bon")
            
            c1, c2, c3 = st.columns(3)
            with c1:
                team_pre = st.text_input("Nama Pengebon / Promotor", placeholder="Contoh: Beni")
            with c2:
                rencana_penyelesaian_date = st.date_input("Tanggal Rencana Penyelesaian", datetime.now())
            with c3:
                keperluan_pre = st.selectbox("Keperluan Bon", [
                    "Dirsell SPG", "Event", "Pembinaan Kantor", "Sampling / Promosi", "Lainnya"
                ], key="pre_kep")

            keterangan_pre_umum = st.text_input("Keterangan Draft (Opsional)", placeholder="Contoh: Permintaan stok untuk Event Weekend")

            st.markdown("---")
            st.markdown("#### Daftar Merk Rokok dalam Draft Ini")
            
            if "jumlah_baris_pre" not in st.session_state:
                st.session_state.jumlah_baris_pre = 5

            item_pre_list = []
            for i in range(st.session_state.jumlah_baris_pre):
                col_m, col_b, col_s, col_bu = st.columns([3, 1, 1, 1])
                with col_m:
                    m_pilih = st.selectbox(f"Merk Rokok #{i+1}", ["-"] + list_merk, key=f"pre_m_{st.session_state.pre_form_reset_id}_{i}")
                with col_b:
                    b_ball = st.number_input(f"Ball #{i+1}", min_value=0, value=0, key=f"pre_b_{st.session_state.pre_form_reset_id}_{i}")
                with col_s:
                    s_slop = st.number_input(f"Slop #{i+1}", min_value=0, value=0, key=f"pre_s_{st.session_state.pre_form_reset_id}_{i}")
                with col_bu:
                    bu_bungkus = st.number_input(f"Bungkus #{i+1}", min_value=0, value=0, key=f"pre_bu_{st.session_state.pre_form_reset_id}_{i}")

                if m_pilih != "-":
                    item_pre_list.append({
                        "merk": m_pilih, "ball": b_ball, "slop": s_slop, "bungkus": bu_bungkus
                    })

            col_pbtn1, col_pbtn2 = st.columns([1, 4])
            with col_pbtn1:
                tambah_baris_pre_btn = st.form_submit_button("➕ Tambah 3 Baris")
            with col_pbtn2:
                simpan_Draft_btn = st.form_submit_button("💾 Simpan Sebagai Draft Pre Entry", type="primary")

            if tambah_baris_pre_btn:
                st.session_state.jumlah_baris_pre += 3
                st.rerun()

            if simpan_Draft_btn:
                if not team_pre:
                    st.error("Nama Pengebon Wajib Diisi!")
                elif not item_pre_list:
                    st.error("Pilih minimal 1 merk rokok!")
                else:
                    Draftt_group_id = f"Draft-{str(uuid.uuid4())[:6].upper()}"
                    sukses_Draftt = 0
                    for item in item_pre_list:
                        merk = item["merk"]
                        b = item["ball"]
                        s = item["slop"]
                        bu = item["bungkus"]
                        
                        master_item = dict_master_detail.get(merk, {"slop": 20, "bungkus": 200})
                        slop_per_ball = master_item.get("slop", 20)
                        bungkus_per_slop = 10
                        total_setara = (b * slop_per_ball * bungkus_per_slop) + (s * bungkus_per_slop) + bu
                        
                        if total_setara > 0:
                            ket_final = keterangan_pre_umum if keterangan_pre_umum else f"Draft Permintaan"
                            new_Draftt_row = {
                                "ID Draftt": Draftt_group_id,
                                "Tanggal": str(selected_date),
                                "Rencana Penyelesaian": str(rencana_penyelesaian_date),
                                "Team/Promotor": team_pre,
                                "Merk Rokok": merk,
                                "Ball": b,
                                "Slop": s,
                                "Bungkus": bu,
                                "Total Setara Bungkus": total_setara,
                                "Keperluan": keperluan_pre,
                                "Keterangan": ket_final
                            }
                            st.session_state.df_pre_entry_bon = pd.concat([
                                st.session_state.df_pre_entry_bon, pd.DataFrame([new_Draftt_row])
                            ], ignore_index=True)
                            sukses_Draftt += 1

                    st.session_state.jumlah_baris_pre = 5
                    st.session_state.pre_form_reset_id += 1
                    st.success(f"✅ Berhasil menyimpan Draft dengan ID Group **{Draftt_group_id}** (Rencana Penyelesaian: {rencana_penyelesaian_date})!")
                    st.rerun()

    st.divider()
    st.markdown("### 📋 Daftar Draft Pre Entry Bon (Belum Disubmit)")

    if not st.session_state.df_pre_entry_bon.empty:
        st.dataframe(st.session_state.df_pre_entry_bon, use_container_width=True)

        st.markdown("#### 🚀 Submit Draft Menjadi Bon Resmi (Masukkan No Bon dari Admin)")
        unique_Draftt_ids = st.session_state.df_pre_entry_bon["ID Draftt"].unique().tolist()
        
        col_sub1, col_sub2, col_sub3 = st.columns([2, 2, 1])
        with col_sub1:
            selected_Draftt_to_submit = st.selectbox("Pilih ID Draft yang ingin disubmit", options=["-"] + unique_Draftt_ids)
        with col_sub2:
            input_no_bon_asli = st.text_input("Masukkan No Bon Resmi dari Admin", placeholder="Contoh: BON-OFFICIAL-01")
        with col_sub3:
            st.markdown("<br>", unsafe_allow_html=True)
            btn_submit_Draftt = st.button("📤 Submit Bon", type="primary")

        if btn_submit_Draftt:
            if selected_Draftt_to_submit == "-":
                st.error("Pilih ID Draft terlebih dahulu!")
            elif not input_no_bon_asli.strip():
                st.error("No Bon Resmi dari Admin wajib diisi!")
            else:
                rows_to_move = st.session_state.df_pre_entry_bon[
                    st.session_state.df_pre_entry_bon["ID Draftt"] == selected_Draftt_to_submit
                ]
                
                for _, r in rows_to_move.iterrows():
                    official_bon_row = {
                        "ID": input_no_bon_asli.strip(),
                        "Tanggal": r["Tanggal"],
                        "Team/Promotor": r["Team/Promotor"],
                        "Merk Rokok": r["Merk Rokok"],
                        "Ball": r["Ball"],
                        "Slop": r["Slop"],
                        "Bungkus": r["Bungkus"],
                        "Total Setara Bungkus": r["Total Setara Bungkus"],
                        "Keperluan": r["Keperluan"],
                        "Keterangan": f"Resmi Admin ({input_no_bon_asli.strip()}) | Rencana: {r['Rencana Penyelesaian']} - {r['Keterangan']}"
                    }
                    st.session_state.df_bon = pd.concat([
                        st.session_state.df_bon, pd.DataFrame([official_bon_row])
                    ], ignore_index=True)

                st.session_state.df_pre_entry_bon = st.session_state.df_pre_entry_bon[
                    st.session_state.df_pre_entry_bon["ID Draftt"] != selected_Draftt_to_submit
                ]

                st.success(f"🎉 Draft {selected_Draftt_to_submit} berhasil disubmit dengan No Bon Resmi **{input_no_bon_asli.strip()}**!")
                st.rerun()

        if st.button("🗑️ Hapus Draft Terpilih"):
            if selected_Draftt_to_submit != "-":
                st.session_state.df_pre_entry_bon = st.session_state.df_pre_entry_bon[
                    st.session_state.df_pre_entry_bon["ID Draftt"] != selected_Draftt_to_submit
                ]
                st.success(f"Draft {selected_Draftt_to_submit} berhasil dihapus.")
                st.rerun()
    else:
        st.info("Belum ada Draft Pre Entry Bon yang dibuat.")

# ================= TAB 1: STOCK ROKOK =================
with tab_stock:
    st.subheader("📉 Sisa Stock Terakhir & Stock Awal Hari Ini")
    st.markdown("Pantau sisa stock terakhir dan kalkulasi stock awal hari ini secara otomatis.")
    
    df_active_stocks = get_active_remaining_stocks()
    df_bon_hari_ini = pd.DataFrame()
    if not st.session_state.df_bon.empty:
        df_bon_hari_ini = st.session_state.df_bon[st.session_state.df_bon["Tanggal"] == str(selected_date)]

    combined_data = []
    if not df_active_stocks.empty:
        for _, row in df_active_stocks.iterrows():
            combined_data.append({
                "Team/Promotor": row["Team/Promotor"],
                "Merk Rokok": row["Merk Rokok"],
                "Stock Terakhir": int(row["Sisa Stock Akhir"]),
                "Bon Hari Ini (Bungkus)": 0,
                "Total Stock Awal": int(row["Sisa Stock Akhir"])
            })

    if not df_bon_hari_ini.empty:
        for _, bon_row in df_bon_hari_ini.iterrows():
            team = bon_row["Team/Promotor"]
            merk = bon_row["Merk Rokok"]
            qty_bon = int(bon_row["Total Setara Bungkus"])
            
            found = False
            for item in combined_data:
                if item["Team/Promotor"].lower() == team.lower() and item["Merk Rokok"] == merk:
                    item["Bon Hari Ini (Bungkus)"] += qty_bon
                    item["Total Stock Awal"] = item["Stock Terakhir"] + item["Bon Hari Ini (Bungkus)"]
                    found = True
                    break
            if not found:
                if qty_bon > 0:
                    combined_data.append({
                        "Team/Promotor": team,
                        "Merk Rokok": merk,
                        "Stock Terakhir": 0,
                        "Bon Hari Ini (Bungkus)": qty_bon,
                        "Total Stock Awal": qty_bon
                    })

    final_combined_data = [item for item in combined_data if item["Total Stock Awal"] > 0]

    if final_combined_data:
        st.dataframe(pd.DataFrame(final_combined_data), use_container_width=True)
    else:
        st.info("Tidak Ada Sisa Stock Aktif atau Bon Baru Untuk Hari Ini (Semua Stock Bernilai 0 / Habis).")

# ================= TAB 2: INPUT TRANSAKSI =================
with tab1:
    st.subheader("📝 Form Pencatatan Harian Transaksi & Stock")
    st.markdown("Pilih Nomor Bon Untuk Menampilkan Otomatis Seluruh Merk Rokok Sesuai Layout.")

    if "last_trx_msg" in st.session_state and st.session_state["last_trx_msg"]:
        st.success(st.session_state.pop("last_trx_msg"))

    all_bons = []
    if not st.session_state.df_bon.empty:
        all_bons = st.session_state.df_bon["ID"].unique().tolist()
    
    used_bons = []
    if not st.session_state.df_transaksi.empty and "No Bon" in st.session_state.df_transaksi.columns:
        used_bons = st.session_state.df_transaksi["No Bon"].unique().tolist()

    available_bons = [b for b in all_bons if b not in used_bons]

    def update_bon_fields():
        chosen = st.session_state.get(f"select_bon_trx_{st.session_state.trx_form_reset_id}", "- Manual Input -")
        if chosen != "- Manual Input -" and not st.session_state.df_bon.empty:
            matched_row = st.session_state.df_bon[st.session_state.df_bon["ID"] == chosen]
            if not matched_row.empty:
                st.session_state[f"no_bon_in_{st.session_state.trx_form_reset_id}"] = chosen
                st.session_state[f"nama_in_{st.session_state.trx_form_reset_id}"] = matched_row.iloc[0]["Team/Promotor"]
        else:
            st.session_state[f"no_bon_in_{st.session_state.trx_form_reset_id}"] = ""
            st.session_state[f"nama_in_{st.session_state.trx_form_reset_id}"] = ""

    selected_bon_id = st.selectbox(
        "🔍 Cari / Pilih No Bon Resmi", 
        options=["- Manual Input -"] + available_bons,
        key=f"select_bon_trx_{st.session_state.trx_form_reset_id}",
        on_change=update_bon_fields
    )

    default_no_bon = ""
    default_nama = ""
    if selected_bon_id != "- Manual Input -" and not st.session_state.df_bon.empty:
        matched_row = st.session_state.df_bon[st.session_state.df_bon["ID"] == selected_bon_id]
        if not matched_row.empty:
            default_no_bon = selected_bon_id
            default_nama = matched_row.iloc[0]["Team/Promotor"]

    text_bon_key = f"no_bon_in_{st.session_state.trx_form_reset_id}"
    text_nama_key = f"nama_in_{st.session_state.trx_form_reset_id}"
    
    if text_bon_key not in st.session_state:
        st.session_state[text_bon_key] = default_no_bon
    if text_nama_key not in st.session_state:
        st.session_state[text_nama_key] = default_nama

    col_h1, col_h2 = st.columns(2)
    with col_h1:
        st.markdown("**No Bon**")
        input_no_bon = st.text_input("No Bon Input", key=text_bon_key, label_visibility="collapsed")
    with col_h2:
        st.markdown("**Nama**")
        input_nama = st.text_input("Nama Input", placeholder="Nama Promotor / Team", key=text_nama_key, label_visibility="collapsed")

    st.markdown("---")

    active_merks = []
    current_active_bon = st.session_state.get(text_bon_key, "")
    current_active_nama = st.session_state.get(text_nama_key, "")

    if current_active_bon and not st.session_state.df_bon.empty:
        selected_bon_rows = st.session_state.df_bon[st.session_state.df_bon["ID"] == current_active_bon]
        if not selected_bon_rows.empty:
            active_merks = selected_bon_rows["Merk Rokok"].tolist()
    
    if not active_merks:
        active_merks = st.multiselect(
            "🚬 Pilih Daftar Merk Rokok (Mode Manual Input)",
            options=list_merk,
            default=list_merk[:3],
            key=f"manual_merks_{st.session_state.trx_form_reset_id}"
        )

    with st.form(f"form_transaksi_layout_{st.session_state.trx_form_reset_id}", clear_on_submit=True):
        st.markdown("**Pilih Merk Rokok & Stock Awal (Stock Kemarin + Bon Hari Ini)**")
        stock_awal_values = {}
        df_active_stocks_trx = get_active_remaining_stocks()

        for merk in active_merks:
            stok_terakhir = 0
            if current_active_nama and not df_active_stocks_trx.empty:
                match_active = df_active_stocks_trx[
                    (df_active_stocks_trx["Team/Promotor"].str.lower() == current_active_nama.lower()) &
                    (df_active_stocks_trx["Merk Rokok"] == merk)
                ]
                if not match_active.empty:
                    stok_terakhir = int(match_active.iloc[0]["Sisa Stock Akhir"])

            bon_hari_ini = 0
            if current_active_bon and not st.session_state.df_bon.empty:
                match_bon = st.session_state.df_bon[
                    (st.session_state.df_bon["ID"] == current_active_bon) & 
                    (st.session_state.df_bon["Merk Rokok"] == merk)
                ]
                if not match_bon.empty:
                    bon_hari_ini = int(float(match_bon.iloc[0]["Total Setara Bungkus"]))

            val_awal = stok_terakhir + bon_hari_ini
            stock_awal_values[merk] = val_awal

            c_m, c_v = st.columns([3, 2])
            with c_m:
                st.markdown(f"🚬 **{merk}**")
            with c_v:
                st.markdown(f"📦 **{val_awal:,} bks** *(Stock Terakhir: {stok_terakhir} + Bon: {bon_hari_ini})*")

        st.markdown("---")
        st.markdown("**Rokok Belum Selesai / Gantung** | **Jumlah (dalam satuan bungkus)**")
        gantung_inputs = {}
        for merk in active_merks:
            c_m, c_v = st.columns([3, 2])
            with c_m:
                st.text(merk)
            with c_v:
                gantung_inputs[merk] = st.number_input(f"Gantung_{merk}", min_value=0, value=0, key=f"gantung_{st.session_state.trx_form_reset_id}_{merk}", label_visibility="collapsed")

        st.markdown("---")
        st.markdown("**Sisa Stock Akhir** | **Jumlah (dalam satuan bungkus)**")
        akhir_inputs = {}
        for merk in active_merks:
            c_m, c_v = st.columns([3, 2])
            with c_m:
                st.text(merk)
            with c_v:
                akhir_inputs[merk] = st.number_input(f"Akhir_{merk}", min_value=0, value=0, key=f"akhir_{st.session_state.trx_form_reset_id}_{merk}", label_visibility="collapsed")

        st.markdown("---")
        st.markdown("**Merk Rokok** | **Harga Jual Konsumen (Otomatis dari Master)**")
        harga_inputs = {}
        for merk in active_merks:
            master_item_info = dict_master_detail.get(merk, {})
            def_konsumen = int(master_item_info.get("harga_konsumen", 0))
            
            widget_key = f"harga_konsumen_{st.session_state.trx_form_reset_id}_{merk}"
            if widget_key not in st.session_state:
                st.session_state[widget_key] = def_konsumen
            
            c_m, c_v = st.columns([3, 2])
            with c_m:
                st.markdown(f"🚬 **{merk}**")
            with c_v:
                harga_inputs[merk] = st.number_input(f"HargaKonsumen_{merk}", min_value=0, key=widget_key, label_visibility="collapsed")

        st.markdown("---")
        st.markdown("**Pengeluaran Rokok Lain-lain** | **Jumlah (dalam satuan bungkus)**")
        lain_inputs = {}
        for merk in active_merks:
            c_m, c_v = st.columns([3, 2])
            with c_m:
                st.text(merk)
            with c_v:
                lain_inputs[merk] = st.number_input(f"Lain_{merk}", min_value=0, value=0, key=f"lain_{st.session_state.trx_form_reset_id}_{merk}", label_visibility="collapsed")

        st.markdown("")
        submitted_all = st.form_submit_button("💾 Simpan Seluruh Transaksi Harian Ini", type="primary")

        if submitted_all:
            final_input_bon = st.session_state.get(text_bon_key, "")
            final_input_nama = st.session_state.get(text_nama_key, "")

            if not final_input_bon:
                st.error("No Bon wajib diisi!")
            elif not active_merks:
                st.error("Pilih minimal 1 merk rokok!")
            else:
                saved_count = 0
                for merk in active_merks:
                    s_awal = stock_awal_values[merk]
                    s_akhir = akhir_inputs[merk]
                    s_gantung = gantung_inputs[merk]
                    s_lain = lain_inputs[merk]  
                    
                    h_konsumen = int(harga_inputs[merk])
                    h_kanvas = int(dict_master_detail.get(merk, {}).get("harga_kanvas", 0))
                    
                    terjual = max(0, (s_awal - s_akhir) - s_gantung - s_lain)
                    tot_kanvas = terjual * h_kanvas
                    tot_konsumen = terjual * h_konsumen

                    new_row = {
                        "ID": str(uuid.uuid4())[:8],
                        "No Bon": final_input_bon,
                        "Tanggal": str(selected_date),
                        "Minggu": current_week,
                        "Team/Promotor": final_input_nama if final_input_nama else "Tanpa Nama",
                        "Merk Rokok": merk,
                        "Stock Awal": s_awal,
                        "Stock Akhir": s_akhir,
                        "Belum Selesai": s_gantung,
                        "Rokok Lain-lain": s_lain,                
                        "Terjual": terjual,
                        "Harga Kanvas": h_kanvas,
                        "Harga Konsumen": h_konsumen,
                        "Total Setoran Kanvas": tot_kanvas,
                        "Total Setoran Konsumen": tot_konsumen
                    }
                    st.session_state.df_transaksi = pd.concat([st.session_state.df_transaksi, pd.DataFrame([new_row])], ignore_index=True)
                    saved_count += 1

                st.session_state.trx_form_reset_id += 1
                if text_bon_key in st.session_state:
                    del st.session_state[text_bon_key]
                if text_nama_key in st.session_state:
                    del st.session_state[text_nama_key]

                st.session_state["last_trx_msg"] = f"✅ Berhasil menyimpan {saved_count} data transaksi untuk No Bon **{final_input_bon}**!"
                st.rerun()
                
# ================= TAB 3: TABEL REKAP & EDIT =================
with tab2:
    st.subheader("📊 Rekapitulasi Data Transaksi")
    
    if not st.session_state.df_transaksi.empty:
        if "No Bon" not in st.session_state.df_transaksi.columns:
            st.session_state.df_transaksi["No Bon"] = st.session_state.df_transaksi["ID"]

        st.markdown("### ✏️ Edit Data Transaksi Langsung")
        edited_df = st.data_editor(st.session_state.df_transaksi, num_rows="dynamic", use_container_width=True, key="editable_transaction_table")
        if not edited_df.equals(st.session_state.df_transaksi):
            for idx, row in edited_df.iterrows():
                row_id = row["ID"]
                st.session_state.df_transaksi.loc[st.session_state.df_transaksi["ID"] == row_id] = row
            st.rerun()

        st.divider()
        st.markdown("### 🔍 Filter Berdasarkan Team / Promotor, Tanggal & No Bon")
        
        list_teams = ["Semua Team"] + st.session_state.df_transaksi["Team/Promotor"].unique().tolist()
        list_tgl_penyelesaian = ["Semua Tanggal"] + sorted(st.session_state.df_transaksi["Tanggal"].dropna().unique().tolist(), reverse=True)
        list_no_bon = ["Semua No Bon"] + sorted(st.session_state.df_transaksi["No Bon"].dropna().unique().tolist())

        col_f_1, col_f_2, col_f_3 = st.columns(3)
        with col_f_1:
            selected_filter_team = st.selectbox("Pilih Team / Promotor", options=list_teams, key="filter_team_tab2")
        with col_f_2:
            selected_filter_tgl = st.selectbox("Tanggal Penyelesaian Bon", options=list_tgl_penyelesaian, key="filter_tgl_tab2")
        with col_f_3:
            selected_filter_bon = st.selectbox("No Bon", options=list_no_bon, key="filter_bon_tab2")

        df_filtered = st.session_state.df_transaksi.copy()
        if selected_filter_team != "Semua Team":
            df_filtered = df_filtered[df_filtered["Team/Promotor"] == selected_filter_team]
        if selected_filter_tgl != "Semua Tanggal":
            df_filtered = df_filtered[df_filtered["Tanggal"] == selected_filter_tgl]
        if selected_filter_bon != "Semua No Bon":
            df_filtered = df_filtered[df_filtered["No Bon"] == selected_filter_bon]

        st.markdown("---")
        st.markdown(f"### 💰 Grand Total & Ringkasan Keuangan (Filter Aktif)")
        
        grand_total_konsumen = pd.to_numeric(df_filtered["Total Setoran Konsumen"], errors='coerce').sum()
        grand_total_kanvas = pd.to_numeric(df_filtered["Total Setoran Kanvas"], errors='coerce').sum()
        total_terjual = pd.to_numeric(df_filtered["Terjual"], errors='coerce').sum()
        total_lain = pd.to_numeric(df_filtered["Rokok Lain-lain"], errors='coerce').sum() if "Rokok Lain-lain" in df_filtered.columns else 0

        col_gt1, col_gt2, col_gt3, col_gt4 = st.columns(4)
        with col_gt1:
            st.metric("Total Rokok Terjual", f"{total_terjual:,.0f} Bks")
        with col_gt2:
            st.metric("Total Rokok Lain-lain", f"{total_lain:,.0f} Bks")
        with col_gt3:
            st.metric("Grand Total Kanvas", f"Rp {grand_total_kanvas:,.0f}")
        with col_gt4:
            st.metric("🎯 Total Setoran Konsumen", f"Rp {grand_total_konsumen:,.0f}")


        st.markdown("---")
        st.markdown("### 👥 Rekapitulasi Berdasarkan Team / Promotor")
        if not df_filtered.empty:
            df_rekap_team = df_filtered.groupby("Team/Promotor").agg({
                "Terjual": "sum", "Rokok Lain-lain": "sum", "Total Setoran Kanvas": "sum", "Total Setoran Konsumen": "sum"
            }).reset_index()
            st.dataframe(df_rekap_team, use_container_width=True)
        else:
            st.info("Tidak ada data rekapitulasi team untuk filter terpilih.")

        st.markdown("---")
        st.markdown("### 📋 Rekapitulasi Berdasarkan Nomor Bon")
        if "No Bon" in df_filtered.columns and not df_filtered.empty:
            df_rekap_bon = df_filtered.groupby("No Bon").agg({
                "Team/Promotor": "first", "Tanggal": "first", "Terjual": "sum",
                "Rokok Lain-lain": "sum", "Total Setoran Kanvas": "sum", "Total Setoran Konsumen": "sum"
            }).reset_index()
            st.dataframe(df_rekap_bon, use_container_width=True)
        else:
            st.info("Tidak ada data rekapitulasi bon untuk filter terpilih.")

        st.markdown("---")
        st.markdown(f"### 📦 Kondisi Sisa Stock Akhir Terakhir per Merk Rokok")
        
        df_active_tab2 = get_active_remaining_stocks()
        if selected_filter_team != "Semua Team":
            df_active_tab2 = df_active_tab2[df_active_tab2["Team/Promotor"] == selected_filter_team]

        if not df_active_tab2.empty:
            df_sisa_merk = df_active_tab2.groupby("Merk Rokok")["Sisa Stock Akhir"].sum().reset_index()
            df_sisa_merk.columns = ["Merk Rokok", "Sisa Stock Akhir Terakhir (Bungkus)"]
            st.dataframe(df_sisa_merk, use_container_width=True)
        else:
            st.info("Tidak ada sisa stock aktif (semua stock sudah habis atau diselesaikan ke gudang).")

        st.divider()
        st.markdown("### 🗑️ Menu Hapus Data")
        col_del1, col_del2 = st.columns(2)
        with col_del1:
            row_ids = st.session_state.df_transaksi["ID"].tolist()
            selected_id_to_delete = st.selectbox("Pilih ID Baris yang ingin dihapus", options=["-"] + row_ids)
            if st.button("Hapus Baris Terpilih"):
                if selected_id_to_delete != "-":
                    st.session_state.df_transaksi = st.session_state.df_transaksi[st.session_state.df_transaksi["ID"] != selected_id_to_delete]
                    st.success("Baris berhasil dihapus!")
                    st.rerun()
        with col_del2:
            unique_dates = st.session_state.df_transaksi["Tanggal"].unique().tolist()
            selected_date_to_delete = st.selectbox("Pilih Tanggal yang ingin dihapus total", options=["-"] + unique_dates)
            if st.button("Hapus Data Hari Ini"):
                if selected_date_to_delete != "-":
                    st.session_state.df_transaksi = st.session_state.df_transaksi[st.session_state.df_transaksi["Tanggal"] != selected_date_to_delete]
                    st.success("Data tanggal terpilih berhasil dihapus!")
                    st.rerun()
    else:
        st.info("Belum ada data transaksi tercatat.")

# ================= TAB 4: LAPORAN PENJUALAN PER TEAM =================
with tab_lap_team:
    st.subheader("👥 Laporan Data Penjualan per Team / Promotor")
    st.markdown("Filter dan Analisis Penjualan berdasarkan Team/Promotor lengkap dengan opsi download Excel.")

    if not st.session_state.df_transaksi.empty:
        c_f1, c_f2 = st.columns(2)
        with c_f1:
            list_teams_lap = ["Semua Team"] + st.session_state.df_transaksi["Team/Promotor"].unique().tolist()
            filter_team_chosen = st.selectbox("Pilih Team / Promotor", options=list_teams_lap, key="filter_team_lap")
        with c_f2:
            list_dates_lap = ["Semua Tanggal"] + sorted(st.session_state.df_transaksi["Tanggal"].unique().tolist(), reverse=True)
            filter_date_chosen = st.selectbox("Filter Tanggal", options=list_dates_lap, key="filter_date_lap")

        df_lap = st.session_state.df_transaksi.copy()
        if filter_team_chosen != "Semua Team":
            df_lap = df_lap[df_lap["Team/Promotor"] == filter_team_chosen]
        if filter_date_chosen != "Semua Tanggal":
            df_lap = df_lap[df_lap["Tanggal"] == filter_date_chosen]

        if not df_lap.empty:
            df_grouped_lap = df_lap.groupby("Merk Rokok").agg({
                "Harga Kanvas": "first", "Terjual": "sum", "Total Setoran Kanvas": "sum", "Total Setoran Konsumen": "sum"
            }).reset_index()

            df_grouped_lap.columns = [
                "Merk Rokok", "Harga Kanvas (per Bungkus)", "Jumlah Rokok Laku (Bks)", "Total (Harga Kanvas)", "Total (Harga Konsumen)"
            ]

            st.markdown("#### Tabel Ringkasan Penjualan")
            st.dataframe(df_grouped_lap, use_container_width=True)

            if not df_grouped_lap.empty:
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df_grouped_lap.to_excel(writer, index=False, sheet_name='Laporan Penjualan')
                excel_data = output.getvalue()

                filename_excel = f"Laporan_Penjualan_{filter_team_chosen.replace(' ', '_')}.xlsx"
                st.download_button(
                    label="📥 Download Excel Laporan Ini",
                    data=excel_data,
                    file_name=filename_excel,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    type="primary"
                )
        else:
            st.info("Tidak ada data transaksi yang sesuai dengan filter yang dipilih.")
    else:
        st.info("Belum ada data transaksi tercatat untuk dibuatkan laporan.")

# ================= TAB 5: Management BON & PRE ENTRY REPORT =================
with tab3:
    st.subheader("📋 Management & Rekap Data Bon Rokok")
    
    # ----------------------------------------------------
    # BAGIAN 1: LAPORAN Draft PRE ENTRY BON
    # ----------------------------------------------------
    st.markdown("### 📥 Rekapitulasi Draft Pre Entry Bon (Belum Disubmit)")
    st.markdown("Filter, unduh, pratinjau cetak, dan cetak rekapitulasi Draft bon berdasarkan tanggal rencana penyelesaian.")

    if not st.session_state.df_pre_entry_bon.empty:
        list_rencana_tgl = ["Semua Tanggal"] + sorted(st.session_state.df_pre_entry_bon["Rencana Penyelesaian"].dropna().unique().tolist())
        selected_filter_rencana = st.selectbox("📅 Filter Berdasarkan Tanggal Rencana Penyelesaian Bon", options=list_rencana_tgl, key="filter_rencana_penyelesaian_bon")

        df_pre_filtered = st.session_state.df_pre_entry_bon.copy()
        if selected_filter_rencana != "Semua Tanggal":
            df_pre_filtered = df_pre_filtered[df_pre_filtered["Rencana Penyelesaian"] == selected_filter_rencana]

        if not df_pre_filtered.empty:
            df_pre_grouped_merk = df_pre_filtered.groupby("Merk Rokok").agg({
                "Total Setara Bungkus": "sum"
            }).reset_index()

            pre_konversi_list = []
            for _, row in df_pre_grouped_merk.iterrows():
                m_name = row["Merk Rokok"]
                tot_bks = int(row["Total Setara Bungkus"])
                
                master_info = dict_master_detail.get(m_name, {"slop": 20, "bungkus": 200})
                slop_per_ball = master_info.get("slop", 20)
                bungkus_per_ball = master_info.get("bungkus", 200)
                bungkus_per_slop = 10
                
                ball = tot_bks // bungkus_per_ball
                sisa_bks = tot_bks % bungkus_per_ball
                slop = sisa_bks // bungkus_per_slop
                bungkus = sisa_bks % bungkus_per_slop

                pre_konversi_list.append({
                    "Merk Rokok": m_name,
                    "Ball": int(ball),
                    "Slop": int(slop),
                    "Bungkus": int(bungkus)
                })

            df_pre_display = pd.DataFrame(pre_konversi_list)
            st.dataframe(df_pre_display, use_container_width=True)

            col_act1, col_act2, col_act3 = st.columns(3)
            
            output_pre = io.BytesIO()
            with pd.ExcelWriter(output_pre, engine='openpyxl') as writer:
                df_pre_display.to_excel(writer, index=False, sheet_name='Rekap Draft Pre-Entry')
            excel_pre_data = output_pre.getvalue()
            
            with col_act1:
                st.download_button(
                    label="📥 Download Excel Draft",
                    data=excel_pre_data,
                    file_name=f"Rekap_Draft_PreEntry_{selected_filter_rencana}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    type="primary"
                )

            html_table = df_pre_display.to_html(index=False, classes='table table-striped')
            print_html = f"""
            <html>
                <head>
                    <title>Cetak Rekap Draft Pre Entry Bon</title>
                    <style>
                        body {{ font-family: Arial, sans-serif; padding: 20px; }}
                        h2 {{ text-align: center; }}
                        table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
                        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                        th {{ background-color: #f2f2f2; }}
                    </style>
                </head>
                <body>
                    <h2>Rekapitulasi Draft Pre Entry Bon</h2>
                    <p><b>Tanggal Rencana Penyelesaian:</b> {selected_filter_rencana}</p>
                    {html_table}
                    <script>
                        window.onload = function() {{ window.print(); }}
                    </script>
                </body>
            </html>
            """

            with col_act2:
                if st.button("👁️ Preview Print Draft"):
                    st.components.v1.html(print_html, height=400, scrolling=True)

            with col_act3:
                st.download_button(
                    label="🖨️ Print Rekap Draft",
                    data=print_html,
                    file_name=f"Print_Rekap_Draft_{selected_filter_rencana}.html",
                    mime="text/html"
                )

            with st.expander("🔎 Lihat Detail Rincian Baris Draft Pre Entry"):
                st.dataframe(df_pre_filtered, use_container_width=True)
        else:
            st.warning("Tidak ada Draft bon untuk tanggal rencana penyelesaian tersebut.")
    else:
        st.info("Belum ada Draft Pre Entry Bon yang aktif saat ini.")

    st.divider()

    # ----------------------------------------------------
    # BAGIAN 2: LAPORAN BON RESMI & STATUS BON (SELESAI / BELUM SELESAI)
    # ----------------------------------------------------
    st.markdown("### 📋 Rekapitulasi Data Bon Rokok Resmi & Status Bon")
    st.markdown("Pilih filter keterangan dan status bon (Selesai/Belum Selesai), lalu lihat ringkasan gabungan merk rokok.")

    if not st.session_state.df_bon.empty:
        used_bon_list = []
        if not st.session_state.df_transaksi.empty and "No Bon" in st.session_state.df_transaksi.columns:
            used_bon_list = st.session_state.df_transaksi["No Bon"].astype(str).unique().tolist()

        df_bon_status = st.session_state.df_bon.copy()
        df_bon_status["Status Bon"] = df_bon_status["ID"].astype(str).apply(
            lambda x: "Selesai" if x in used_bon_list else "Belum Selesai (Masih Menggantung)"
        )

        list_keterangan = []
        if "Keterangan" in df_bon_status.columns:
            unique_ket = df_bon_status["Keterangan"].dropna().unique().tolist()
            list_keterangan = [str(k) for k in unique_ket if str(k).strip() != ""]

        list_team_bon = ["Semua Team"] + sorted(df_bon_status["Team/Promotor"].dropna().unique().tolist())
        list_status_bon = ["Semua Status", "Selesai", "Belum Selesai (Masih Menggantung)"]

        col_fk1, col_fk2, col_fk3 = st.columns(3)
        with col_fk1:
            selected_ket_filter = st.multiselect(
                "🔍 Filter Keterangan", options=list_keterangan, default=list_keterangan, key="filter_keterangan_multi"
            )
        with col_fk2:
            selected_team_bon_filter = st.selectbox("👥 Filter Team / Promotor", options=list_team_bon, key="filter_team_bon_mgmt_multi")
        with col_fk3:
            selected_status_filter = st.selectbox("📌 Filter Status Bon", options=list_status_bon, key="filter_status_bon_mgmt")

        df_bon_filtered = df_bon_status.copy()
        
        if selected_ket_filter:
            df_bon_filtered = df_bon_filtered[df_bon_filtered["Keterangan"].isin(selected_ket_filter)]
        else:
            df_bon_filtered = df_bon_filtered.iloc[0:0]

        if selected_team_bon_filter != "Semua Team":
            df_bon_filtered = df_bon_filtered[df_bon_filtered["Team/Promotor"] == selected_team_bon_filter]

        if selected_status_filter != "Semua Status":
            df_bon_filtered = df_bon_filtered[df_bon_filtered["Status Bon"] == selected_status_filter]

        st.markdown("---")
        st.markdown("#### 📊 Ringkasan Gabungan Merk Rokok & Konversi Satuan (Bon Resmi)")

        if not df_bon_filtered.empty:
            df_grouped_merk = df_bon_filtered.groupby("Merk Rokok").agg({
                "Total Setara Bungkus": "sum"
            }).reset_index()

            hasil_tabel_konversi = []
            for _, row in df_grouped_merk.iterrows():
                merk_name = row["Merk Rokok"]
                total_bks = int(row["Total Setara Bungkus"])

                master_info = dict_master_detail.get(merk_name, {"slop": 20, "bungkus": 200, "harga_kanvas": 0})
                
                slop_per_ball = master_info.get("slop", 20)
                bungkus_per_ball = master_info.get("bungkus", 200)
                bungkus_per_slop = 10
                
                ball = total_bks // bungkus_per_ball
                sisa_bks_1 = total_bks % bungkus_per_ball
                
                slop = sisa_bks_1 // bungkus_per_slop
                bungkus = sisa_bks_1 % bungkus_per_slop

                hasil_tabel_konversi.append({
                    "Merk Rokok": merk_name, "Ball": int(ball), "Slop": int(slop), "Bungkus": int(bungkus)
                })

            df_final_display = pd.DataFrame(hasil_tabel_konversi)
            total_merk_unik = len(df_final_display)
            
            mc1, mc2 = st.columns(2)
            with mc1:
                st.metric("Total Jenis Merk Rokok", f"{total_merk_unik} Merk")
            with mc2:
                st.metric("Status Filter", "Aktif")

            st.markdown("")
            st.markdown("##### 📌 Tabel Rekap Gabungan & Konversi Satuan")
            st.dataframe(df_final_display, use_container_width=True)

            st.divider()
            with st.expander("🔎 Lihat Detail Rincian Baris Bon Resmi & Statusnya"):
                edited_bon_table = st.data_editor(df_bon_filtered, num_rows="dynamic", use_container_width=True, key="editable_bon_table_multi_filtered")
                if not edited_bon_table.equals(df_bon_filtered):
                    for idx, row in edited_bon_table.iterrows():
                        st.session_state.df_bon.loc[st.session_state.df_bon["ID"] == row["ID"]] = row
                    st.rerun()

            st.divider()
            st.markdown("#### 📑 Ringkasan Total Bon Berdasarkan Keterangan")
            if "Keterangan" in df_bon_status.columns:
                df_rekap_ket = df_bon_filtered.groupby("Keterangan").agg(
                    Jumlah_Bon=("ID", "nunique"),
                    Total_Setara_Bungkus=("Total Setara Bungkus", "sum")
                ).reset_index()
                df_rekap_ket.columns = ["Keterangan", "Jumlah Bon", "Total Setara Bungkus (Bks)"]
                st.dataframe(df_rekap_ket, use_container_width=True)

        else:
            st.warning("Tidak ada data bon resmi yang sesuai dengan filter pilihan Anda.")

        st.divider()
        st.markdown("### 🗑️ Hapus Data Bon Resmi")
        bon_ids = st.session_state.df_bon["ID"].unique().tolist()
        del_bon_id = st.selectbox("Pilih No Bon yang ingin dihapus total", options=["-"] + bon_ids, key="select_del_bon")
        if st.button("Hapus Bon Terpilih"):
            if del_bon_id != "-":
                st.session_state.df_bon = st.session_state.df_bon[st.session_state.df_bon["ID"] != del_bon_id]
                st.success(f"No Bon {del_bon_id} berhasil dihapus!")
                st.rerun()
    else:
        st.info("Belum ada data bon resmi tercatat.")

# ================= TAB 6: PENYELESAIAN ROKOK KE GUDANG =================
with tab_gudang:
    st.subheader("📥 Menu Penyelesaian Rokok ke Gudang")
    st.markdown("Data sisa rokok diambil secara otomatis dari **Tabel Rekapitulasi & Edit Data Transaksi**. Pilih Team/Promotor untuk menyelesaikan sisa rokok hari ini agar tidak muncul pada sisa stock hari berikutnya.")

    df_sisa_aktif_gudang = get_active_remaining_stocks()

    if not df_sisa_aktif_gudang.empty:
        list_team_sisa = sorted(df_sisa_aktif_gudang["Team/Promotor"].unique().tolist())

        col_gdg_f1, col_gdg_f2, col_gdg_f3 = st.columns(3)
        with col_gdg_f1:
            selected_team_gudang = st.selectbox(
                "👤 Pilih Team / Promotor",
                options=list_team_sisa,
                key="select_team_penyelesaian_gudang"
            )
        with col_gdg_f2:
            tanggal_penyelesaian = st.date_input("📅 Tanggal Penyelesaian", selected_date, key="tgl_penyelesaian_gudang")
        with col_gdg_f3:
            keterangan_gudang = st.text_input(
                "📝 Keterangan Penyelesaian",
                value="Penyelesaian Sisa Rokok ke Gudang",
                key="ket_penyelesaian_gudang"
            )

        df_target_gudang = df_sisa_aktif_gudang[
            df_sisa_aktif_gudang["Team/Promotor"] == selected_team_gudang
        ].copy().reset_index(drop=True)

        st.markdown("---")
        st.markdown(f"#### 📦 Daftar Sisa Stock Rokok Aktif Milik **{selected_team_gudang}**")
        st.caption("Centang item yang ingin diselesaikan ke gudang, dan sesuaikan kolom **Jumlah Bungkus Diselesaikan** (default terisi otomatis seluruh sisa stock).")

        df_target_gudang.insert(0, "Selesaikan", True)
        df_target_gudang["Jumlah Bungkus Diselesaikan"] = df_target_gudang["Sisa Stock Akhir"]

        edited_penyelesaian = st.data_editor(
            df_target_gudang,
            column_config={
                "Selesaikan": st.column_config.CheckboxColumn("Selesaikan?", default=True),
                "Team/Promotor": st.column_config.TextColumn("Team/Promotor", disabled=True),
                "Merk Rokok": st.column_config.TextColumn("Merk Rokok", disabled=True),
                "Sisa Stock Akhir": st.column_config.NumberColumn("Sisa Stock Tersedia (Bks)", disabled=True),
                "No Bon Terakhir": st.column_config.TextColumn("No Bon Terakhir", disabled=True),
                "Tanggal Terakhir": st.column_config.TextColumn("Tanggal Terakhir", disabled=True),
                "Jumlah Bungkus Diselesaikan": st.column_config.NumberColumn(
                    "Jumlah Diselesaikan ke Gudang (Bks)",
                    min_value=0,
                    step=1
                ),
            },
            hide_index=True,
            use_container_width=True,
            key=f"editor_penyelesaian_gudang_{selected_team_gudang}"
        )

        if st.button("💾 Submit Penyelesaian ke Gudang", type="primary"):
            rows_selected = edited_penyelesaian[
                (edited_penyelesaian["Selesaikan"] == True) &
                (edited_penyelesaian["Jumlah Bungkus Diselesaikan"] > 0)
            ]

            if rows_selected.empty:
                st.warning("Tidak ada item yang dicentang atau jumlah bungkus bernilai 0.")
            else:
                id_penyelesaian = f"GDG-{str(uuid.uuid4())[:6].upper()}"
                sukses_gudang = 0
                error_over = False

                for _, r in rows_selected.iterrows():
                    sisa_tersedia = int(r["Sisa Stock Akhir"])
                    jml_selesai = int(r["Jumlah Bungkus Diselesaikan"])

                    if jml_selesai > sisa_tersedia:
                        st.error(f"Jumlah penyelesaian untuk **{r['Merk Rokok']}** ({jml_selesai} bks) melebihi sisa stock tersedia ({sisa_tersedia} bks)!")
                        error_over = True
                        break

                if not error_over:
                    for _, r in rows_selected.iterrows():
                        new_gudang_row = {
                            "ID Penyelesaian": id_penyelesaian,
                            "Tanggal": str(tanggal_penyelesaian),
                            "Team/Promotor": str(r["Team/Promotor"]),
                            "Merk Rokok": str(r["Merk Rokok"]),
                            "Jumlah Bungkus": int(r["Jumlah Bungkus Diselesaikan"]),
                            "Keterangan": f"{keterangan_gudang} (Ref Bon: {r['No Bon Terakhir']})"
                        }
                        st.session_state.df_penyelesaian_gudang = pd.concat([
                            st.session_state.df_penyelesaian_gudang, pd.DataFrame([new_gudang_row])
                        ], ignore_index=True)
                        sukses_gudang += 1

                    st.success(f"✅ Berhasil menyelesaikan {sukses_gudang} item rokok milik **{selected_team_gudang}** ke gudang (ID: **{id_penyelesaian}**)!")
                    st.rerun()
    else:
        st.info("Saat ini tidak ada sisa stock aktif pada data transaksi yang perlu diselesaikan ke gudang.")

    st.divider()
    st.markdown("### 📋 Riwayat Data Penyelesaian Rokok ke Gudang")

    if not st.session_state.df_penyelesaian_gudang.empty:
        edited_gudang_table = st.data_editor(
            st.session_state.df_penyelesaian_gudang, 
            num_rows="dynamic", 
            use_container_width=True, 
            key="editable_gudang_table"
        )
        if not edited_gudang_table.equals(st.session_state.df_penyelesaian_gudang):
            st.session_state.df_penyelesaian_gudang = edited_gudang_table
            st.rerun()

        st.markdown("")
        col_del_gdg1, col_del_gdg2 = st.columns(2)
        with col_del_gdg1:
            gudang_ids = st.session_state.df_penyelesaian_gudang["ID Penyelesaian"].unique().tolist()
            selected_gdg_to_del = st.selectbox("Pilih ID Penyelesaian yang ingin dihapus", options=["-"] + gudang_ids)
            if st.button("Hapus ID Penyelesaian Terpilih"):
                if selected_gdg_to_del != "-":
                    st.session_state.df_penyelesaian_gudang = st.session_state.df_penyelesaian_gudang[
                        st.session_state.df_penyelesaian_gudang["ID Penyelesaian"] != selected_gdg_to_del
                    ]
                    st.success(f"Data penyelesaian {selected_gdg_to_del} berhasil dihapus.")
                    st.rerun()
    else:
        st.info("Belum ada riwayat penyelesaian rokok ke gudang.")

# ================= TAB 7: BACKUP, RESTORE & RESET (DAPAT DIAKSES SEMUA ROLE) =================
with tab4:
    st.subheader("⚙️ Menu Backup, Load & Reset Data")
    st.markdown(f"Status Login Saat Ini: **{role}** (Menu Backup & Load Google Sheet terbuka untuk semua role).")

    col_bk1, col_bk2 = st.columns(2)
    
    with col_bk1:
        st.markdown("### ☁️ Backup ke Google Sheet")
        st.markdown("Menimpa (*overwrite*) data terbaru ke Google Sheet agar aman dan tidak double.")
        if st.button("🚀 Backup Sekarang (Overwrite)", type="primary"):
            with st.spinner("Sedang memproses backup data..."):
                success, msg = backup_to_google_sheets()
                if success:
                    st.success("✅ " + msg)
                else:
                    st.error("❌ " + msg)

    with col_bk2:
        st.markdown("### 📥 Load dari Google Sheet")
        st.markdown("Tarik data dari Google Sheet secara manual jika diperlukan.")
        if st.button("🔄 Tarik Data dari Google Sheet", type="secondary"):
            with st.spinner("Sedang memuat data..."):
                success, msg = load_from_google_sheets()
                if success:
                    st.success("✅ " + msg)
                    st.rerun()
                else:
                    st.error("❌ " + msg)

    st.divider()
    st.markdown("### 🗑️ Zona Bahaya: Reset & Hapus Keseluruhan")
    if role != "Admin":
        st.info("🔒 Tombol **Hapus Semua Data (Reset All)** hanya dapat diakses oleh role **Admin**.")
    else:
        confirm_checkbox = st.checkbox("Saya mengerti risiko dan ingin menghapus seluruh data.")
        if st.button("🗑️ HAPUS SEMUA DATA (RESET ALL)", type="primary"):
            if confirm_checkbox:
                st.session_state.df_transaksi = pd.DataFrame(columns=st.session_state.df_transaksi.columns)
                st.session_state.df_bon = pd.DataFrame(columns=st.session_state.df_bon.columns)
                st.session_state.df_pre_entry_bon = pd.DataFrame(columns=st.session_state.df_pre_entry_bon.columns)
                st.session_state.df_penyelesaian_gudang = pd.DataFrame(columns=st.session_state.df_penyelesaian_gudang.columns)
                st.success("Semua data berhasil dibersihkan!")
                st.rerun()
            else:
                st.warning("Centang kotak konfirmasi terlebih dahulu.")
