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

# ================= TAB 0: STOCK ROKOK (BON MULTI-MERK) =================
with tab_stock:
    st.subheader("📦 Manajemen Stock Rokok & Bon Multi-Merk")
    st.markdown("Input 1 nomor bon untuk sekaligus banyak merk rokok, pantau sisa stock kemarin, serta kalkulasi stock awal hari ini.")

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
                    st.session_state.jumlah_baris_bon = 10
                    st.rerun()

    st.divider()

    # Sisa Stok Kemarin & Kalkulasi Stok Awal
    st.markdown("### 📉 Sisa Stock Rokok Kemarin & Stock Awal Hari Ini")
    prev_date = selected_date - timedelta(days=1)
    df_kemarin = pd.DataFrame()
    if not st.session_state.df_transaksi.empty:
        df_kemarin = st.session_state.df_transaksi[st.session_state.df_transaksi["Tanggal"] == str(prev_date)]
        
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
        st.dataframe(pd.DataFrame(combined_data), use_container_width=True)
    else:
        st.info("Belum ada data kalkulasi stock awal untuk hari ini.")

# ================= TAB 1: INPUT TRANSAKSI (DENGAN DROPDOWN NOMOR BON OTOMATIS) =================
with tab1:
    st.subheader("Form Pencatatan Harian Stok & Penjualan")
    st.markdown("Pilih Nomor Bon untuk mengisi otomatis data Team, Merk Rokok, dan Stock Awal.")

    # Mengambil daftar nomor bon yang tersedia
    available_bons = []
    if not st.session_state.df_bon.empty:
        available_bons = st.session_state.df_bon["ID"].unique().tolist()

    selected_bon_id = st.selectbox("🔍 Cari / Pilih Nomor Bon", options=["- Manual Input -"] + available_bons)

    # Inisialisasi nilai default form
    default_team = ""
    default_merk = list_merk[0] if list_merk else ""
    default_stok_awal = 0
    default_keperluan = "-"

    # Jika nomor bon dipilih, ambil data otomatis dari df_bon
    selected_bon_rows = pd.DataFrame()
    if selected_bon_id != "- Manual Input -" and not st.session_state.df_bon.empty:
        selected_bon_rows = st.session_state.df_bon[st.session_state.df_bon["ID"] == selected_bon_id]
        if not selected_bon_rows.empty:
            default_team = selected_bon_rows.iloc[0]["Team/Promotor"]
            default_keperluan = selected_bon_rows.iloc[0]["Keperluan"]
            # Jika bon hanya punya 1 merk atau multiple, kita bisa sediakan pilihan merk dari bon tersebut
            bon_merks = selected_bon_rows["Merk Rokok"].tolist()
            if bon_merks:
                default_merk = bon_merks[0]
                matching_row = selected_bon_rows[selected_bon_rows["Merk Rokok"] == default_merk]
                if not matching_row.empty:
                    default_stok_awal = int(matching_row.iloc[0]["Total Setara Bungkus"])

    with st.form("form_transaksi", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            team_name = st.text_input("Nama Team / Promotor / Direct Selling", value=default_team, placeholder="Contoh: SPG Zona Barat - Siska")
            
            # Jika menggunakan bon, opsi merk bisa disesuaikan atau tetap dari master
            if selected_bon_id != "- Manual Input -" and not selected_bon_rows.empty:
                bon_merks_list = selected_bon_rows["Merk Rokok"].tolist()
                merk_pilih = st.selectbox("Merk Rokok (Dari Bon)", bon_merks_list)
                # Ambil stok awal sesuai merk yang dipilih di dropdown bon
                matched_item = selected_bon_rows[selected_bon_rows["Merk Rokok"] == merk_pilih]
                if not matched_item.empty:
                    default_stok_awal = int(matched_item.iloc[0]["Total Setara Bungkus"])
            else:
                merk_pilih = st.selectbox("Merk Rokok", list_merk)

        with col2:
            stok_awal = st.number_input("Stok Awal (Otomatis dari Bon / Manual)", min_value=0, value=int(default_stok_awal))
            stok_akhir = st.number_input("Stok Akhir (Sisa Fisik)", min_value=0, value=0)
            
        col3, col4, col5 = st.columns(3)
        with col3:
            belum_selesai = st.number_input("Rokok Belum Selesai / Gantung", min_value=0, value=0)
        with col4:
            bon_qty = st.number_input("Jumlah Bon Terpakai", min_value=0, value=0)
            keperluan_bon = st.selectbox("Keperluan Bon", ["-", "Dirsell SPG", "Event Pameran", "Pembinaan Kantor", "Sampling", "Lainnya"], index=0 if default_keperluan=="-" else 1)
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
            st.success("✅ Data transaksi berdasarkan bon berhasil disimpan!")

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
            
        bon_ids = st.session_state.df_bon["ID"].unique().tolist()
        del_bon_id = st.selectbox("Pilih Nomor Bon yang ingin dihapus total", options=["-"] + bon_ids, key="select_del_bon")
        if st.button("Hapus Bon Terpilih"):
            if del_bon_id != "-":
                st.session_state.df_bon = st.session_state.df_bon[st.session_state.df_bon["ID"] != del_bon_id]
                st.success(f"Bon No. {del_bon_id} berhasil dihapus!")
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
