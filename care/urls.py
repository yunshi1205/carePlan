from django.urls import path

from care import views

urlpatterns = [
    path("", views.index, name="index"),
    path("api/orders/", views.create_order_and_generate, name="create_order"),
    path("api/orders/search/", views.search_orders, name="search_orders"),
    path(
        "api/orders/<str:order_id>/download/",
        views.download_care_plan,
        name="download_care_plan",
    ),
    path("api/orders/<str:order_id>/", views.get_order, name="get_order"),
]
