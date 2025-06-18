'''
from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('', views.course_list, name='course_list'),
    path('course/create/', views.create_course, name='create_course'),
    path('course/<int:pk>/', views.course_detail, name='course_detail'),
    path('course/<int:pk>/enroll/', views.enroll_course, name='enroll_course'),
]
'''

from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('', views.course_list, name='course_list'),
    path('course/create/', views.create_course, name='create_course'),
    path('course/<int:pk>/', views.course_detail, name='course_detail'),
    path('course/<int:pk>/enroll/', views.enroll_course, name='enroll_course'),

    # 🔧 Fix here: Change <int:pk> to <int:course_id> to match the view argument
    path('course/<int:course_id>/certificate/', views.download_certificate, name='download_certificate'),

    # (If using mark_video_watched view)
    path('course/<int:course_id>/video/<int:video_id>/watched/', views.mark_video_watched, name='mark_video_watched'),

    path('dashboard/', views.dashboard_redirect, name='dashboard'),
    path('dashboard/student/', views.student_dashboard, name='student_dashboard'),
    path('dashboard/tutor/', views.tutor_dashboard, name='tutor_dashboard'),
]


