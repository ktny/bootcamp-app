from django.db import migrations, models


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
    ]
