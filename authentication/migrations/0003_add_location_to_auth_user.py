from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("authentication", "0002_delete_userprofile"),
    ]

    operations = [
        migrations.RunSQL(
            sql="ALTER TABLE auth_user ADD COLUMN IF NOT EXISTS location boolean NOT NULL DEFAULT false;",
            reverse_sql="ALTER TABLE auth_user DROP COLUMN IF EXISTS location;",
        ),
    ]
