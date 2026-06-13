from django.db import models


class Item(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=255, unique=True)
    table_name = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField()

    class Meta:
        db_table = "items"
        ordering = ["id"]
