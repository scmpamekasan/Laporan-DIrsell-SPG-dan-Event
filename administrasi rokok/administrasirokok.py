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

# ================= TAB 0: STOCK ROKOK (BON, STOK KEMARIN, STOK AWAL HARI INI) =================
with tab_stock:
    st.subheader("📦 Manajemen Stock Rokok & Bon Pagi")
    st.markdown("Kelola nomor bon manual, pantau sisa stock kemarin, serta lihat kalkulasi stock awal hari ini.")

    # 1. Form Pencatatan Bon Rokok
    with st.expander("➕ Tambah Bon Rokok Baru", expanded=True):
        with st.form("form_bon_stock", clear_on_submit=True):
            col_b1, col_b2 = st.columns(2)
            with col_b1:
                nomor_bon = st.text_input("Nomor Bon Rokok (Manual)", placeholder="Contoh: BON/2026/XI/001")
                team_bon = st.text_input("Nama Team / Promotor / Pemohon", placeholder="Contoh: SPG Zona Barat - Siska")
            with col_b2:
                merk_bon = st.selectbox("Merk Rokok", list_merk)
                keperluan_bon = st.selectbox("Keperluan Bon", [
                    "Dirsell SPG", 
                    "Event Pameran", 
                    "Pembinaan Kantor", 
                    "Sampling / Promosi", 
                    "Penambahan Stock Gudang", 
                    "Lainnya"
                ])

            st.markdown("#### Rincian Satuan Rokok yang Di-bon")
            sc1, sc2, sc3 = st.columns(3)
            with sc1:
                bon_ball = st.number_input("Jumlah (Ball)", min_value=0, value=0)
            with sc2:
                bon_slop = st.number_input("Jumlah (Slop)", min_value=0, value=0)
            with sc3:
                bon_bungkus = st.number_input("Jumlah (Bungkus)", min_value=0, value=0)

            keterangan_bon = st.text_input("Keterangan Tambahan", placeholder="Catatan opsional...")
            simpan_bon = st.form_submit_button("Simpan Bon Rokok")

            if simpan_bon:
                if not nomor_bon:
                    st.error("Nomor Bon wajib diisi!")
                else:
                    master_item = dict_master_detail.get(merk_bon, {"slop": 10})
                    slop_per_ball = master_item.get("slop", 10)
                    bungkus_per_slop = 10
                    
                    total_setara_bungkus = (bon_ball * slop_per_ball * bungkus_per_slop) + (bon_slop * bungkus_per_slop) + bon_bungkus
                    
                    new_bon_row = {
                        "ID": nomor_bon,
                        "Tanggal": str(selected_date),
                        "Team/Promotor": team_bon if team_bon else "Tanpa Nama",
                        "Merk Rokok": merk_bon,
                        "Ball": bon_ball,
                        "Slop": bon_slop,
                        "Bungkus": bon_bungkus,
                        "Total Setara Bungkus": total_setara_bungkus,
                        "Keperluan": keperluan_bon,
                        "Keterangan": keterangan_bon
                    }
                    st.session_state.df_bon = pd.concat([st.session_state.df_bon, pd.DataFrame([new_bon_row])], ignore_index=True)
                    st.success(f"✅ Bon rokok dengan No. **{nomor_bon}** berhasil disimpan!")

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
    
    # Ambil data bon hari ini
    df_bon_hari_ini = pd.DataFrame()
    if not st.session_state.df_bon.empty:
        df_bon_hari_ini = st.session_state.df_bon[st.session_state.df_bon["Tanggal"] == str(selected_date)]

    # Buat ringkasan stock awal gabungan per Team dan Merk Rokok
    combined_data = []
    
    # Masukkan sisa kemarin sebagai basis
    if not df_kemarin.empty:
        for _, row in df_kemarin.iterrows():
            combined_data.append({
                "Team/Promotor": row["Team/Promotor"],
                "Merk Rokok": row["Merk Rokok"],
                "Stok Kemarin": row["Stok Akhir"],
                "Bon Hari Ini (Bungkus)": 0,
                "Total Stock Awal": row["Stok Akhir"]
            })

    # Tambahkan atau gabungkan dengan bon hari ini
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
        st.info("Belum ada data kalkulasi stock awal untuk hari ini (pastikan ada data sisa kemarin atau bon hari ini).")

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
    st.markdown("Anda dapat langsung mengedit sel di bawah ini secara inline menggunakan tabel interaktif, atau menghapus baris tertentu.")

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
        st.markdown("### Menu Hapus Spesifik (Per Baris / Per Hari / Per Team)")
        
        col_del1, col_del2 = st.columns(2)
        with col_del1:
            st.text("Hapus Berdasarkan ID Baris")
            row_ids = st.session_state.df_transaksi["ID"].tolist()
            selected_id_to_delete = st.selectbox("Pilih ID Baris yang ingin dihapus", options=["-"] + row_ids)
            if st.button("Hapus Baris Terpilih"):
                if selected_id_to_delete != "-":
                    st.session_state.df_transaksi = st.session_state.df_transaksi[st.session_state.df_transaksi["ID"] != selected_id_to_delete]
                    st.success(f"Baris dengan ID {selected_id_to_delete} berhasil dihapus!")
                    st.rerun()

        with col_del2:
            st.text("Hapus Berdasarkan Hari (Tanggal)")
            unique_dates = st.session_state.df_transaksi["Tanggal"].unique().tolist()
            selected_date_to_delete = st.selectbox("Pilih Tanggal yang ingin dihapus total", options=["-"] + unique_dates)
            if st.button("Hapus Data Hari Ini"):
                if selected_date_to_delete != "-":
                    st.session_state.df_transaksi = st.session_state.df_transaksi[st.session_state.df_transaksi["Tanggal"] != selected_date_to_delete]
                    st.success(f"Seluruh data pada tanggal {selected_date_to_delete} berhasil dihapus!")
                    st.rerun()

        st.divider()
        unique_teams = st.session_state.df_transaksi["Team/Promotor"].unique().tolist()
        selected_team_to_delete = st.selectbox("Pilih Team / Promotor yang ingin dihapus datanya", options=["-"] + unique_teams)
        if st.button("Hapus Data Team Terpilih"):
            if selected_team_to_delete != "-":
                st.session_state.df_transaksi = st.session_state.df_transaksi[st.session_state.df_transaksi["Team/Promotor"] != selected_team_to_delete]
                st.success(f"Seluruh data untuk team {selected_team_to_delete} berhasil dihapus!")
                st.rerun()

    else:
        st.info("Belum ada data transaksi tercatat. Silakan isi melalui tab **Input Transaksi**.")

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
                st.success(f"Bon dengan ID {del_bon_id} berhasil dihapus!")
                st.rerun()
    else:
        st.info("Belum ada data bon rokok tercatat.")

# ================= TAB 4: RESET & HAPUS ALL (ADMIN ONLY) =================
with tab4:
    st.subheader("⚙️ Zona Administratif: Reset & Hapus Keseluruhan")
    
    if role != "Admin":
        st.warning("⚠️ Menu ini dikunci dan hanya dapat diakses oleh **Admin**.")
    else:
        st.error("Tindakan di bawah ini akan menghapus seluruh database transaksi dan bon secara permanen.")
        
        confirm_checkbox = st.checkbox("Saya mengerti risiko dan ingin menghapus seluruh data.")
        
        if st.button("🗑️ HAPUS SEMUA DATA (RESET ALL)", type="primary"):
            if confirm_checkbox:
                st.session_state.df_transaksi = pd.DataFrame(columns=st.session_state.df_transaksi.columns)
                st.session_state.df_bon = pd.DataFrame(columns=st.session_state.df_bon.columns)
                st.success("Semua data berhasil dibersihkan (Reset All)!")
                st.rerun()
            else:
                st.warning("Mohon centang kotak konfirmasi terlebih dahulu sebelum melakukan Hapus Semua.")
