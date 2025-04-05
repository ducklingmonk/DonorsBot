# Navigation structure (menu tree)
MENU_TREE = {
    "Kell+": {
        "Что это?": "kell_is",  # Reference to answer key
        "Могу ли я быть донором?": "donor_req",
    },
    "РДКБ": "something",
    "РДКМ": {
        "Что это и для чего?": {
            "Для чего?": "rdkm_for",
            "Что это?": "rdkm_is"
        },
        "Где могу вступить?":
            {"РНИМУ": "rnimu",
             "Парт. центры": "part_centers"
             },
        "Противопоказания": "contraindications",
    },
    "Где мы?": "location",
    "Акции": {
        "Питание": {
            "До донации": {
                "Можно": "before_true",
                "Нельзя": "before_false",
            },
            "После донации": {
                "Можно": "after_true",
                "Нельзя": "after_false",
            },
        },
        "Противопоказания": {
            "Постоянные": {
                "ССС": "sss",
                "Пищеварения": "digestion",
                "Инфекции": "infections",
                "Дыхание": "breathing",
                "Психические": "mental",
                "Кровь": "blood"
            },
            "Временные": {  # Changed from string to dict
                "Общие": "temporary_contr"  # Now matches structure
            }
        },
        "Календарь": {
            "Где найти?": "calendar_location",
            "Мероприятия": "events"
        },
        "Регистрация": {
            "На кроводачу": {
                "Видеоматериал": "donation_video",
                "Инструкция": "donation_instruction"
            },
            "В лк донора РНИМУ": {
                "Видеоматериал": "lk_video",
                "Инструкция": "lk_instruction"
            },
        },
    },
}

# All answers in one dictionary
ANSWERS = {
    "kell_is": """.""",
    "donor_req": """.""",
    "something": """.""",
    "rdkm_for": """.""",
    "rdkm_is": """.""",
    "rnimu": """.""",
    "part_centers": """.""",
    "contraindications": """.""",
    "location": """.""",
    "before_true": """.""",
    "before_false": """.""",
    "after_true": """.""",
    "after_false": """.""",
    "sss": """.""",
    "digestion": """.""",
    "infections": """.""",
    "breathing": """.""",
    "mental": """.""",
    "blood": """.""",
    "temporary_contr": """.""",
    "calendar_location": """.""",
    "events": """.""",
    "donation_video": """.""",
    "donation_instruction": """.""",
    "lk_video": """.""",
    "lk_instruction": """."""
}
