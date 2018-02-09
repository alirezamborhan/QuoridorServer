from django.contrib import admin

from .models import User, TwoPlayerGame, FourPlayerGame
from django.contrib.sessions.models import Session

# Register your models here.

admin.site.register(User)
admin.site.register(TwoPlayerGame)
admin.site.register(FourPlayerGame)
admin.site.register(Session)
