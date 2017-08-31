# from django.conf.urls import url

#from . import views

from guardian.compat import url
from mp import views

app_name = 'report'

urlpatterns = [
    url(r'^$', views.index, name = 'index' ),
]
