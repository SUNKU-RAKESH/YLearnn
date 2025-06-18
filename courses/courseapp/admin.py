from django.contrib import admin
from .models import Profile, Course, Enrollment, Video

admin.site.register(Profile)
admin.site.register(Course)
admin.site.register(Enrollment)
admin.site.register(Video)
