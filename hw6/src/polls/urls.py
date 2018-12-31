from django.urls import path

from .views import index, detail, vote, results, IndexView, DetailView, ResultView

urlpatterns = [
    path("", IndexView.as_view(), name="index"),
    path("<int:pk>/", DetailView.as_view(), name="detail"),
    path("<int:qid>/vote/", vote, name="vote"),
    path("<int:pk>/results/", ResultView.as_view(), name="results")

]