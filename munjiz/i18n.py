import re
from datetime import datetime

_ARABIC = re.compile(r"[؀-ۿ]")
_LATIN = re.compile(r"[A-Za-z]")

AR_WEEKDAYS = ["الاثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة", "السبت", "الأحد"]
AR_MONTHS = ["يناير", "فبراير", "مارس", "أبريل", "مايو", "يونيو",
             "يوليو", "أغسطس", "سبتمبر", "أكتوبر", "نوفمبر", "ديسمبر"]


def detect_lang(text: str) -> str:
    return "ar" if len(_ARABIC.findall(text)) > len(_LATIN.findall(text)) else "en"


def fmt_dt(value: str | datetime | None, lang: str) -> str:
    if not value:
        return "—"
    dt = datetime.fromisoformat(value) if isinstance(value, str) else value
    if lang == "ar":
        hour = dt.hour % 12 or 12
        period = "مساءً" if dt.hour >= 12 else "صباحًا"
        return f"{AR_WEEKDAYS[dt.weekday()]} {dt.day} {AR_MONTHS[dt.month - 1]}، {hour}:{dt.minute:02d} {period}"
    return dt.strftime("%a %d %b, %H:%M")


# Agent replies and UI labels.
T = {
    "followup_intro": {
        "en": "Almost there. To send this to all desks in one go, I need:",
        "ar": "باقي القليل. حتى أرسل الطلب لجميع الجهات دفعة واحدة، أحتاج:",
    },
    "problems_intro": {
        "en": "A few things need changing before I can submit:",
        "ar": "هناك أمور تحتاج تعديلًا قبل الإرسال:",
    },
    "summary_intro": {
        "en": "Here's what I'll submit under **one ticket**:",
        "ar": "هذا ما سأرسله تحت **تذكرة واحدة**:",
    },
    "summary_outro": {
        "en": "Shall I submit it?",
        "ar": "هل أرسله؟",
    },
    "nothing_understood": {
        "en": "I can handle deliveries, worker permits and power or facility requests for your pavilion. What do you need?",
        "ar": "أستطيع ترتيب التوصيلات وتصاريح العمال وطلبات الكهرباء والمرافق لجناحك. ماذا تحتاج؟",
    },
    "for_workers": {"en": "{n} workers", "ar": "عددهم {n}"},
    "submitted": {
        "en": "Submitted. Your ticket is **{ticket}**. Each desk reviews its part and you'll see every approval here.",
        "ar": "تم الإرسال. رقم تذكرتك **{ticket}**. كل جهة تراجع الجزء الخاص بها وستظهر الموافقات هنا.",
    },
    "staff_note": {"en": "Note for desk", "ar": "ملاحظة للجهة"},
}


def t(key: str, lang: str, **kw) -> str:
    return T[key][lang].format(**kw)
