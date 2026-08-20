from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # главная страница и быстрые действия
    path('', views.main, name='main'),
    path('quick_booking/', views.quick_booking, name='quick_booking'),
    path('workplace_status/', views.workplace_status, name='workplace_status'),
    path('tariffs/', views.tariffs_view, name='tariffs'),
    path('reviews/', views.reviews_view, name='reviews'),

    # пользователи
    path('register/', views.register, name='register'),
    path(
        'login/',
        auth_views.LoginView.as_view(
            template_name='booking/login.html',
            redirect_authenticated_user=True  # если уже залогинен, сразу на main
        ),
        name='login'
    ),
    path('logout/', views.logout_view, name='logout'),  # использует кастомный logout_view

    # роли
    path('mechanic/computers/', views.mechanic_computers, name='mechanic_computers'),
    path('mechanic/parts/', views.mechanic_parts, name='mechanic_parts'),
    path('operator/bookings/', views.operator_bookings, name='operator_bookings'),
    path('operator/create/booking/', views.operator_create_booking, name='operator_create_booking'),
    path('operator/create/user', views.operator_create_user, name='operator_create_user'),

    # бронирование
    path('booking/', views.booking, name='booking'),
    path('api/workplace-availability/', views.workplace_availability, name='workplace_availability'),

    # профиль и история
    path('profile/', views.profile, name='profile'),

    # новый API для проверки брони по UUID
    path('booking/check/', views.booking_check, name='booking_check'),

    # обновление брони
    path('booking/update/<int:booking_id>/', views.booking_update, name='booking_update'),
]