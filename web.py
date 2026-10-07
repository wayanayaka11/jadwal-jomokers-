import streamlit as st
import json
from datetime import datetime, date, timedelta
from waktu import cari_jadwal_kumpul, load_data

st.set_page_config(page_title="infokan KK", page_icon="📅", layout="centered")

def save_data(data):
    with open('jadwal_sekolah.json', 'w') as file:
        json.dump(data, file, indent=2)

st.title("🎉 infokan KK")
st.caption("Aplikasi Pencari Waktu Luang Ber-4 (Nay, Sean, Vian, & Rey)")

data = load_data()

# --- LOGIN ---
if "user_login" not in st.session_state:
    st.session_state["user_login"] = None

if st.session_state["user_login"] is None:
    st.subheader("🔑 Login Pengguna")
    selected_user = st.selectbox("Pilih Nama Anda:", list(data["users"].keys()))
    input_pin = st.text_input("Masukkan PIN:", type="password")
    
    if st.button("Login"):
        if input_pin == data["users"][selected_user]["pin"]:
            st.session_state["user_login"] = selected_user
            st.success(f"Selamat datang, {selected_user}!")
            st.rerun()
        else:
            st.error("PIN salah! Silakan coba lagi.")
else:
    current_user = st.session_state["user_login"]
    sekolah_user = data["users"][current_user]["sekolah"]
    
    st.sidebar.markdown(f"### 👤 Akun Aktif")
    st.sidebar.write(f"**Nama:** {current_user}")
    st.sidebar.write(f"**Sekolah:** {sekolah_user}")
    if st.sidebar.button("Logout"):
        st.session_state["user_login"] = None
        st.rerun()

    tab1, tab2, tab3, tab4 = st.tabs(["📅 Kalender Status", "⚽ Les / Extra", "🚫 Ijin / Acara", "🏫 Libur Sekolah"])

    # --- TAB 1: KALENDER STATUS (WAKTU) ---
    with tab1:
        st.subheader("📅 waktu")
        st.markdown("""
        **Keterangan Warna Kalender:**
        * 🔴 **Merah:** < 2 Jam / Pasti Ada Halangan
        * 🔵 **Biru:** **sikon** (Ada acara/jadwal yang belum fix)
        * 🟠 **Orange:** 2 s/d < 4 Jam Free
        * 🟢 **Hijau:** 4 s/d < 6 Jam Free
        * ⚪ **Putih:** 6 s/d 12+ Jam Free (Libur / Bebas)
        """)
        
        col_a, col_b = st.columns(2)
        with col_a:
            tgl_mulai = st.date_input("Dari Tanggal:", value=date.today())
        with col_b:
            tgl_akhir = st.date_input("Sampai Tanggal:", value=date.today() + timedelta(days=14))

        if st.button("Cek Kalender Status 🔍", type="primary"):
            st.write("---")
            curr = tgl_mulai
            
            while curr <= tgl_akhir:
                tgl_str = str(curr)
                hasil = cari_jadwal_kumpul(tgl_str)
                kat = hasil["kategori"]
                
                if kat == "biru":
                    st.info(f"🔵 **{hasil['hari']}, {tgl_str}** → **sikon** ({hasil['alasan']})")
                elif kat == "putih":
                    st.write(f"⚪ **{hasil['hari']}, {tgl_str}** → **LELUASA ({hasil['durasi_jam']} Jam Free)** | ⏰ {hasil['jam_mulai']} - {hasil['jam_selesai']} WITA")
                elif kat == "hijau":
                    st.success(f"🟢 **{hasil['hari']}, {tgl_str}** → **BISA KUMPUL ({hasil['durasi_jam']} Jam Free)** | ⏰ {hasil['jam_mulai']} - {hasil['jam_selesai']} WITA")
                elif kat == "orange":
                    st.warning(f"🟠 **{hasil['hari']}, {tgl_str}** → **SINGKAT ({hasil['durasi_jam']} Jam Free)** | ⏰ {hasil['jam_mulai']} - {hasil['jam_selesai']} WITA")
                else:  # merah
                    st.error(f"🔴 **{hasil['hari']}, {tgl_str}** → **TIDAK BISA** ({hasil['alasan']})")
                    
                with st.expander(f"🔍 Detail Jam Bebas Masing-Masing ({tgl_str})"):
                    for orang, detail in hasil["rincian"].items():
                        st.write(f"• **{orang}**: Bebas jam {detail['jam_free']} ({detail['catatan']})")
                
                curr += timedelta(days=1)

    # --- TAB 2: KEGIATAN RUTIN ---
    with tab2:
        st.subheader(f"Kelola Les & Extra Rutin")
        st.write(f"**Tambah Kegiatan Rutin ({current_user}):**")
        nama_kegiatan = st.text_input("Nama Kegiatan:")
        hari_kegiatan = st.selectbox("Hari:", ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"])
        
        c1, c2 = st.columns(2)
        with c1:
            jam_mulai_les = st.time_input("Jam Mulai:", value=datetime.strptime("15:30", "%H:%M").time())
        with c2:
            jam_selesai_les = st.time_input("Jam Selesai:", value=datetime.strptime("17:00", "%H:%M").time())

        if st.button("Simpan Kegiatan Rutin"):
            if nama_kegiatan:
                kegiatan_baru = {
                    "nama_kegiatan": nama_kegiatan,
                    "hari": hari_kegiatan,
                    "jam_mulai": jam_mulai_les.strftime("%H:%M"),
                    "jam_selesai": jam_selesai_les.strftime("%H:%M")
                }
                data["kegiatan_rutin"][current_user].append(kegiatan_baru)
                save_data(data)
                st.success("Kegiatan rutin disimpan!")
                st.rerun()

        st.write("---")
        st.write("📋 **Daftar Les / Extra Seluruh Anggota:**")
        for u in data["users"].keys():
            st.markdown(f"**{u}:**")
            kegiatans = data["kegiatan_rutin"].get(u, [])
            if not kegiatans:
                st.caption("Tidak ada kegiatan rutin.")
            else:
                for idx, item in enumerate(kegiatans):
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        st.write(f"• **{item['nama_kegiatan']}** ({item['hari']}: {item['jam_mulai']} - {item['jam_selesai']})")
                    with col2:
                        if u == current_user:
                            if st.button("🗑️ Hapus", key=f"del_les_{u}_{idx}"):
                                data["kegiatan_rutin"][u].pop(idx)
                                save_data(data)
                                st.rerun()

    # --- TAB 3: IJIN / ACARA ---
    with tab3:
        st.subheader("Kelola Halangan / Acara Tanggal Khusus")
        st.write(f"**Tambah Catatan Tanggal ({current_user}):**")
        tgl_ijin = st.date_input("Pilih Tanggal:", min_value=date.today(), key="ijin_tgl")
        keterangan_ijin = st.text_input("Keterangan:")
        
        is_tentative = st.checkbox("❓ Status sikon (Ragu-Ragu / Biru)")
        
        if st.button("Simpan Catatan Tanggal"):
            if keterangan_ijin:
                acara_baru = {
                    "tanggal": str(tgl_ijin), 
                    "keterangan": keterangan_ijin,
                    "tentative": is_tentative
                }
                data["acara_manual"][current_user].append(acara_baru)
                save_data(data)
                st.success("Catatan tanggal berhasil dicatat!")
                st.rerun()

        st.write("---")
        st.write("📋 **Daftar Halangan / Catatan Seluruh Anggota:**")
        for u in data["users"].keys():
            st.markdown(f"**{u}:**")
            acaras = data["acara_manual"].get(u, [])
            if not acaras:
                st.caption("Tidak ada catatan.")
            else:
                for idx, item in enumerate(acaras):
                    col1, col2 = st.columns([4, 1])
                    status_text = "🔵 [SIKON]" if item.get("tentative", False) else "🔴 [FIX HALANGAN]"
                    with col1:
                        st.write(f"• **{item['tanggal']}**: {item['keterangan']} {status_text}")
                    with col2:
                        if u == current_user:
                            if st.button("🗑️ Hapus", key=f"del_ijin_{u}_{idx}"):
                                data["acara_manual"][u].pop(idx)
                                save_data(data)
                                st.rerun()

    # --- TAB 4: LIBUR SEKOLAH ---
    with tab4:
        st.subheader(f"Kelola Libur Sekolah ({sekolah_user})")
        tgl_libur_sekolah = st.date_input("Tanggal Libur Baru:", min_value=date.today(), key="libur_sch")
        
        if st.button("Tandai Sekolah Libur"):
            if str(tgl_libur_sekolah) not in data["sekolah"][sekolah_user]["tanggal_libur"]:
                data["sekolah"][sekolah_user]["tanggal_libur"].append(str(tgl_libur_sekolah))
                save_data(data)
                st.success(f"Tanggal {tgl_libur_sekolah} ditandai libur!")
                st.rerun()

        st.write("---")
        st.write(f"📋 **Daftar Hari Libur {sekolah_user}:**")
        daftar_libur = data["sekolah"][sekolah_user]["tanggal_libur"]
        if not daftar_libur:
            st.caption("Belum ada tanggal libur yang terdaftar.")
        else:
            for tgl in daftar_libur:
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"📅 **{tgl}**")
                with col2:
                    if st.button("🗑️ Hapus", key=f"del_{tgl}"):
                        data["sekolah"][sekolah_user]["tanggal_libur"].remove(tgl)
                        save_data(data)
                        st.rerun()
