from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms import  ProfileUpdateForm
from django.contrib import messages

@login_required
def profile(request):
    return render(request, 'core/profile.html')

@login_required
def edit_profile(request):
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated!')
            return redirect('profile')
    else:
        form = ProfileUpdateForm(instance=request.user.profile)
    return render(request, 'core/edit_profile.html', {'form': form})