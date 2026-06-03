from django.urls import path

from care import views

urlpatterns = [
    path("", views.index, name="index"),
    path("api/orders/", views.create_order_and_generate, name="create_order"),
    path("api/orders/<str:order_id>/", views.get_order, name="get_order"),
]
