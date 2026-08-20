from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponseForbidden, HttpResponseBadRequest
from django.contrib.auth import login, logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.db import transaction
from datetime import datetime
from uuid import UUID
from .models import (
    Workplace, Tariff, Booking, Computer, Role, CPU, GPU, RAM, Storage,
    PhoneNumber, Review
)
from .forms import (
    QuickBookingForm, OperatorBookingForm, ComputerStatusForm, NewComputerForm,
    CPUForm, GPUForm, RAMForm, StorageForm, BookingForm, OperatorCreateUserForm,
    ReviewForm
)
from .permissions import is_mechanic, is_operator


# основные страницы сайта
def main(request):
    return render(request, 'booking/main.html', {
        'workplaces': Workplace.objects.all(),
        'tariffs': Tariff.objects.all(),
        'quick_booking_form': QuickBookingForm(),
    })

def quick_booking(request):
    if request.method == 'POST':
        form = QuickBookingForm(request.POST)
        if form.is_valid():
            form.save()
    return redirect('main')

def workplace_status(request):
    return render(request, 'booking/workplace_status.html', {'workplaces': Workplace.objects.all()})

def about(request):
    return render(request, 'booking/about.html')

def tariffs_view(request):
    return render(request, 'booking/tariffs.html', {'tariffs': Tariff.objects.all()})

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('main')
    else:
        form = UserCreationForm()
    return render(request, 'booking/register.html', {'form': form})


# проверка доступности свободного места
def is_workplace_available(workplace, start, end):
    return not Booking.objects.filter(
        workplace=workplace,
        status__in=['pending', 'confirmed']
    ).filter(
        start_time__lt=end,
        end_time__gt=start
    ).exists()


# api для проверки свободного места
@login_required
def workplace_availability(request):
    wp_id = request.GET.get('workplace_id')
    date_str = request.GET.get('date')
    start_str = request.GET.get('start')
    end_str = request.GET.get('end')

    if not (wp_id and date_str and start_str and end_str):
        return JsonResponse({'available': False, 'error': 'Missing parameters'})

    try:
        wp = Workplace.objects.get(pk=wp_id)
        start_dt = datetime.strptime(f"{date_str} {start_str}", "%Y-%m-%d %H:%M")
        end_dt = datetime.strptime(f"{date_str} {end_str}", "%Y-%m-%d %H:%M")
    except (Workplace.DoesNotExist, ValueError):
        return JsonResponse({'available': False, 'error': 'Invalid parameters'})

    available = is_workplace_available(wp, start_dt, end_dt)
    return JsonResponse({'available': available})


# api для проверки брони по id
def booking_check(request):
    unique_id = request.GET.get('unique_id')
    if not unique_id:
        return JsonResponse({'success': False, 'error': 'Missing unique_id'})

    try:
        booking_obj = Booking.objects.get(unique_id=UUID(unique_id))
        comp = booking_obj.workplace.current_computer()
        data = {
            'success': True,
            'unique_id': str(booking_obj.unique_id),
            'workplace': booking_obj.workplace.name,
            'computer': {
                'name': comp.name if comp else None,
                'cpu': comp.cpu if comp else None,
                'gpu': comp.gpu if comp else None,
                'ram': comp.ram if comp else None,
                'storage': comp.storage if comp else None,
            },
            'start_time': booking_obj.start_time,
            'end_time': booking_obj.end_time,
            'status': booking_obj.get_status_display(),
            'tariff': booking_obj.tariff.name if booking_obj.tariff else None,
            'cost': booking_obj.cost if booking_obj.tariff else None,
        }
        return JsonResponse(data)
    except (Booking.DoesNotExist, ValueError):
        return JsonResponse({'success': False, 'error': 'Booking not found'})


# просмотр и редактирование компьютеров механиком
@login_required
def mechanic_computers(request):
    if not is_mechanic(request.user):
        return HttpResponseForbidden()

    computers = Computer.objects.all()
    computer_forms = [
        {'computer': comp, 'form': ComputerStatusForm(instance=comp, prefix=str(comp.id))}
        for comp in computers
    ]
    new_computer_form = NewComputerForm()
    cpu_list = CPU.objects.all()
    gpu_list = GPU.objects.all()
    ram_list = RAM.objects.all()
    storage_list = Storage.objects.all()

    if request.method == 'POST':
        if 'add_computer' in request.POST:
            new_computer_form = NewComputerForm(request.POST)
            if new_computer_form.is_valid():
                new_computer_form.save()
                messages.success(request, 'Новый компьютер добавлен!')
                return redirect('mechanic_computers')
        else:
            saved = False
            for comp_dict in computer_forms:
                form = ComputerStatusForm(
                    request.POST,
                    instance=comp_dict['computer'],
                    prefix=str(comp_dict['computer'].id)
                )
                if form.is_valid():
                    form.save()
                    saved = True
            if saved:
                messages.success(request, 'Изменения сохранены.')
                return redirect('mechanic_computers')

    context = {
        'computer_forms': computer_forms,
        'new_computer_form': new_computer_form,
        'cpu_list': cpu_list,
        'gpu_list': gpu_list,
        'ram_list': ram_list,
        'storage_list': storage_list,
    }
    return render(request, 'booking/mechanic_computers.html', context)


# просмотр и создание броней оператором
@login_required
def operator_bookings(request):
    if not is_operator(request.user):
        return HttpResponseForbidden()
    bookings = Booking.objects.all().order_by('-start_time')
    return render(request, 'booking/operator_bookings.html', {'bookings': bookings})

@login_required
def operator_create_booking(request):
    if request.method == 'POST':
        form = BookingForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Бронирование успешно создано.')
            return redirect('booking_list')
    else:
        form = BookingForm()
    return render(request, 'booking/operator_create_booking.html', {'form': form})


# бронирование клиентом
@login_required
def booking(request):
    user = request.user

    if request.method == 'POST' and not (is_operator(user) or is_mechanic(user)):
        date_str = request.POST.get('date')
        start_str = request.POST.get('start_time')
        end_str = request.POST.get('end_time')
        workplace_ids = request.POST.get('workplace_ids', '').split(',')
        tariff_id = request.POST.get('tariff_id')

        tariff = Tariff.objects.filter(pk=tariff_id).first() if tariff_id else Tariff.objects.filter(name__iexact='standart').first()

        if not (date_str and start_str and end_str and workplace_ids and any(workplace_ids)):
            return HttpResponseBadRequest("Missing data")

        try:
            start_dt = datetime.strptime(f"{date_str} {start_str}", "%Y-%m-%d %H:%M")
            end_dt = datetime.strptime(f"{date_str} {end_str}", "%Y-%m-%d %H:%M")
        except ValueError:
            return HttpResponseBadRequest("Invalid date/time format")

        try:
            with transaction.atomic():
                for wid in workplace_ids:
                    if not wid:
                        continue
                    wp = get_object_or_404(Workplace, pk=wid)
                    computer = wp.current_computer()
                    if not computer or computer.status != 'working':
                        return HttpResponseBadRequest(f"Computer at {wp.name} unavailable")
                    if not is_workplace_available(wp, start_dt, end_dt):
                        return HttpResponseBadRequest(f"{wp.name} is already booked for this period")

                    Booking.objects.create(
                        user=user,
                        workplace=wp,
                        start_time=start_dt,
                        end_time=end_dt,
                        tariff=tariff,
                        status='pending'
                    )
        except Exception as e:
            return HttpResponseBadRequest(str(e))

        return redirect('profile')

    # GET: отображение страницы бронирования
    date_str = request.GET.get('date')
    start_str = request.GET.get('start')
    end_str = request.GET.get('end')
    unique_id = request.GET.get('unique_id')

    start_dt = end_dt = None
    if date_str and start_str and end_str:
        try:
            start_dt = datetime.strptime(f"{date_str} {start_str}", "%Y-%m-%d %H:%M")
            end_dt = datetime.strptime(f"{date_str} {end_str}", "%Y-%m-%d %H:%M")
        except ValueError:
            start_dt = end_dt = None

    workplaces = list(Workplace.objects.all().order_by('row', 'number'))
    workplace_status = {}
    for wp in workplaces:
        overlapping = Booking.objects.filter(workplace=wp, status__in=['pending', 'confirmed'])
        if start_dt and end_dt:
            overlapping = overlapping.filter(start_time__lt=end_dt, end_time__gt=start_dt)
        computers = wp.computer_set.all()
        if computers.filter(status__in=['broken', 'repair']).exists():
            workplace_status[wp.id] = 'repair'
        elif overlapping.exists():
            workplace_status[wp.id] = 'booked'
        else:
            workplace_status[wp.id] = 'working'

    context = {
        'workplaces': workplaces,
        'workplace_status': workplace_status,
        'date': date_str,
        'start_time': start_str,
        'end_time': end_str,
        'booking_info': None,
        'unique_id': unique_id,
    }

    if unique_id:
        try:
            booking_obj = Booking.objects.get(unique_id=UUID(unique_id))
            context['booking_info'] = booking_obj
        except (Booking.DoesNotExist, ValueError):
            context['booking_info'] = None

    return render(request, 'booking/booking.html', context)


# профиль пользователя
@login_required
def profile(request):
    user = request.user

    # POST: сохраняем номер телефона
    if request.method == 'POST':
        phone_number = request.POST.get('phone_number')
        if phone_number:
            phone_obj, _ = PhoneNumber.objects.get_or_create(user=user)
            phone_obj.phone_number = phone_number
            phone_obj.save()

    context = {'user': user}

    # определение роли
    role_name = 'client'
    if user.is_superuser:
        role_name = 'superuser'
    else:
        try:
            if user in Role.objects.get(name='mechanic').user_set.all():
                role_name = 'mechanic'
        except Role.DoesNotExist:
            pass
        try:
            if user in Role.objects.get(name='operator').user_set.all():
                role_name = 'operator'
        except Role.DoesNotExist:
            pass

    context['role_name'] = role_name

    # получаем данные для роли
    if role_name == 'client':
        context['bookings'] = Booking.objects.filter(user=user).order_by('start_time')
    elif role_name == 'mechanic':
        context['computers'] = Computer.objects.all()
    elif role_name == 'operator':
        context['bookings'] = Booking.objects.all().order_by('-start_time')

    # текущий номер телефона для формы
    try:
        context['phone_number_value'] = PhoneNumber.objects.get(user=user).phone_number
    except PhoneNumber.DoesNotExist:
        context['phone_number_value'] = ''

    return render(request, 'booking/profile.html', context)


# обновление статуса бронирования
@login_required
def booking_update(request, booking_id):
    if not is_operator(request.user):
        return HttpResponseForbidden()
    booking_obj = get_object_or_404(Booking, id=booking_id)
    if request.method == 'POST':
        status = request.POST.get('status')
        if status in ['pending', 'confirmed', 'rejected']:
            booking_obj.status = status
            booking_obj.save()
    return redirect('operator_bookings')


# выход из аккаунта
@login_required
def logout_view(request):
    logout(request)
    return redirect('main')


# управление комплектующих механиком
@login_required
def mechanic_parts(request):
    if not is_mechanic(request.user):
        return HttpResponseForbidden()

    cpus = CPU.objects.all()
    gpus = GPU.objects.all()
    rams = RAM.objects.all()
    storages = Storage.objects.all()

    cpu_form = CPUForm(prefix='cpu')
    gpu_form = GPUForm(prefix='gpu')
    ram_form = RAMForm(prefix='ram')
    storage_form = StorageForm(prefix='storage')

    if request.method == 'POST':
        if 'add_cpu' in request.POST:
            cpu_form = CPUForm(request.POST, prefix='cpu')
            if cpu_form.is_valid():
                cpu_form.save()
                return redirect('mechanic_parts')
        elif 'add_gpu' in request.POST:
            gpu_form = GPUForm(request.POST, prefix='gpu')
            if gpu_form.is_valid():
                gpu_form.save()
                return redirect('mechanic_parts')
        elif 'add_ram' in request.POST:
            ram_form = RAMForm(request.POST, prefix='ram')
            if ram_form.is_valid():
                ram_form.save()
                return redirect('mechanic_parts')
        elif 'add_storage' in request.POST:
            storage_form = StorageForm(request.POST, prefix='storage')
            if storage_form.is_valid():
                storage_form.save()
                return redirect('mechanic_parts')

    context = {
        'cpus': cpus,
        'gpus': gpus,
        'rams': rams,
        'storages': storages,
        'cpu_form': cpu_form,
        'gpu_form': gpu_form,
        'ram_form': ram_form,
        'storage_form': storage_form,
    }
    return render(request, 'booking/mechanic_parts.html', context)


# создание пользователя оператором
@login_required
def operator_create_user(request):
    if not is_operator(request.user):
        return HttpResponseForbidden()

    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        phone = request.POST.get('phone_number')
        if form.is_valid():
            user = form.save()
            if phone:
                PhoneNumber.objects.create(user=user, phone_number=phone)
            messages.success(request, 'Пользователь создан')
            return redirect('operator_create_user')
    else:
        form = UserCreationForm()

    return render(request, 'booking/operator_create_user.html', {'form': form})


# создание брони оператором
@login_required
def operator_create_booking(request):
    if not is_operator(request.user):
        return HttpResponseForbidden()

    if request.method == 'POST':
        username = request.POST.get('username')
        user = get_object_or_404(User, username=username)

        date_str = request.POST.get('date')
        start_str = request.POST.get('start_time')
        end_str = request.POST.get('end_time')
        workplace_ids = request.POST.get('workplace_ids', '').split(',')

        tariff = Tariff.objects.filter(name__iexact='standart').first()

        if not (date_str and start_str and end_str and workplace_ids and any(workplace_ids)):
            return HttpResponseBadRequest("Missing data")

        try:
            start_dt = datetime.strptime(f"{date_str} {start_str}", "%Y-%m-%d %H:%M")
            end_dt = datetime.strptime(f"{date_str} {end_str}", "%Y-%m-%d %H:%M")
        except ValueError:
            return HttpResponseBadRequest("Invalid date/time format")

        try:
            with transaction.atomic():
                for wid in workplace_ids:
                    if not wid:
                        continue
                    wp = get_object_or_404(Workplace, pk=wid)
                    computer = wp.current_computer()
                    if not computer or computer.status != 'working':
                        return HttpResponseBadRequest(f"Computer at {wp.name} unavailable")
                    if not is_workplace_available(wp, start_dt, end_dt):
                        return HttpResponseBadRequest(f"{wp.name} is already booked for this period")

                    Booking.objects.create(
                        user=user,
                        workplace=wp,
                        start_time=start_dt,
                        end_time=end_dt,
                        tariff=tariff,
                        status='pending'
                    )
        except Exception as e:
            return HttpResponseBadRequest(str(e))

        messages.success(request, 'Бронирование успешно создано.')
        return redirect('operator_bookings')

    # GET как у клиентов
    workplaces = list(Workplace.objects.all().order_by('row', 'number'))
    workplace_status = {wp.id: 'working' for wp in workplaces}  # можно добавить фильтр занятости, как в клиенте

    return render(request, 'booking/operator_create_booking.html', {
        'workplaces': workplaces,
        'workplace_status': workplace_status,
        'users': User.objects.all(),
        'date': '',
        'start_time': '',
        'end_time': ''
    })

# функция для оставление отзывов
def reviews_view(request):
    if request.method == 'POST':
        if request.user.is_authenticated:
            form = ReviewForm(request.POST)
            if form.is_valid():
                review = form.save(commit=False)
                review.user = request.user
                review.save()
                return redirect('reviews')
        else:
            form = ReviewForm()
    else:
        form = ReviewForm()

    reviews = Review.objects.all().order_by('-created_at')
    return render(request, 'booking/reviews.html', {'form': form, 'reviews': reviews})