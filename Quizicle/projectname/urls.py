"""
URL configuration for projectname project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
# urls.py

from . import views
from django.urls import path
from django.contrib.auth import views as auth_views
from django.contrib.auth.views import LogoutView
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from .views import custom_login_view



urlpatterns = [
    # Authentication URLs
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', custom_login_view, name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('admin/', admin.site.urls),  

    # Well done page
    path('well-done/', views.well_done, name='well_done'),
    path('create_quiz/', views.QuizCreateView.as_view(), name='create_quiz'),  # Handles quiz, questions, and answers
    path('quizzes/', views.QuizListView.as_view(), name='quiz_list'),  # Lists available quizzes
    path('quiz/<int:quiz_id>/', views.TakeQuizView.as_view(), name='take_quiz'),  # Taking a quiz
    path('quiz_result/<int:quiz_id>/<int:score>/', views.QuizResultView.as_view(), name='quiz_result'),  # Viewing quiz results
    path('search_quizzes/', views.search_quizzes, name='search_quizzes'),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
