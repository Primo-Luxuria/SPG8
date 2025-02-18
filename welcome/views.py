from django.http import HttpResponse
from django.shortcuts import render

def home(request):
    return render(request, 'welcome/home.html')
    
def login(request):
    return render(request, 'welcome/login.html')
    
def signup(request):
    return render(request, 'welcome/signup.html')
    
def signup_handler(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        password_confirm = request.POST.get('passwordconfirm')
        role = request.POST.get('role')
        
        # Validation
        if not all([username, password, password_confirm, role]):
            messages.error(request, 'All fields are required.')
            return render(request, 'welcome/signup.html')
            
        if password != password_confirm:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'welcome/signup.html')
            
        if CustomUser.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists. Please choose a different username.')
            return render(request, 'welcome/signup.html')
            
        # Ensure role is valid (no admin from signup)
        if role not in ['student', 'teacher']:
            messages.error(request, 'Invalid role selected.')
            return render(request, 'welcome/signup.html')
            
        # Create user
        try:
            user = CustomUser.objects.create_user(
                username=username,
                password=password,
                role=role
            )
            login(request, user)
            messages.success(request, 'Sign-up successful! You are now logged in.')
            return redirect('home')
        except Exception as e:
            messages.error(request, str(e))
            
    return render(request, 'welcome/signup.html')
    
def back_to_home(request):
    return redirect('home')