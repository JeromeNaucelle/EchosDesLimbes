from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class Purchase(models.Model):
    class Meta:
        verbose_name = "Achat"

    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Utilisateur")
    price = models.FloatField(verbose_name="Prix", default=1.0)
    article = models.CharField(verbose_name="Article", max_length=100)
    created_at  = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.article} : {self.price}€"