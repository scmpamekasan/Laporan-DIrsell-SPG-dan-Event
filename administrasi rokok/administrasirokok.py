import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import uuid

from app_config import setup_page_config, apply_custom_styling
from date_utils import get_current_week_label, format_date_indo
from data_store import load_master_harga, init_session_state

# Konfigurasi Awal
setup_page_config()
apply_custom_styling()
init_session_state()

master_rokok = load_master_harga()
list_merk = [item["merk"] for item in master_rokok]
dict_master_detail = {item["merk"]: item for item in master_rokok}

# Header Utama
st.title("🚬 Sistem Administrasi Stok & Penjualan Rokok")
st.markdown("Pencatatan stok awal, akhir, bon keperluan, rokok gantung/belum selesai, serta setoran harga kanvas vs konsumen.")

# --- SIDEBAR: NAVIGASI & ROLE ---
st.sidebar.image("https://img.icons8.com/color/96/wooden-crate.png", width=70)
st.sidebar.header("Panel Navigasi")
role = st.sidebar.selectbox("Pilih Hak Akses (Role)", ["Admin", "Supervisi", "SPG / Promotor"])

st.sidebar.divider()
selected_date = st.sidebar.date_input("Pilih Tanggal Laporan", datetime.now())
current_week = get_current_week_label(selected_date)
st.sidebar.info(f"📅 Periode: **{current_week}**")

# --- MENU UTAMA ---
tab_stock, tab1, tab2, tab3, tab4 = st.tabs([
    "📦 Stock Rokok", 
    "📝 Input Transaksi", 
    "📊 Tabel Rekap & Edit", 
    "📋 Manajemen Bon", 
    "⚙️ Reset & Hapus Data"
])

# ================= TAB 0: STOCK ROKOK (BON MULTI-MERK, KEMARIN, & STOK AWAL) =================
with tab_stock:
    st.subheader("📦 Manajemen Stock Rokok & Bon Multi-Merk")
    st.markdown("Input 1 nomor bon untuk sekaligus banyak merk rokok, pantau sisa stock kemarin, serta kalkulasi stock awal hari ini.")

    # 1. Form Pencatatan Bon Rokok Multi-Merk
    with st.expander("➕ Input Bon Rokok Baru (Multi-Merk)", expanded=True):
        with st.form("form_bon_multimerk"):
            st.markdown("#### Informasi Umum Bon")
            c1, c2, c3 = st.columns(3)
            with c1:
                nomor_bon = st.text_input("Nomor Bon Rokok (Manual)", placeholder="Contoh: BON/2026/001")
            with c2:
                team_bon = st.text_input("Nama Team / Promotor / Pemohon", placeholder="Contoh: Siska - Zona Barat")
            with c3:
                keperluan_bon = st.selectbox("Keperluan Bon", [
                    "Dirsell SPG", 
                    "Event Pameran", 
                    "Pembinaan Kantor", 
                    "Sampling / Promosi", 
                    "Penambahan Stock Gudang", 
                    "Lainnya"
                ])

            st.markdown("---")
            st.markdown("#### Daftar Merk Rokok dalam Bon Ini")
            st.markdown("Pilih merk rokok dan masukkan jumlah satuannya. Baris kosong akan diabaikan.")

            # Menyiapkan 10 baris input default (bisa ditambah via session state jika kurang)
            if "jumlah_baris_bon" not in st.session_state:
                st.session_state.jumlah_baris_bon = 10

            item_bon_list = []
            for i in range(st.session_state.jumlah_baris_bon):
                st.markdown(f"**Item ke-{i+1}**")
                col_m, col_b, col_s, col_bu = st.columns([3, 1, 1, 1])
                with col_m:
                    m_pilih = st.selectbox(f"Merk Rokok #{i+1}", ["-"] + list_merk, key=f"bon_m_{i}")
                with col_b:
                    b_ball = st.number_input(f"Ball #{i+1}", min_value=0, value=0, key=f"bon_b_{i}")
                with col_s:
                    s_slop = st.number_input(f"Slop #{i+1}", min_value=0, value=0, key=f"bon_s_{i}")
                with col_bu:
                    bu_bungkus = st.number_input(f"Bungkus #{i+1}", min_value=0, value=0, key=f"bon_bu_{i}")

                if m_pilih != "-":
                    item_bon_list.append({
                        "merk": m_pilih,
                        "ball": b_ball,
                        "slop": s_slop,
                        "bungkus": bu_bungkus
                    })

            # Tombol tambah baris di dalam form / di luar form (Streamlit menangani interaksi tombol tambah baris)
            col_btn1, col_btn2 = st.columns([1, 4])
            with col_btn1:
                tambah_baris_btn = st.form_submit_button("➕ Tambah 5 Baris Lagi")
            with col_btn2:
                simpan_semua_bon = st.form_submit_button("💾 Simpan Semua Bon Ini", type="primary")

            if tambah_baris_btn:
                st.session_state.jumlah_baris_bon += 5
                st.rerun()

            if simpan_semua_bon:
                if not nomor_bon:
                    st.error("Nomor Bon wajib diisi!")
                elif not item_bon_list:
                    st.error("Pilih minimal 1 merk rokok yang di-bon!")
                else:
                    sukses_count = 0
                    for item in item_bon_list:
                        merk = item["merk"]
                        b = item["ball"]
                        s = item["slop"]
                        bu = item["bungkus"]
                        
                        master_item = dict_master_detail.get(merk, {"slop": 10})
                        slop_per_ball = master_item.get("slop", 10)
                        bungkus_per_slop = 10
                        total_setara = (b * slop_per_ball * bungkus_per_slop) + (s * bungkus_per_slop) + bu
                        
                        if total_setara > 0:
                            new_row = {
                                "ID": nomor_bon,
                                "Tanggal": str(selected_date),
                                "Team/Promotor": team_bon if team_bon else "Tanpa Nama",
                                "Merk Rokok": merk,
                                "Ball": b,
                                "Slop": s,
                                "Bungkus": bu,
                                "Total Setara Bungkus": total_setara,
                                "Keperluan": keperluan_bon,
                                "Keterangan": f"Bon Multi-Merk No: {nomor_bon}"
                            }
                            st.session_state.df_bon = pd.concat([st.session_state.df_bon, pd.DataFrame([new_row])], ignore_index=True)
                            sukses_count += 1

                    st.success(f"✅ Berhasil menyimpan {sukses_count} item merk rokok untuk Bon No. **{nomor_bon}**!")
                    st.session_state.jumlah_baris_bon = 10 # reset
                    st.rerun()

    st.divider()

    # 2. Sisa List Stock Rokok Kemarin
    st.markdown("### 📉 Sisa Stock Rokok Kemarin")
    prev_date = selected_date - timedelta(days=1)
    df_kemarin = pd.DataFrame()
    
    if not st.session_state.df_transaksi.empty:
        df_kemarin = st.session_state.df_transaksi[st.session_state.df_transaksi["Tanggal"] == str(prev_date)]
        if not df_kemarin.empty:
            st.info(f"Menampilkan sisa stock fisik (Stok Akhir) tanggal: **{prev_date}**")
            st.dataframe(df_kemarin[["Team/Promotor", "Merk Rokok", "Stok Akhir"]], use_container_width=True)
        else:
            st.warning(f"Tidak ada catatan transaksi pada tanggal kemarin ({prev_date}).")
    else:
        st.info("Belum ada data transaksi tersimpan.")

    st.divider()

    # 3. List Rokok Stock Awal Hari Ini (Sisa Stock Kemarin + Bon Rokok Hari Ini)
    st.markdown("### 📈 List Stock Awal Hari Ini (Sisa Kemarin + Bon Hari Ini)")
    
    df_bon_hari_ini = pd.DataFrame()
    if not st.session_state.df_bon.empty:
        df_bon_hari_ini = st.session_state.df_bon[st.session_state.df_bon["Tanggal"] == str(selected_date)]

    combined_data = []
    
    if not df_kemarin.empty:
        for _, row in df_kemarin.iterrows():
            combined_data.append({
                "Team/Promotor": row["Team/Promotor"],
                "Merk Rokok": row["Merk Rokok"],
                "Stok Kemarin": row["Stok Akhir"],
                "Bon Hari Ini (Bungkus)": 0,
                "Total Stock Awal": row["Stok Akhir"]
            })

    if not df_bon_hari_ini.empty:
        for _, bon_row in df_bon_hari_ini.iterrows():
            team = bon_row["Team/Promotor"]
            merk = bon_row["Merk Rokok"]
            qty_bon = bon_row["Total Setara Bungkus"]
            
            found = False
            for item in combined_data:
                if item["Team/Promotor"] == team and item["Merk Rokok"] == merk:
                    item["Bon Hari Ini (Bungkus)"] += qty_bon
                    item["Total Stock Awal"] = item["Stok Kemarin"] + item["Bon Hari Ini (Bungkus)"]
                    found = True
                    break
            if not found:
                combined_data.append({
                    "Team/Promotor": team,
                    "Merk Rokok": merk,
                    "Stok Kemarin": 0,
                    "Bon Hari Ini (Bungkus)": qty_bon,
                    "Total Stock Awal": qty_bon
                })

    if combined_data:
        df_stock_awal = pd.DataFrame(combined_data)
        st.dataframe(df_stock_awal, use_container_width=True)
    else:
        st.info("Belum ada data kalkulasi stock awal untuk hari ini.")

# ================= TAB 1: INPUT TRANSAKSI =================
with tab1:
    st.subheader("Form Pencatatan Harian Stok & Penjualan")
    
    with st.form("form_transaksi", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            team_name = st.text_input("Nama Team / Promotor / Direct Selling", placeholder="Contoh: SPG Zona Barat - Siska")
            merk_pilih = st.selectbox("Merk Rokok", list_merk)
        with col2:
            stok_awal = st.number_input("Stok Awal", min_value=0, value=100)
            stok_akhir = st.number_input("Stok Akhir (Sisa Fisik)", min_value=0, value=20)
            
        col3, col4, col5 = st.columns(3)
        with col3:
            belum_selesai = st.number_input("Rokok Belum Selesai / Gantung", min_value=0, value=5)
        with col4:
            bon_qty = st.number_input("Jumlah Bon Terpakai", min_value=0, value=0)
            keperluan_bon = st.selectbox("Keperluan Bon", ["-", "Event Pameran", "Direct Selling SPG", "Sampling", "Keperluan Lainnya"])
        with col5:
            default_harga_kanvas = dict_master_detail.get(merk_pilih, {}).get("harga_kanvas", 10000)
            harga_konsumen_input = st.number_input("Harga Jual Konsumen (Satuan)", min_value=0, value=int(default_harga_kanvas))

        submitted = st.form_submit_button("Simpan Data Transaksi")
        
        if submitted:
            terjual = max(0, (stok_awal - stok_akhir) - belum_selesai - bon_qty)
            harga_kanvas = default_harga_kanvas
            total_setoran_kanvas = terjual * harga_kanvas
            total_setoran_konsumen = terjual * harga_konsumen_input
            
            new_id = str(uuid.uuid4())[:8]
            new_row = {
                "ID": new_id,
                "Tanggal": str(selected_date),
                "Minggu": current_week,
                "Team/Promotor": team_name if team_name else "Tanpa Nama",
                "Merk Rokok": merk_pilih,
                "Stok Awal": stok_awal,
                "Stok Akhir": stok_akhir,
                "Belum Selesai": belum_selesai,
                "Bon Qty": bon_qty,
                "Keperluan Bon": keperluan_bon if bon_qty > 0 else "-",
                "Terjual": terjual,
                "Harga Kanvas": harga_kanvas,
                "Harga Konsumen": harga_konsumen_input,
                "Total Setoran Kanvas": total_setoran_kanvas,
                "Total Setoran Konsumen": total_setoran_konsumen
            }
            
            st.session_state.df_transaksi = pd.concat([st.session_state.df_transaksi, pd.DataFrame([new_row])], ignore_index=True)
            st.success("✅ Data transaksi berhasil disimpan!")

# ================= TAB 2: TABEL REKAP & EDIT (ST.DATA_EDITOR) =================
with tab2:
    st.subheader("📊 Tabel Rekapitulasi & Edit Data Transaksi")
    if not st.session_state.df_transaksi.empty:
        edited_df = st.data_editor(
            st.session_state.df_transaksi,
            num_rows="dynamic",
            use_container_width=True,
            key="editable_transaction_table"
        )
        if not edited_df.equals(st.session_state.df_transaksi):
            st.session_state.df_transaksi = edited_df
            st.rerun()

        st.divider()
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

# ================= TAB 3: MANAJEMEN BON =================
with tab3:
    st.subheader("📋 Manajemen Data Bon Rokok")
    if not st.session_state.df_bon.empty:
        edited_bon_table = st.data_editor(
            st.session_state.df_bon,
            num_rows="dynamic",
            use_container_width=True,
            key="editable_bon_table_main"
        )
        if not edited_bon_table.equals(st.session_state.df_bon):
            st.session_state.df_bon = edited_bon_table
            st.rerun()
            
        bon_ids = st.session_state.df_bon["ID"].tolist()
        del_bon_id = st.selectbox("Pilih ID Bon yang ingin dihapus", options=["-"] + bon_ids, key="select_del_bon")
        if st.button("Hapus Bon Terpilih"):
            if del_bon_id != "-":
                st.session_state.df_bon = st.session_state.df_bon[st.session_state.df_bon["ID"] != del_bon_id]
                st.success("Bon berhasil dihapus!")
                st.rerun()
    else:
        st.info("Belum ada data bon rokok tercatat.")

# ================= TAB 4: RESET & HAPUS ALL (ADMIN ONLY) =================
with tab4:
    st.subheader("⚙️ Zona Administratif: Reset & Hapus Keseluruhan")
    if role != "Admin":
        st.warning("⚠️ Menu ini dikunci dan hanya dapat diakses oleh **Admin**.")
    else:
        confirm_checkbox = st.checkbox("Saya mengerti risiko dan ingin menghapus seluruh data.")
        if st.button("🗑️ HAPUS SEMUA DATA (RESET ALL)", type="primary"):
            if confirm_checkbox:
                st.session_state.df_transaksi = pd.DataFrame(columns=st.session_state.df_transaksi.columns)
                st.session_state.df_bon = pd.DataFrame(columns=st.session_state.df_bon.columns)
                st.success("Semua data berhasil dibersihkan!")
                st.rerun()
            else:
                st.warning("Centang kotak konfirmasi terlebih dahulu.")
