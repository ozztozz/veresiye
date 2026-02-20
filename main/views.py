from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout


def home(request):
    blok_list= ['A', 'B', 'C', 'D', 'E', 'F']
    number_list = [str(i) for i in range(1, 80)]
    context = {
        'blok_list': blok_list, 
        'number_list': number_list,
    }

    return render(request, 'home.html', context)


def logout_view(request):
    logout(request)
    return redirect('main:home')