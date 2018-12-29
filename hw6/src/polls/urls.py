from django.urls import path

from .views import index, detail, vote, results

urlpatterns = [
    path("", index, name="index"),
    path("<int:qid>/", detail, name="detail"),
    path("<int:qid>/vote/", vote, name="vote"),
    path("<int:qid>/results/", results, name="results")

]