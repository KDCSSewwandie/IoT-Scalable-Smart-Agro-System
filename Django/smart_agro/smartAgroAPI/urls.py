from django.urls import path
from .views import *

urlpatterns = [
    path('',loading),
    path('start', start, name='start'),  # Ensure this matches
    path('home', home, name='home'),
    path('update', update, name='update'),
    path('noServer', homeWithoutFetch, name='home'),
    path('historicalData', showHistory, name='historicalData'),
    path('insert', insertData, name='table update'),
]