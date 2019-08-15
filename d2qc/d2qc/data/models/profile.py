from django.contrib.gis.db import models
from django.contrib.auth.models import User

class Profile(models.Model):
    class Meta:
        db_table = 'd2qc_user_profile'
    user = models.OneToOneField(
        User,
        related_name='profile',
        on_delete = models.CASCADE,
        blank=True,
        null=True,
        editable=False
    )
    min_depth = models.IntegerField(default=1500)
    crossover_radius = models.IntegerField(default=200000)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
