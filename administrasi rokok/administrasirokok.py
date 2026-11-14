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

    if "bon_form_reset_id" not in st.session_state:
        st.session_state.bon_form_reset_id = 0

    with st.expander("➕ Input Bon Rokok Baru (Multi-Merk)", expanded=True):
        with st.form(f"form_bon_multimerk_{st.session_state.bon_form_reset_id}", clear_on_submit=True):
            st.markdown("#### Informasi Umum Bon")
            c1, c2, c3 = st.columns(3)
            with c1:
                nomor_bon = st.text_input("No Bon", placeholder="Contoh: bon111")
            with c2:
                team_bon = st.text_input("Nama (Promotor / Team)", placeholder="Contoh: Beni")
            with c3:
                keperluan_bon = st.selectbox("Keperluan Bon Utama", [
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
                col_m, col_b, col_s, col_bu = st.columns([3, 1, 1, 1])
                with col_m:
                    m_pilih = st.selectbox(f"Merk Rokok #{i+1}", ["-"] + list_merk, key=f"bon_m_{st.session_state.bon_form_reset_id}_{i}")
                with col_b:
                    b_ball = st.number_input(f"Ball #{i+1}", min_value=0, value=0, key=f"bon_b_{st.session_state.bon_form_reset_id}_{i}")
                with col_s:
                    s_slop = st.number_input(f"Slop #{i+1}", min_value=0, value=0, key=f"bon_s_{st.session_state.bon_form_reset_id}_{i}")
                with col_bu:
                    bu_bungkus = st.number_input(f"Bungkus #{i+1}", min_value=0, value=0, key=f"bon_bu_{st.session_state.bon_form_reset_id}_{i}")

                if m_pilih != "-":
                    item_bon_list.append({
                        "merk": m_pilih,
                        "ball": b_ball,
                        "slop": s_slop,
                        "bungkus": bu_bungkus
                    })

            col_btn1, col_btn2 = st.columns([1, 4])
            with col_btn1:
                tambah_baris_btn = st.form_submit_button("➕ Tambah 5 Baris")
            with col_btn2:
                simpan_semua_bon = st.form_submit_button("💾 Simpan Semua Bon Ini", type="primary")

            if tambah_baris_btn:
                st.session_state.jumlah_baris_bon += 5
                st.rerun()

            if simpan_semua_bon:
                if not nomor_bon:
                    st.error("No Bon wajib diisi!")
                elif not item_bon_list:
                    st.error("Pilih minimal 1 merk rokok!")
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
                                "Keterangan": f"Bon No: {nomor_bon}"
                            }
                            st.session_state.df_bon = pd.concat([st.session_state.df_bon, pd.DataFrame([new_row])], ignore_index=True)
                            sukses_count += 1

                    st.session_state.jumlah_baris_bon = 10
                    st.session_state.bon_form_reset_id += 1
                    st.session_state["last_bon_msg"] = f"✅ Berhasil menyimpan {sukses_count} item merk untuk No Bon **{nomor_bon}**!"
                    st.rerun()

    if "last_bon_msg" in st.session_state and st.session_state["last_bon_msg"]:
        st.success(st.session_state.pop("last_bon_msg"))

    st.divider()

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

# ================= TAB 1: INPUT TRANSAKSI =================
with tab1:
    st.subheader("📝 Form Pencatatan Harian Transaksi & Stok")
    st.markdown("Pilih Nomor Bon untuk menampilkan otomatis seluruh merk rokok sesuai layout[cite: 3].")

    if "trx_form_reset_id" not in st.session_state:
        st.session_state.trx_form_reset_id = 0

    if "last_trx_msg" in st.session_state and st.session_state["last_trx_msg"]:
        st.success(st.session_state.pop("last_trx_msg"))

    available_bons = []
    if not st.session_state.df_bon.empty:
        available_bons = st.session_state.df_bon["ID"].unique().tolist()

    selected_bon_id = st.selectbox(
        "🔍 Cari / Pilih No Bon", 
        options=["- Manual Input -"] + available_bons,
        key=f"select_bon_trx_{st.session_state.trx_form_reset_id}"
    )

    default_team = ""
    selected_bon_rows = pd.DataFrame()

    if selected_bon_id != "- Manual Input -" and not st.session_state.df_bon.empty:
        selected_bon_rows = st.session_state.df_bon[st.session_state.df_bon["ID"] == selected_bon_id]
        if not selected_bon_rows.empty:
            default_team = selected_bon_rows.iloc[0]["Team/Promotor"]

    col_h1, col_h2 = st.columns(2)
    with col_h1:
        st.markdown("**No Bon**")
        input_no_bon = st.text_input(
            "No Bon Input", 
            value=selected_bon_id if selected_bon_id != "- Manual Input -" else "", 
            key=f"no_bon_in_{st.session_state.trx_form_reset_id}",
            label_visibility="collapsed"
        )
    with col_h2:
        st.markdown("**Nama**")
        input_nama = st.text_input(
            "Nama Input", 
            value=default_team, 
            placeholder="Nama Promotor / Team", 
            key=f"nama_in_{st.session_state.trx_form_reset_id}",
            label_visibility="collapsed"
        )

    st.markdown("---")

    active_merks = []
    if selected_bon_id != "- Manual Input -" and not selected_bon_rows.empty:
        active_merks = selected_bon_rows["Merk Rokok"].tolist()
    else:
        active_merks = list_merk[:3]

    with st.form(f"form_transaksi_layout_{st.session_state.trx_form_reset_id}", clear_on_submit=True):
        
        st.markdown("**Pilih Merk Rokok yang akan diinput transaksinya** | **Stock Awal (dalam satuan Bungkus)**")
        stok_awal_inputs = {}
        for merk in active_merks:
            default_val = 0
            if selected_bon_id != "- Manual Input -" and not selected_bon_rows.empty:
                matched = selected_bon_rows[selected_bon_rows["Merk Rokok"] == merk]
                if not matched.empty:
                    default_val = int(matched.iloc[0]["Total Setara Bungkus"])
            
            c_m, c_v = st.columns([3, 2])
            with c_m:
                st.text(merk)
            with c_v:
                stok_awal_inputs[merk] = st.number_input(
                    f"Awal_{merk}", 
                    min_value=0, 
                    value=default_val, 
                    key=f"awal_{st.session_state.trx_form_reset_id}_{merk}",
                    label_visibility="collapsed"
                )

        st.markdown("---")

        st.markdown("**Rokok Belum Selesai / Gantung** | **Jumlah (dalam satuan bungkus)**")
        gantung_inputs = {}
        for merk in active_merks:
            c_m, c_v = st.columns([3, 2])
            with c_m:
                st.text(merk)
            with c_v:
                gantung_inputs[merk] = st.number_input(
                    f"Gantung_{merk}", 
                    min_value=0, 
                    value=0, 
                    key=f"gantung_{st.session_state.trx_form_reset_id}_{merk}",
                    label_visibility="collapsed"
                )

        st.markdown("---")

        st.markdown("**Sisa Stock Akhir** | **Jumlah (dalam satuan bungkus)**")
        akhir_inputs = {}
        for merk in active_merks:
            c_m, c_v = st.columns([3, 2])
            with c_m:
                st.text(merk)
            with c_v:
                akhir_inputs[merk] = st.number_input(
                    f"Akhir_{merk}", 
                    min_value=0, 
                    value=0, 
                    key=f"akhir_{st.session_state.trx_form_reset_id}_{merk}",
                    label_visibility="collapsed"
                )

        st.markdown("---")

        st.markdown("**Harga Jual Konsumen (Satuan)** | **Harga Jual Konsumen (Satuan)**")
        harga_inputs = {}
        for merk in active_merks:
            def_harga = dict_master_detail.get(merk, {}).get("harga_kanvas", 10000)
            c_m, c_v = st.columns([3, 2])
            with c_m:
                st.text(merk)
            with c_v:
                harga_inputs[merk] = st.number_input(
                    f"Harga_{merk}", 
                    min_value=0, 
                    value=int(def_harga), 
                    key=f"harga_{st.session_state.trx_form_reset_id}_{merk}",
                    label_visibility="collapsed"
                )

        st.markdown("---")

        st.markdown("**Pengeluaran Rokok Lain-lain** | **Jumlah (dalam satuan bungkus)**")
        lain_inputs = {}
        for merk in active_merks:
            c_m, c_v = st.columns([3, 2])
            with c_m:
                st.text(merk)
            with c_v:
                lain_inputs[merk] = st.number_input(
                    f"Lain_{merk}", 
                    min_value=0, 
                    value=0, 
                    key=f"lain_{st.session_state.trx_form_reset_id}_{merk}",
                    label_visibility="collapsed"
                )

        st.markdown("")
        submitted_all = st.form_submit_button("💾 Simpan Seluruh Transaksi Harian Ini", type="primary")

        if submitted_all:
            if not input_no_bon:
                st.error("No Bon wajib diisi!")
            else:
                saved_count = 0
                for merk in active_merks:
                    s_awal = stok_awal_inputs[merk]
                    s_akhir = akhir_inputs[merk]
                    s_gantung = gantung_inputs[merk]
                    s_lain = lain_inputs[merk]
                    h_konsumen = harga_inputs[merk]
                    
                    h_kanvas = dict_master_detail.get(merk, {}).get("harga_kanvas", 10000)
                    terjual = max(0, (s_awal - s_akhir) - s_gantung - s_lain)
                    tot_kanvas = terjual * h_kanvas
                    tot_konsumen = terjual * h_konsumen

                    new_row = {
                        "ID": str(uuid.uuid4())[:8],
                        "No Bon": input_no_bon,
                        "Tanggal": str(selected_date),
                        "Minggu": current_week,
                        "Team/Promotor": input_nama if input_nama else "Tanpa Nama",
                        "Merk Rokok": merk,
                        "Stok Awal": s_awal,
                        "Stok Akhir": s_akhir,
                        "Belum Selesai": s_gantung,
                        "Bon Qty": s_lain,
                        "Keperluan Bon": f"Bon [{input_no_bon}]",
                        "Terjual": terjual,
                        "Harga Kanvas": h_kanvas,
                        "Harga Konsumen": h_konsumen,
                        "Total Setoran Kanvas": tot_kanvas,
                        "Total Setoran Konsumen": tot_konsumen
                    }
                    st.session_state.df_transaksi = pd.concat([st.session_state.df_transaksi, pd.DataFrame([new_row])], ignore_index=True)
                    saved_count += 1

                st.session_state.trx_form_reset_id += 1
                st.session_state["last_trx_msg"] = f"✅ Berhasil menyimpan {saved_count} data transaksi untuk No Bon **{input_no_bon}**!"
                st.rerun()

# ================= TAB 2: TABEL REKAP & EDIT (DENGAN FILTER TEAM/PROMOTOR) =================
with tab2:
    st.subheader("📊 Tabel Rekapitulasi & Edit Data Transaksi")
    
    if not st.session_state.df_transaksi.empty:
        if "No Bon" not in st.session_state.df_transaksi.columns:
            st.session_state.df_transaksi["No Bon"] = st.session_state.df_transaksi["ID"]

        st.markdown("### ✏️ Edit Data Transaksi Langsung")
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

        # --- FILTER TEAM / PROMOTOR ---
        st.markdown("### 🔍 Filter Berdasarkan Team / Promotor")
        list_teams = ["Semua Team"] + st.session_state.df_transaksi["Team/Promotor"].unique().tolist()
        selected_filter_team = st.selectbox("Pilih Team / Promotor untuk Filter Ringkasan", options=list_teams)

        # Filter dataframe sesuai pilihan
        if selected_filter_team == "Semua Team":
            df_filtered = st.session_state.df_transaksi
        else:
            df_filtered = st.session_state.df_transaksi[st.session_state.df_transaksi["Team/Promotor"] == selected_filter_team]

        st.markdown("---")

        # --- GRAND TOTAL & RINGKASAN KEUANGAN (BERDASARKAN FILTER) ---
        st.markdown(f"### 💰 Grand Total & Ringkasan Keuangan ({selected_filter_team})")
        
        grand_total_konsumen = df_filtered["Total Setoran Konsumen"].sum()
        grand_total_kanvas = df_filtered["Total Setoran Kanvas"].sum()
        total_terjual = df_filtered["Terjual"].sum()

        col_gt1, col_gt2, col_gt3 = st.columns(3)
        with col_gt1:
            st.metric("Total Rokok Terjual", f"{total_terjual:,.0f} Bks")
        with col_gt2:
            st.metric("Grand Total Setoran Kanvas", f"Rp {grand_total_kanvas:,.0f}")
        with col_gt3:
            st.metric("🎯 Grand Total Setoran Konsumen", f"Rp {grand_total_konsumen:,.0f}")

        st.markdown("---")

        # --- TOTAL SISA STOCK AKHIR PER MERK (BERDASARKAN FILTER) ---
        st.markdown(f"### 📦 Total Sisa Stock Akhir (Sisa Fisik) per Merk Rokok ({selected_filter_team})")
        if not df_filtered.empty:
            df_sisa_merk = df_filtered.groupby("Merk Rokok")["Stok Akhir"].sum().reset_index()
            df_sisa_merk.columns = ["Merk Rokok", "Total Sisa Stok Akhir (Bungkus)"]
            st.dataframe(df_sisa_merk, use_container_width=True)
        else:
            st.info("Tidak ada data untuk team ini.")

        st.markdown("---")

        # --- REKAPITULASI PER BON ---
        st.markdown("### 📋 Rekapitulasi Berdasarkan Nomor Bon")
        if "No Bon" in st.session_state.df_transaksi.columns:
            df_rekap_bon = st.session_state.df_transaksi.groupby("No Bon").agg({
                "Team/Promotor": "first",
                "Tanggal": "first",
                "Terjual": "sum",
                "Total Setoran Kanvas": "sum",
                "Total Setoran Konsumen": "sum"
            }).reset_index()
            st.dataframe(df_rekap_bon, use_container_width=True)

        st.markdown("---")

        # --- REKAPITULASI PER TEAM / PROMOTOR ---
        st.markdown("### 👥 Rekapitulasi Berdasarkan Team / Promotor")
        df_rekap_team = st.session_state.df_transaksi.groupby("Team/Promotor").agg({
            "Terjual": "sum",
            "Total Setoran Kanvas": "sum",
            "Total Setoran Konsumen": "sum"
        }).reset_index()
        st.dataframe(df_rekap_team, use_container_width=True)

        st.divider()

        # Menu Hapus Data Spesifik
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
        del_bon_id = st.selectbox("Pilih No Bon yang ingin dihapus total", options=["-"] + bon_ids, key="select_del_bon")
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
