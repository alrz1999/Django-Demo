from django.urls import path
from .views import ContentScoreCreateUpdateView, ContentListView

urlpatterns = [
    path('list/', ContentListView.as_view(), name='content-list'),
    path('score/', ContentScoreCreateUpdateView.as_view(), name='content-score'),
]
