from django.urls import path
from assets import views

app_name = 'assets'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('report/', views.report, name='report'),
    path('index/', views.index, name='index'),
    path('detail/<int:asset_id>/', views.detail, name="detail"),
]