from datetime import UTC

from django.db import migrations, models
from django.utils import timezone


def create_seed_item(apps, _schema_editor):
    item = apps.get_model("api", "Item")
    item.objects.create(
        id=1,
        name="サンプルCSV",
        table_name="sample_csv",
        created_at=timezone.datetime(2026, 1, 1, tzinfo=UTC),
    )


def delete_seed_item(apps, _schema_editor):
    item = apps.get_model("api", "Item")
    item.objects.filter(id=1).delete()


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Item",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=255, unique=True)),
                ("table_name", models.CharField(max_length=255, unique=True)),
                ("created_at", models.DateTimeField()),
            ],
            options={
                "db_table": "items",
                "ordering": ["id"],
            },
        ),
        migrations.RunPython(create_seed_item, delete_seed_item),
    ]
