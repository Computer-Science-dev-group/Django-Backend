from django.contrib import admin

from uia_backend.accounts.models import OTP, CustomUser, EmailVerification

admin.site.register(CustomUser)
admin.site.register(OTP)
admin.site.register(EmailVerification)
