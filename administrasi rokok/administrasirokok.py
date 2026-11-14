import streamlit as st
import pandas as pd
from datetime import datetime
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
tab1, tab2, tab3, tab4 = st.tabs(["📝 Input Transaksi", "📊 Tabel Rekap & Edit", "📋 Manajemen Bon", "⚙️ Reset & Hapus Data"])

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

# ================= TAB 3: MANAJEMEN BON (SUB-MENU LENGKAP SATUAN & STOK) =================
with tab3:
    st.subheader("📋 Sub-Menu Bon Rokok & Penambahan Stok")
    st.markdown("Catat bon rokok berdasarkan merk master, tentukan jumlah satuan (Ball, Slop, Bungkus), dan jadikan penambah stok awal.")

    with st.form("form_bon_rokok", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            bon_team = st.text_input("Nama Team / Promotor / Pemohon Bon", placeholder="Contoh: SPG Area Barat - Budi")
            bon_merk = st.selectbox("Pilih Merk Rokok (Master)", list_merk)
        with c2:
            bon_keperluan = st.selectbox("Keperluan Bon", ["Event Pameran", "Direct Selling SPG", "Sampling / Promosi", "Penambahan Stock Gudang", "Lainnya"])
            jadikan_stok = st.checkbox("Jadikan Bon ini sebagai Penambah Stock Awal / Stock Masuk", value=True)

        st.markdown("---")
        st.markdown("#### 📦 Rincian Jumlah Satuan Rokok")
        sc1, sc2, sc3 = st.columns(3)
        with sc1:
            qty_ball = st.number_input("Jumlah (Ball)", min_value=0, value=0)
        with sc2:
            qty_slop = st.number_input("Jumlah (Slop)", min_value=0, value=0)
        with sc3:
            qty_bungkus = st.number_input("Jumlah (Bungkus)", min_value=0, value=0)
            
        bon_keterangan = st.text_input("Keterangan Tambahan", placeholder="Catatan opsional...")

        submitted_bon = st.form_submit_button("Simpan Data Bon Rokok")

        if submitted_bon:
            # Ambil standar konversi dari master master_harga_rokok_lengkap.json
            master_item = dict_master_detail.get(bon_merk, {"ball": 1, "slop": 10, "bungkus": 100})
            slop_per_ball = master_item.get("slop", 10)
            bungkus_per_slop = 10 # Standar umum atau dihitung dari master jika ada
            
            # Konversi total setara bungkus atau hitung total item
            total_setara_bungkus = (qty_ball * slop_per_ball * bungkus_per_slop) + (qty_slop * bungkus_per_slop) + qty_bungkus
            
            new_bon_id = str(uuid.uuid4())[:8]
            new_bon_row = {
                "ID": new_bon_id,
                "Tanggal": str(selected_date),
                "Team/Promotor": bon_team if bon_team else "Tanpa Nama",
                "Merk Rokok": bon_merk,
                "Ball": qty_ball,
                "Slop": qty_slop,
                "Bungkus": qty_bungkus,
                "Total Setara Bungkus": total_setara_bungkus,
                "Keperluan": bon_keperluan,
                "Masuk Stok": "Ya" if jadikan_stok else "Tidak",
                "Keterangan": bon_keterangan
            }
            
            st.session_state.df_bon = pd.concat([st.session_state.df_bon, pd.DataFrame([new_bon_row])], ignore_index=True)
            
            # Jika dicentang sebagai penambah stok, masukkan juga ke tabel transaksi sebagai tambahan stok awal
            if jadikan_stok and total_setara_bungkus > 0:
                harga_kanvas_val = master_item.get("harga_kanvas", 10000)
                new_trx_from_bon = {
                    "ID": "BON-" + new_bon_id,
                    "Tanggal": str(selected_date),
                    "Minggu": current_week,
                    "Team/Promotor": bon_team if bon_team else "Tanpa Nama",
                    "Merk Rokok": bon_merk,
                    "Stok Awal": total_setara_bungkus,
                    "Stok Akhir": 0,
                    "Belum Selesai": 0,
                    "Bon Qty": total_setara_bungkus,
                    "Keperluan Bon": bon_keperluan,
                    "Terjual": 0,
                    "Harga Kanvas": harga_kanvas_val,
                    "Harga Konsumen": harga_kanvas_val,
                    "Total Setoran Kanvas": 0,
                    "Total Setoran Konsumen": 0
                }
                st.session_state.df_transaksi = pd.concat([st.session_state.df_transaksi, pd.DataFrame([new_trx_from_bon])], ignore_index=True)

            st.success("✅ Data Bon Rokok berhasil disimpan dan otomatis diperbarui!")

    st.divider()
    st.subheader("📋 Tabel Daftar Bon Rokok (Bisa Diedit)")
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
            
        # Tombol Hapus Bon Spesifik
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
