from django.contrib.auth.decorators import login_required
from django.shortcuts import render



@login_required
def user_logout(request):
    from django.contrib.auth import logout

    logout(request)
    return render(request, 'registration/logged_out.html', {})

def test(request):
    return render(request, 'test.html', {})


def registration_closed(request):
    from django_registration.backends.activation.views import RegistrationView
    from .form import RegisterForm

    RegistrationView.as_view(form_class=RegisterForm)
    title = "Site en maintenance"
    text = """La création de compte est actuellement fermée, les équipes travaillent pour vous permettre d'accéder à un  
    site fini avec les bonnes fonctionnalités. N'hésitez pas à revenir, et à suivre notre actualité sur les réseaux"""
    return render(request, 'simple_text.html', {title: title, text:text})
