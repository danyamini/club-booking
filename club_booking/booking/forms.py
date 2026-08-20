from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from .models import (
    Booking, Tariff, Workplace, Computer,
    CPU, GPU, RAM, Storage, PhoneNumber, Review
)



# стандартная форма для клиента
class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ['workplace', 'tariff', 'start_time', 'end_time']
        labels = {
            'workplace': 'Рабочее место',
            'tariff': 'Тариф',
            'start_time': 'Начало',
            'end_time': 'Конец',
        }

    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get('start_time')
        end = cleaned_data.get('end_time')
        workplace = cleaned_data.get('workplace')

        if start and end:
            if start >= end:
                raise ValidationError("Время начала должно быть меньше времени окончания.")

            overlapping = Booking.objects.filter(
                workplace=workplace,
                start_time__lt=end,
                end_time__gt=start
            )
            if self.instance.pk:
                overlapping = overlapping.exclude(pk=self.instance.pk)

            if overlapping.exists():
                raise ValidationError("Выбранное время пересекается с другим бронированием.")


# форма для создание брони оператором
class QuickBookingForm(forms.ModelForm):
    phone = forms.CharField(max_length=20, required=True, label="Телефон")

    class Meta:
        model = Booking
        fields = ['workplace', 'start_time', 'end_time', 'phone']

    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get('start_time')
        end = cleaned_data.get('end_time')
        workplace = cleaned_data.get('workplace')

        if start and end:
            if start >= end:
                raise ValidationError("Время начала должно быть меньше времени окончания.")

            overlapping = Booking.objects.filter(
                workplace=workplace,
                start_time__lt=end,
                end_time__gt=start
            )
            if self.instance.pk:
                overlapping = overlapping.exclude(pk=self.instance.pk)

            if overlapping.exists():
                raise ValidationError("Выбранное время пересекается с другим бронированием.")


# форма для создани брони оператором с указанием номера тлефона
class OperatorBookingForm(forms.ModelForm):
    client_name = forms.CharField(
        max_length=150,
        required=False,
        label='Имя клиента',
        widget=forms.TextInput(attrs={'placeholder': 'Имя клиента (необязательно)'})
    )
    phone = forms.CharField(
        max_length=20,
        required=True,
        label='Телефон клиента',
        widget=forms.TextInput(attrs={'placeholder': 'Введите номер телефона'})
    )
    user = forms.ModelChoiceField(
        queryset=User.objects.all(),
        required=False,
        label='Пользователь (по желанию)'
    )

    class Meta:
        model = Booking
        fields = ['user', 'client_name', 'phone', 'workplace', 'tariff', 'start_time', 'end_time']
        labels = {
            'workplace': 'Рабочее место',
            'tariff': 'Тариф',
            'start_time': 'Начало',
            'end_time': 'Конец',
        }

    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get('start_time')
        end = cleaned_data.get('end_time')
        workplace = cleaned_data.get('workplace')

        if start and end:
            if start >= end:
                self.add_error('start_time', 'Время начала должно быть меньше времени окончания.')

            overlapping = Booking.objects.filter(
                workplace=workplace,
                start_time__lt=end,
                end_time__gt=start
            )
            if self.instance.pk:
                overlapping = overlapping.exclude(pk=self.instance.pk)

            if overlapping.exists():
                raise forms.ValidationError("Выбранное время пересекается с другим бронированием.")

    def save(self, commit=True):
        booking = super().save(commit=False)
        phone_number = self.cleaned_data['phone']

        if commit:
            # Сохраняем бронирование
            booking.save()

            # Сохраняем телефон в PhoneNumber, если его ещё нет
            PhoneNumber.objects.get_or_create(
                phone_number=phone_number,
                defaults={'user': None}
            )

            # Сохраняем телефон в поле бронирования
            booking.phone = phone_number
            booking.save(update_fields=['phone'])

        return booking


# форма изменения статус и места компьютера
class ComputerStatusForm(forms.ModelForm):
    cpu = forms.ModelChoiceField(queryset=CPU.objects.all(), required=False, label='Процессор')
    gpu = forms.ModelChoiceField(queryset=GPU.objects.all(), required=False, label='Видеокарта')
    ram = forms.ModelChoiceField(queryset=RAM.objects.all(), required=False, label='ОЗУ')
    storage = forms.ModelChoiceField(queryset=Storage.objects.all(), required=False, label='Хранилище')

    class Meta:
        model = Computer
        fields = ['workplace', 'status', 'cpu', 'gpu', 'ram', 'storage']
        labels = {
            'workplace': 'Рабочее место',
            'status': 'Статус',
            'cpu': 'Процессор',
            'gpu': 'Видеокарта',
            'ram': 'ОЗУ',
            'storage': 'Хранилище',
        }
        widgets = {
            'status': forms.Select(),
            'workplace': forms.Select(),
        }


# форма создания нового компьютера
class NewComputerForm(forms.ModelForm):
    cpu = forms.ModelChoiceField(queryset=CPU.objects.all(), required=False, label='Процессор')
    gpu = forms.ModelChoiceField(queryset=GPU.objects.all(), required=False, label='Видеокарта')
    ram = forms.ModelChoiceField(queryset=RAM.objects.all(), required=False, label='ОЗУ')
    storage = forms.ModelChoiceField(queryset=Storage.objects.all(), required=False, label='Хранилище')

    class Meta:
        model = Computer
        fields = ['name', 'workplace', 'status', 'cpu', 'gpu', 'ram', 'storage']
        labels = {
            'name': 'Название',
            'workplace': 'Рабочее место',
            'status': 'Статус',
            'cpu': 'Процессор',
            'gpu': 'Видеокарта',
            'ram': 'ОЗУ',
            'storage': 'Хранилище',
        }
        widgets = {
            'status': forms.Select(),
            'workplace': forms.Select(),
        }


# форма добавления новых комплектующих
class CPUForm(forms.ModelForm):
    class Meta:
        model = CPU
        fields = ['name', 'identifier']
        labels = {'name': 'Название CPU', 'identifier': 'Уникальный ID'}

class GPUForm(forms.ModelForm):
    class Meta:
        model = GPU
        fields = ['name', 'identifier']
        labels = {'name': 'Название GPU', 'identifier': 'Уникальный ID'}

class RAMForm(forms.ModelForm):
    class Meta:
        model = RAM
        fields = ['name', 'identifier']
        labels = {'name': 'Название RAM', 'identifier': 'Уникальный ID'}

class StorageForm(forms.ModelForm):
    class Meta:
        model = Storage
        fields = ['name', 'identifier']
        labels = {'name': 'Название Storage', 'identifier': 'Уникальный ID'}


# форма сохранения или изменения номера телефона
class PhoneNumberForm(forms.ModelForm):
    class Meta:
        model = PhoneNumber
        fields = ['phone_number']
        widgets = {
            'phone_number': forms.TextInput(attrs={'placeholder': 'Введите номер телефона'})
        }


# форма создания пользователя оператором
class OperatorCreateUserForm(forms.Form):
    username = forms.CharField(max_length=150, label="Имя пользователя")
    phone_number = forms.CharField(max_length=20, label="Телефон")
    password = forms.CharField(widget=forms.PasswordInput, label="Пароль")


# форма отзывов
class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['content']