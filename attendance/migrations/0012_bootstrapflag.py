from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("attendance", "0011_course_is_active_alter_student_year"),
    ]

    operations = [
        migrations.CreateModel(
            name="BootstrapFlag",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("key", models.CharField(max_length=64, unique=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
        ),
    ]
