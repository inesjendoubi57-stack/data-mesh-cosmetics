from django.urls import path

from ui import views

urlpatterns = [
    path("", views.home, name="home"),
    path("products/<str:name>/", views.detail, name="detail"),
    path("products/<str:name>/changes/", views.changes, name="changes"),
    path("revenue/", views.revenue, name="revenue"),
    path('lineage/', views.lineage, name='lineage'),
]


