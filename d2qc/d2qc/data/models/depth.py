from django.contrib.gis.db import models

class Depth(models.Model):
    class Meta:
        db_table = 'd2qc_depths'
        indexes = [
            models.Index(fields=['depth']),
        ]
        unique_together = ( 'cast', 'depth', 'bottle', 'date_and_time')
        ordering = ['depth']

    id = models.AutoField(primary_key=True)
    cast = models.ForeignKey('Cast',
            related_name='depths', on_delete=models.CASCADE)
    depth = models.DecimalField(max_digits=8, decimal_places=3)
    sigma4 = models.DecimalField(
        max_digits = 8,
        decimal_places = 5,
        blank = True,
        null = True,
    )
    date_and_time = models.DateTimeField()
    bottle = models.IntegerField(default=0)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.depth)
