from datetime import timedelta
from decimal import Decimal
from django.utils import timezone
from .models import Booking

# функция для проверки доступности и стоимости
def check_availability_and_calculate_cost(user, workplace, start_time, end_time, tariff):
    # если datetime "naive", делаем aware
    if timezone.is_naive(start_time):
        start_time = timezone.make_aware(start_time)
    if timezone.is_naive(end_time):
        end_time = timezone.make_aware(end_time)

    # проверяем пересечение
    overlapping = Booking.objects.filter(
        workplace=workplace,
        start_time__lt=end_time,
        end_time__gt=start_time
    ).exists()

    if overlapping:
        return False, Decimal('0.00')

    # расчёт стоимости
    duration = end_time - start_time
    hours = Decimal(duration.total_seconds() / 3600)
    cost = hours * tariff.price_per_hour

    return True, cost