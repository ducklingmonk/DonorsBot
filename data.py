# List of questions
QUESTIONS = [
    "Регистрация в личном кабинете донора РНИМУ",
    "Регистрация на донорскую акцию",
    "Противопоказания",
    "Как до нас добраться",
    "Диета донора ДО донации",
    "Диета донора ПОСЛЕ донации",
]

# Answers to questions
REPLIES = {
    "Регистрация в личном кабинете донора РНИМУ":
        """
        1. В интернете заходим на сайт «Личный кабинет донора РНИМУ»: https://paper.rsmu.ru/donor/user/register
        2. Находим поле «Регистрация» и нажимаем
        3. Вводим все данные, согласно образцу и личным документам
        4. Соглашаемся на «Разрешение ФГАОУ ВО РНИМУ им.Н.И.Пирогова обработку представленных данных» и «Я подтверждаю достоверность введенных мною данных»
        5. Нажимаем на кнопку «Зарегистрироваться»
        6. Нас переносит на начальную страницу входа
        7. На почту Вам придет письмо с ссылкой, по которой нужно пройти и заполнить новый пароль 
        8. После этого перейти на начальную страницу 
        9. Вводим придуманный логин и пароль со своей почты
        10. Успешно заходим в личный кабинет и регистрируемся на акцию!
        Успешной сдачи крови!""",

    "Регистрация на донорскую акцию": "Ответ в разработке",

    "Противопоказания": """
    Временные противопоказания:
    •	Масса тела менее 50 кг
    •	Индекс массы тела Менее 18,5 и более 40
    •	Гемоглобин менее 120 Ж и 130 М г/л
    •	Температура тела выше 37 °С
    •	Оперативные вмешательства, 120 календарных дней со дня оперативного вмешательства
    •	Лечебные и косметические процедуры с нарушением кожного покрова (пирсинг, иглоукалывание и иное)
    •	120 календарных дней с момента окончания процедур
    •	Перенесенные инфекционные и паразитарные заболевания, 120 календарных дней после выздоровления
    •	Аллергические заболевания в стадии обострения (60 календарных дней после купирования острого периода)
    •	Период беременности, лактации (1 год после родов, 90 календарных дней после окончания лактации)
    •	Вакцинация: прививка инактивированными вакцинами (в том числе, против столбняка, дифтерии, коклюша, паратифа, холеры, гриппа), анатоксинами (10 календарных дней после вакцинации)
    •	Вакцинация: прививка живыми вакцинами (бруцеллез, оспа, краснуха, полиомиелит, вакцина БЦЖ), рекомбинантными вакцинами (от COVID-19, гепатита В)- 30 календарных дней

Также существуют постоянные противопоказания:

    Инфекционные:
    •	СПИД, носительство ВИЧ-инфекции;
    •	Сифилис, врожденный или приобретенный;
    •	Вирусные гепатиты;
    •	Туберкулез, все формы;

    Соматические заболевания:
    •	Злокачественные новообразования;
    •	Болезни крови;
    •	Органические заболевания ЦНС;
    •	Психические заболевания;
    •	Наркомания, алкоголизм;

    Сердечно-сосудистые заболевания:
    •	Гипертоническая болезнь ІІ-ІІІ ст.;
    •	Ишемическая болезнь сердца;
    •	Атеросклероз, атеросклеротический кардиосклероз;
    •	Облитерирующий эндоартериит, неспецифический аортоартериит, рецидивирующий тромбофлебит;
    •	Эндокардит, миокардит;
    •	Порок сердца;

    Болезни органов дыхания:
    •	Бронхиальная астма;
    •	Бронхоэктатическая болезнь, эмфизема легких, обструктивный бронхит, диффузный пневмосклероз встали декомпенсации;

    Болезни органов пищеварения:
    •	Ахилический гастрит;
    •	Хронические заболевания печени, в том числе токсической природы и неясной этиологии;
    •	Калькулезный холецистит с повторяющимися приступами и явлениями холангита;""",

    "Как до нас добраться": "Ответ находится в разработке",

    "Диета донора ДО донации":
        """Для скорейшего восстановления организма и состава крови после совершенной кроводачи донору рекомендуется включить в рацион продукты, богатые железом, белком и кальцием: 
    •	Мясо, птица, рыба, морепродукты, яйца.
    •	Молоко, кефир, сметана, творог, сыры.
    •	Фасоль, горох, соя, чечевица, кукуруза, гречка.
    •	Шпинат, яблоки, гранат.
    •	Орехи, кунжут.
    •	Петрушка, зелень.
    Также для восстановления объема крови необходимо употреблять достаточное количество жидкости (чай, вода, компоты, соки).
    Для избежания обезвоживания следует воздержаться от употребления соленой пищи и алкогольных напитков!
    Соблюдение данных рекомендаций после донации позволит организму как можно скорее восстановиться после кровопотери, а в будущем избежать временных отводов по причине низкого уровня гемоглобина.""",

    "Диета донора ПОСЛЕ донации":
        """
    Перед сдачей крови донору необходимо соблюдать определенную диету!
    За 2-3 дня до планируемой сдачи крови необходимо воздержаться от употребления следующих продуктов:
    •	Жареных, копченых и острых блюд, специй;
    •	Молочных продуктов, яиц;
    •	Колбасных изделий, сосисок;
    •	Сладких газированных напитков;
    •	Продуктов с высоким содержанием красителей, консервантов и усилителей вкуса (чипсы, сухарики, магазинные соусы);
    •	Орехов, семечек и халвы;
    •	Бананов и цитрусов.
    Также за 48 часов до планируем донации необходимо исключить употребление алкоголя!
    Не забывайте о соблюдении водного баланса. Не менее 30 грамм на килограмм веса. Не обязательно пить залпом, просто понемногу в течение дня. 
    Соблюдение данной диеты поможет сохранить качество компонентов крови и избежать ложноположительных результатов лабораторных анализов.""",
}
