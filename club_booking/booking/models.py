from django.db import models
from django.contrib.auth.models import User
import uuid


# статусы компьютеров
STATUS_CHOICES = [
    ('working', 'Работает'),
    ('broken', 'Не работает'),
    ('glitch', 'Глючит'),
]


# статусы бронирования
BOOKING_STATUS_CHOICES = [
    ('pending', 'В ожидании'),
    ('confirmed', 'Подтверждено'),
    ('rejected', 'Отклонено'),
]


# модель ролей
class Role(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name


# модель рабочего места
class Workplace(models.Model):
    name = models.CharField(max_length=50)
    description = models.TextField(blank=True)
    row = models.PositiveIntegerField(default=1)
    number = models.PositiveIntegerField(default=1)

    def __str__(self):
        return self.name

    def current_computer(self):
        return self.computer_set.first()


# модель CPU
class CPU(models.Model):
    name = models.CharField(max_length=100)
    identifier = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return f"{self.name} ({self.identifier})"


# модель GPU
class GPU(models.Model):
    name = models.CharField(max_length=100)
    identifier = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return f"{self.name} ({self.identifier})"


# модель RAM
class RAM(models.Model):
    name = models.CharField(max_length=100)
    identifier = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return f"{self.name} ({self.identifier})"


# модель storage
class Storage(models.Model):
    name = models.CharField(max_length=100)
    identifier = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return f"{self.name} ({self.identifier})"


# модель компьютера
class Computer(models.Model):
    name = models.CharField(max_length=50)
    workplace = models.ForeignKey(Workplace, on_delete=models.SET_NULL, null=True, blank=True)

    cpu = models.ForeignKey(CPU, on_delete=models.SET_NULL, null=True, blank=True)
    gpu = models.ForeignKey(GPU, on_delete=models.SET_NULL, null=True, blank=True)
    ram = models.ForeignKey(RAM, on_delete=models.SET_NULL, null=True, blank=True)
    storage = models.ForeignKey(Storage, on_delete=models.SET_NULL, null=True, blank=True)

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='working')

    def __str__(self):
        return self.name


# модель тарифа
class Tariff(models.Model):
    name = models.CharField(max_length=50)
    price_per_hour = models.DecimalField(max_digits=8, decimal_places=2)

    def __str__(self):
        return self.name


# модель бронирования
class Booking(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    workplace = models.ForeignKey(Workplace, on_delete=models.CASCADE)

    start_time = models.DateTimeField()
    end_time = models.DateTimeField()

    tariff = models.ForeignKey(Tariff, on_delete=models.SET_NULL, null=True)

    cost = models.DecimalField(max_digits=8, decimal_places=2, default=0)

    unique_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    status = models.CharField(
        max_length=10,
        choices=BOOKING_STATUS_CHOICES,
        default='pending'
    )

    def __str__(self):
        return f"{self.user.username} - {self.workplace.name}"

# расчет стоимости бронирования
    def save(self, *args, **kwargs):
        duration = (self.end_time - self.start_time).total_seconds() / 3600

        if self.tariff:
            self.cost = duration * float(self.tariff.price_per_hour)
        else:
            self.cost = 0

        super().save(*args, **kwargs)


# модель номера телефона
class PhoneNumber(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    phone_number = models.CharField(max_length=20)

    def __str__(self):
        if self.user:
            return f"{self.user.username} - {self.phone_number}"
        return self.phone_number


# модель отзывов
class Review(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}: {self.content[:20]}"