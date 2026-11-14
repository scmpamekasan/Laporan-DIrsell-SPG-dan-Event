from datetime import datetime

def get_current_week_label(target_date=None):
    if target_date is None:
        target_date = datetime.now()
    # Mengambil nomor minggu dalam tahun (ISO week)
    week_num = target_date.isocalendar()[1]
    year = target_date.isocalendar()[0]
    return f"Minggu ke-{week_num} ({year})"

def format_date_indo(date_obj):
    days = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
    months = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Ags", "Sep", "Okt", "Nov", "Des"]
    
    d_name = days[date_obj.weekday()]
    d = date_obj.day
    m = months[date_obj.month - 1]
    y = date_obj.year
    return f"{d_name}, {d} {m} {y}"
