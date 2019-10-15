from django.contrib.gis.db import models
from django.contrib.auth.models import User

class Profile(models.Model):
    SIGMA4 = 'sigma4'
    DEPTH = 'depth'
    DEPTH_METRICS = [
        (SIGMA4, 'Sigma 4'),
        (DEPTH, 'Depth'),
    ]
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
    depth_metric = models.CharField(
        choices = DEPTH_METRICS,
        max_length = 20,
        default = SIGMA4,
    )
    only_qc_controlled_data = models.BooleanField(
        default = False,
    )
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        str = {
            'min_depth': self.min_depth,
            'crossover_radius': self.crossover_radius,
            'depth_metric': self.depth_metric,
            'only_qc_controlled_data': self.only_qc_controlled_data,
        }
        return str(str)
