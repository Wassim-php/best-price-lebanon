from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.contrib.admin.sites import NotRegistered

from .models import get_user_location, set_user_location


class UserAdminForm(forms.ModelForm):
    location = forms.BooleanField(required=False, label="Inside Beirut")

    class Meta:
        model = User
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields["location"].initial = get_user_location(self.instance.pk)


class CustomUserAdmin(BaseUserAdmin):
    form = UserAdminForm
    list_display = BaseUserAdmin.list_display + ("location",)
    fieldsets = BaseUserAdmin.fieldsets + (("Location", {"fields": ("location",)}),)
    add_fieldsets = BaseUserAdmin.add_fieldsets + (("Location", {"fields": ("location",)}),)

    @admin.display(boolean=True, description="Inside Beirut")
    def location(self, obj):
        return get_user_location(obj.id)

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        set_user_location(obj.id, form.cleaned_data.get("location", False))


try:
    admin.site.unregister(User)
except NotRegistered:
    pass

admin.site.register(User, CustomUserAdmin)
