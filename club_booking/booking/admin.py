from django.contrib import admin
from .models import Workplace, Computer, Tariff, Booking, CPU, GPU, RAM, Storage, PhoneNumber, Review


# регистрация моделей
@admin.register(Workplace)
class WorkplaceAdmin(admin.ModelAdmin):
    pass


@admin.register(Computer)
class ComputerAdmin(admin.ModelAdmin):
    pass


@admin.register(Tariff)
class TariffAdmin(admin.ModelAdmin):
    pass


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    pass


@admin.register(CPU)
class CPUAdmin(admin.ModelAdmin):
    pass


@admin.register(GPU)
class GPUAdmin(admin.ModelAdmin):
    pass


@admin.register(RAM)
class RAMAdmin(admin.ModelAdmin):
    pass


@admin.register(Storage)
class StorageAdmin(admin.ModelAdmin):
    pass


@admin.register(PhoneNumber)
class PhoneNumberAdmin(admin.ModelAdmin):
    list_display = ('phone_number', 'user')
    search_fields = ('phone_number', 'user__username')


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('user', 'content', 'created_at')
    list_filter = ('created_at', 'user')
    search_fields = ('user__username', 'content')