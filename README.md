# Club Booking

Дипломный проект — веб-приложение для бронирования рабочих мест в компьютерном клубе.

## Возможности

* регистрация и авторизация пользователей;
* бронирование рабочих мест;
* проверка занятости мест;
* назначение роли пользователей: клиент, оператор, механик;
* управление компьютерами и комплектующими;
* тарифы и расчёт стоимости бронирования;
* отзывы;
* Django Admin.

## Стек

* Python
* Django
* SQLite
* HTML
* Django ORM

## Структура

```text
booking/
├── models.py       # модели и работа с данными
├── views.py        # обработка запросов
├── forms.py        # формы и валидация
├── urls.py         # маршруты
├── permissions.py  # проверка ролей
└── admin.py        # Django Admin
```

## Запуск

```bash
git clone https://github.com/danyamini/club-booking.git
cd club-booking
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

После запуска:

```text
http://127.0.0.1:8000/
```
