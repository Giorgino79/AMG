# prodotti/urls.py

from django.urls import path
from . import views

app_name = "prodotti"

urlpatterns = [
    # Dashboard
    path("prodotti", views.dashboard_prodotti, name="dashboard"),
    # Categorie CRUD
    path("categorie/", views.CategoriaListView.as_view(), name="categoria_list"),
    path("categorie/<int:pk>/", views.CategoriaDetailView.as_view(), name="categoria_detail"),
    path("categorie/crea/", views.CategoriaCreateView.as_view(), name="categoria_create"),
    path("categorie/<int:pk>/modifica/", views.CategoriaUpdateView.as_view(), name="categoria_update"),
    path("categorie/<int:pk>/elimina/", views.CategoriaDeleteView.as_view(), name="categoria_delete"),
    # Prodotti CRUD
    path("prodotti/", views.ProdottoListView.as_view(), name="prodotto_list"),
    path("prodotti/<int:pk>/", views.ProdottoDetailView.as_view(), name="prodotto_detail"),
    path("prodotti/crea/", views.ProdottoCreateView.as_view(), name="prodotto_create"),
    path("prodotti/<int:pk>/modifica/", views.ProdottoUpdateView.as_view(), name="prodotto_update"),
    path("prodotti/<int:pk>/elimina/", views.ProdottoDeleteView.as_view(), name="prodotto_delete"),
    # API
    path("api/prodotto/<int:prodotto_id>/info/", views.api_prodotto_info, name="api_prodotto_info"),
    path("api/prodotti/search/", views.api_prodotto_search, name="api_prodotto_search"),
]
