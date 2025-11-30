# app/utils/shift_helper.py

from datetime import datetime, timedelta, time

def get_current_shift_start(current_dt: datetime) -> datetime:
    """
    Одоогийн цагт харгалзах ээлжийн ЭХЛЭХ цагийг буцаана.
    
    Дүрэм:
    - Ээлж өглөө 08:00 цагт эхэлнэ.
    - Хэрэв одоо 08:00-аас хойш бол (ж: 14:00) -> Өнөөдрийн 08:00
    - Хэрэв одоо 08:00-аас өмнө бол (ж: 02:00) -> Өчигдрийн 08:00
    """
    SHIFT_START_HOUR = 8
    
    # Хэрэв одоогийн цаг 08:00-аас бага бол (шөнийн 00:00 - 07:59)
    # Ээлж нь "Өчигдөр" эхэлсэн гэж үзнэ.
    if current_dt.hour < SHIFT_START_HOUR:
        shift_date = current_dt.date() - timedelta(days=1)
    else:
        # 08:00-аас хойш бол "Өнөөдөр" эхэлсэн гэж үзнэ.
        shift_date = current_dt.date()
        
    # Тухайн өдрийн өглөөний 08:00:00 цагийг үүсгэнэ
    return datetime.combine(shift_date, time(SHIFT_START_HOUR, 0, 0))