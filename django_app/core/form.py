from django_registration.forms import RegistrationForm
from django.contrib.auth.models import User

class RegisterForm(RegistrationForm):

    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "password1", "password2", "email"]
        labels = {
            'first_name': 'Prénom (réel !)',
            'last_name': 'Nom (réel !)',
        }