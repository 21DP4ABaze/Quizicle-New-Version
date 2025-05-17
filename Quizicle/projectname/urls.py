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
from .views import QuizDeleteView, ModifyQuizView,QuizDetailView,UserResultsView,PopularQuizView,ReportCreateView,admin_reports_view,admin_quiz_delete_view



urlpatterns = [
    path('report/<int:pk>/delete/', views.ReportDeleteView.as_view(), name='report_delete'),
    path('quiz/<int:pk>/', QuizDetailView.as_view(), name='quiz_details'),
    path('admin/delete/quiz/<int:pk>/', admin_quiz_delete_view, name='admin_quiz_delete'),
    path('admin/reports/', admin_reports_view, name='admin_reports'),
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('admin/', admin.site.urls),
    path('well-done/', views.well_done, name='well_done'),
    path('create_quiz/', views.QuizCreateView.as_view(), name='create_quiz'),  # Handles quiz, questions, and answers
    path('my-quizzes/', views.QuizListView.as_view(), name='quiz_list'),  # Lists available quizzes
    path('quizzes/', views.QuizPublicList.as_view(), name='quiz_public_list'),  # Lists available quizzes
    path('quiz/<int:quiz_id>/take/', views.TakeQuizView.as_view(), name='take_quiz'),
    path('quiz_result/<int:quiz_id>/<int:score>/', views.QuizResultView.as_view(), name='quiz_result'),  # Viewing quiz results
    path('search_quizzes/', views.search_quizzes, name='search_quizzes'),
    path('my-results/', UserResultsView.as_view(), name='user_results'),
    path('quiz/<int:pk>/delete/', QuizDeleteView.as_view(), name='quiz_delete'),
    path('quiz/<int:quiz_id>/modify/', ModifyQuizView.as_view(), name='modify_quiz'),
    path('popular-quizzes/', PopularQuizView.as_view(), name='popular_quizzes'),
    path('quiz/details/<int:pk>/', QuizDetailView.as_view(), name='quiz_details'),
    path('report/<int:quiz_id>/', ReportCreateView.as_view(), name='report_quiz'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
