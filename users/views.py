from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout, aauthenticate
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
# Create your views here.
# flask kind of function @


def logout_view(request):
    logout(request)
    return redirect('profile')

def profile(request):
    return render(request, 'users/profile.html', {'user': request.user})



def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('profile')
        else:
            return render(request, 'users/login.html', {'error': 'Invalid credentials'})
    return render(request, 'users/login.html')


def register(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        email = request.POST['email']
        user = User.objects.create_user(username=username, password=password, email=email)
        login(request, user)
        return redirect('profile')
    return render(request, 'users/register.html')   