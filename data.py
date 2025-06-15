MENU_TREE = {
    "Донорство компонентов крови": {
        "Донорство плазмы": "plasma_donation",
        "Донорство тромбоцитов": "platelets_donation",
        "Донорство гранулоцитов": "granulocytes_donation",
    },
    "Kell+": {
        "_answer": "kell_is", #Что это и для чего?
        "У меня Kell+ Я могу быть донором?": {
            "_answer": "kell_donation",
            "Донорство компонентов крови": {
                "Донорство плазмы": "plasma_donation",
                "Донорство тромбоцитов": "platelets_donation",
                "Донорство гранулоцитов": "granulocytes_donation",
            }
        }
    },
    "РДКМ": {
        "_answer": "rdkm_info",
        "Вступление в РДКМ": {
            "Где я могу вступить в РДКМ?": "where_join_rdkm",
            "Противопоказания для вступления": {
                "Абсолютные": "absolute_contr_rdkm",
                "Относительные": "relative_contr_rdkm",
            }
        },
    },
    "Где мы?": "location",
    "Акции": {
        "Регистрация": {
            "Регистрация в личном кабинете": "reg_lk",
            "Регистрация на акцию": "reg_event"
        },
        "Питание": {
            "Питание до донации": "food_before",
            "Питание в день сдачи крови": "food_donation_day",
            "Питание после донации": "food_after",
        },
        "Противопоказания к донации": {
            "Постоянные": {
                "Заболевания ССС": "sss",
                "Болезни органов пищеварения": "digestion",
                "Заболевания печени и желчи": "liver",
                "Заболевания почек и мочевыводящих путей": "kidney",
                "Болезни органов дыхания": "breathing",
                "Комные болезни": "eye",
                "Заболевания ЛОР-органов": "lor",
                "Другое": "other_perm"
            },
            "Временные": {
                "Физические показатели": "phys",
                "Лабораторные показатели": "labs",
                "Различные манипуляции": "manipul",
                "Перенесенные инфекционные заболевания": "infbol",
                "Соматические заболевания": "somabol",
                "Вакцинация": "vaccine",
                "Прием лекарственных препаратов": "medicine",
            },
            "Гематотрансмиссивные заболевания (могут передаваться донорской кровью и ее компонентами)": {
                "Инфекционные": "bloodborne_inf",
                "Паразитарные": "bloodborne_par"
            }
        },
        "Календарь": {
            "_answer": "calendar",
            "Мероприятия в ближайшее время": "events"
        },
        "Почетный донор": {
            "Почетный донор Москвы": "moscow_donor",
            "Почетный донор России": "russia_donor"
        },
        "Информационная помощь донорам": "donor_info_help"
    },
}


ANSWERS = {
    "plasma_donation": "..",
    "platelets_donation": "..",
    "granulocytes_donation": "..",
    "kell_is": ".",
    "kell_donation": "...",
    "rdkm_info": "..",
    "where_join_rdkm": "...",
    "absolute_contr_rdkm": "...",
    "relative_contr_rdkm": "...",
    "location": "...",
    "reg_lk": "...",
    "reg_event": "...",
    "food_before": "...",
    "food_donation_day": "...",
    "food_after": "...",
    "sss": "...",
    "digestion": "...",
    "liver": "...",
    "kidney": "...",
    "breathing": "...",
    "eye": "...",
    "lor": "...",
    "other_perm": "...",
    "phys": "...",
    "labs": "...",
    "manipul": "...",
    "infbol": "...",
    "somabol": "...",
    "vaccine": "...",
    "medicine": "...",
    "bloodborne_inf": "...",
    "bloodborne_par": "...",
    "calendar": {
        "text": "Вот календарь мероприятий 📅",
        "photo_url": "https://i.ibb.co/xc5MKqX/Untitled.png" #вместо размещения фото на этом сайтике, можно разместить на каком-нибудь другом либо
        #закомменти/удали строку "photo_url" и просто тогда в text укажи ссылку на календарь как обычно...
    },
    "events": "...",
    "moscow_donor": "...",
    "russia_donor": "...",
    "donor_info_help": "..."
}

