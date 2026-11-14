# ================= TAB 1: INPUT TRANSAKSI =================
with tab1:
    st.subheader("📝 Form Pencatatan Harian Transaksi & Stok")
    st.markdown("Pilih Nomor Bon untuk menampilkan otomatis seluruh merk rokok sesuai layout.")

    if "trx_form_reset_id" not in st.session_state:
        st.session_state.trx_form_reset_id = 0

    if "last_trx_msg" in st.session_state and st.session_state["last_trx_msg"]:
        st.success(st.session_state.pop("last_trx_msg"))

    # Filter nomor bon: Saring bon yang sudah pernah di-entry ke df_transaksi
    all_bons = []
    if not st.session_state.df_bon.empty:
        all_bons = st.session_state.df_bon["ID"].unique().tolist()
    
    used_bons = []
    if not st.session_state.df_transaksi.empty and "No Bon" in st.session_state.df_transaksi.columns:
        used_bons = st.session_state.df_transaksi["No Bon"].unique().tolist()

    available_bons = [b for b in all_bons if b not in used_bons]

    # Inisialisasi session state untuk menyimpan nilai terpilih jika belum ada
    if "selected_bon_dropdown" not in st.session_state:
        st.session_state.selected_bon_dropdown = "- Manual Input -"

    # Fungsi callback saat dropdown bon diubah
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
        "🔍 Cari / Pilih No Bon", 
        options=["- Manual Input -"] + available_bons,
        key=f"select_bon_trx_{st.session_state.trx_form_reset_id}",
        on_change=update_bon_fields
    )

    # Ambil nilai awal untuk teks input berdasarkan pilihan
    default_no_bon = ""
    default_nama = ""
    if selected_bon_id != "- Manual Input -" and not st.session_state.df_bon.empty:
        matched_row = st.session_state.df_bon[st.session_state.df_bon["ID"] == selected_bon_id]
        if not matched_row.empty:
            default_no_bon = selected_bon_id
            default_nama = matched_row.iloc[0]["Team/Promotor"]

    # Pastikan session state untuk text_input terisi jika baru dipilih
    text_bon_key = f"no_bon_in_{st.session_state.trx_form_reset_id}"
    text_nama_key = f"nama_in_{st.session_state.trx_form_reset_id}"
    
    if text_bon_key not in st.session_state:
        st.session_state[text_bon_key] = default_no_bon
    if text_nama_key not in st.session_state:
        st.session_state[text_nama_key] = default_nama

    col_h1, col_h2 = st.columns(2)
    with col_h1:
        st.markdown("**No Bon**")
        input_no_bon = st.text_input(
            "No Bon Input", 
            key=text_bon_key,
            label_visibility="collapsed"
        )
    with col_h2:
        st.markdown("**Nama**")
        input_nama = st.text_input(
            "Nama Input", 
            placeholder="Nama Promotor / Team", 
            key=text_nama_key,
            label_visibility="collapsed"
        )

    st.markdown("---")

    active_merks = []
    current_active_bon = st.session_state.get(text_bon_key, "")
    if current_active_bon and not st.session_state.df_bon.empty:
        selected_bon_rows = st.session_state.df_bon[st.session_state.df_bon["ID"] == current_active_bon]
        if not selected_bon_rows.empty:
            active_merks = selected_bon_rows["Merk Rokok"].tolist()
    
    if not active_merks:
        active_merks = list_merk[:3]

    with st.form(f"form_transaksi_layout_{st.session_state.trx_form_reset_id}", clear_on_submit=True):
        
        st.markdown("**Pilih Merk Rokok yang akan diinput transaksinya** | **Stock Awal (dalam satuan Bungkus)**")
        stok_awal_inputs = {}
        for merk in active_merks:
            default_val = 0
            if current_active_bon and not st.session_state.df_bon.empty:
                matched = st.session_state.df_bon[(st.session_state.df_bon["ID"] == current_active_bon) & (st.session_state.df_bon["Merk Rokok"] == merk)]
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
            final_input_bon = st.session_state.get(text_bon_key, "")
            final_input_nama = st.session_state.get(text_nama_key, "")

            if not final_input_bon:
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
                        "No Bon": final_input_bon,
                        "Tanggal": str(selected_date),
                        "Minggu": current_week,
                        "Team/Promotor": final_input_nama if final_input_nama else "Tanpa Nama",
                        "Merk Rokok": merk,
                        "Stok Awal": s_awal,
                        "Stok Akhir": s_akhir,
                        "Belum Selesai": s_gantung,
                        "Bon Qty": s_lain,
                        "Keperluan Bon": f"Bon [{final_input_bon}]",
                        "Terjual": terjual,
                        "Harga Kanvas": h_kanvas,
                        "Harga Konsumen": h_konsumen,
                        "Total Setoran Kanvas": tot_kanvas,
                        "Total Setoran Konsumen": tot_konsumen
                    }
                    st.session_state.df_transaksi = pd.concat([st.session_state.df_transaksi, pd.DataFrame([new_row])], ignore_index=True)
                    saved_count += 1

                st.session_state.trx_form_reset_id += 1
                # Bersihkan juga state key teks agar form bersih total
                if text_bon_key in st.session_state:
                    del st.session_state[text_bon_key]
                if text_nama_key in st.session_state:
                    del st.session_state[text_nama_key]

                st.session_state["last_trx_msg"] = f"✅ Berhasil menyimpan {saved_count} data transaksi untuk No Bon **{final_input_bon}**!"
                st.rerun()
