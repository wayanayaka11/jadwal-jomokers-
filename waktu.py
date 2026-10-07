import json
from datetime import datetime, timedelta

def load_data():
    with open('jadwal_sekolah.json', 'r') as file:
        return json.load(file)

def time_to_minutes(time_str):
    h, m = map(int, time_str.split(':'))
    return h * 60 + m

def minutes_to_time(minutes):
    h = minutes // 60
    m = minutes % 60
    return f"{h:02d}:{m:02d}"

def cari_jadwal_kumpul(tanggal_str, buffer_perjalanan=30, min_bisa_kumpul_jam=2.0, max_jam_malam="19:30"):
    data = load_data()
    tgl_obj = datetime.strptime(tanggal_str, "%Y-%m-%d")
    nama_hari = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"][tgl_obj.weekday()]
    
    jam_mulai_bebas_per_orang = []
    rincian_orang = {}
    batas_maksimal_menit = time_to_minutes(max_jam_malam)
    ada_halangan_fix = False
    ada_halangan_tentative = False
    alasan_tentative_list = []

    for user, info in data["users"].items():
        sekolah_user = info["sekolah"]
        alasan_user = []
        
        # 1. Cek Libur Sekolah
        if tanggal_str in data["sekolah"][sekolah_user]["tanggal_libur"]:
            jam_mulai = 0
            alasan_user.append("Sekolah Libur")
        else:
            jam_pulang_str = data["sekolah"][sekolah_user]["jam_pulang"][nama_hari]
            jam_mulai = time_to_minutes(jam_pulang_str)
            if jam_mulai > 0:
                alasan_user.append(f"Pulang sekolah jam {jam_pulang_str}")

        if jam_mulai > 0:
            jam_mulai += buffer_perjalanan

        # 2. Cek Acara Manual / Halangan
        halangan_manual = False
        for acara in data["acara_manual"].get(user, []):
            if acara["tanggal"] == tanggal_str:
                if acara.get("tentative", False):
                    ada_halangan_tentative = True
                    alasan_tentative_list.append(f"{user}: {acara['keterangan']}")
                    alasan_user.append(f"Ragu-Ragu ({acara['keterangan']})")
                else:
                    halangan_manual = True
                    ada_halangan_fix = True
                    alasan_user.append(f"Acara: {acara['keterangan']}")

        # 3. Cek Les / Extra
        if not halangan_manual:
            for rutin in data["kegiatan_rutin"].get(user, []):
                if rutin["hari"] == nama_hari:
                    ada_ijin = any(
                        ijin["nama_kegiatan"] == rutin["nama_kegiatan"] and ijin["tanggal"] == tanggal_str 
                        for ijin in data["ijin_rutin"].get(user, [])
                    )
                    if not ada_ijin:
                        jam_selesai_les = time_to_minutes(rutin["jam_selesai"]) + buffer_perjalanan
                        if jam_selesai_les > jam_mulai:
                            jam_mulai = jam_selesai_les
                        alasan_user.append(f"{rutin['nama_kegiatan']} ({rutin['jam_mulai']}-{rutin['jam_selesai']})")
                    else:
                        alasan_user.append(f"Izin {rutin['nama_kegiatan']}")

        jam_mulai_bebas_per_orang.append(jam_mulai)
        rincian_orang[user] = {
            "jam_free": minutes_to_time(jam_mulai) if jam_mulai > 0 else "00:00 (Bebas)",
            "halangan": halangan_manual,
            "catatan": ", ".join(alasan_user) if alasan_user else "Bebas"
        }

    jam_mulai_bersama = max(jam_mulai_bebas_per_orang)
    durasi_tersisa_menit = batas_maksimal_menit - jam_mulai_bersama
    durasi_jam = round(durasi_tersisa_menit / 60, 1)

    # Prioritas 1: Jika ada halangan FIX
    if ada_halangan_fix or durasi_jam < min_bisa_kumpul_jam:
        return {
            "status": False,
            "kategori": "merah",
            "hari": nama_hari,
            "durasi_jam": max(0, durasi_jam),
            "rincian": rincian_orang,
            "alasan": f"Kurang dari 2 jam / Ada halangan pasti."
        }

    # Prioritas 2: Jika ada yang RAGU-RAGU / BELUM PASTI -> BIRU 🔵
    if ada_halangan_tentative:
        return {
            "status": True,
            "kategori": "biru",
            "tanggal": tanggal_str,
            "hari": nama_hari,
            "jam_mulai": minutes_to_time(jam_mulai_bersama),
            "jam_selesai": max_jam_malam,
            "durasi_jam": durasi_jam,
            "rincian": rincian_orang,
            "alasan": ", ".join(alasan_tentative_list)
        }

    # Prioritas 3: Kategori berdasarkan Durasi Normal
    if 2.0 <= durasi_jam < 4.0:
        kategori = "orange"
    elif 4.0 <= durasi_jam < 6.0:
        kategori = "hijau"
    else:
        kategori = "putih"

    return {
        "status": True,
        "kategori": kategori,
        "tanggal": tanggal_str,
        "hari": nama_hari,
        "jam_mulai": minutes_to_time(jam_mulai_bersama),
        "jam_selesai": max_jam_malam,
        "durasi_jam": durasi_jam,
        "rincian": rincian_orang
    }