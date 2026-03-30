from django.db import connection


def set_user_location(user_id: int, location: bool) -> None:
    with connection.cursor() as cursor:
        cursor.execute(
            "UPDATE auth_user SET location = %s WHERE id = %s",
            [location, user_id],
        )


def get_user_location(user_id: int) -> bool:
    with connection.cursor() as cursor:
        cursor.execute("SELECT location FROM auth_user WHERE id = %s", [user_id])
        row = cursor.fetchone()
    return bool(row[0]) if row else False
