# from django.conf.urls import url

#from . import views

from guardian.compat import url
from report import views

app_name = 'report'

urlpatterns = [
    url(r'^$', views.index, name = 'index' ),
    url(r'^download/$', views.DownloadReportListView, name = 'download' ),
    url(r'^update/$', views.updateReportListView, name = 'update' ),
    url(r'^showall/$', views.showAllView, name = 'showall' ),
    url(r'^showselected/$', views.showSelectedView, name = 'showselected' ),
    url(r'^clear/$', views.clearView, name = 'clear' ),
    url(r'^mptest/$', views.mptestView, name = 'mptest' ),
    url(r'^ajaxtest/$', views.ajaxtest, name = 'ajaxtest' ),
    url(r'^selfselected/$', views.selfselected, name = 'selfselected' ),
]
