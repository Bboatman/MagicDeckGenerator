from django.urls import include, path
from magic_api import views
from rest_framework import routers

router = routers.DefaultRouter()
router.register(r'users', views.UserViewSet)
router.register(r'groups', views.GroupViewSet)

urlpatterns = [
    path('', views.index, name='index'), 
    path('', include(router.urls)),
    path('cards/', views.card_list),
    path('cards/<int:pk>', views.card_detail),
    path('deck/', views.deck_list),
    path('deck/<int:pk>', views.deck_info),
    path('deck_detail/', views.deck_detail_info),
    path('deck_detail/<int:pk>', views.deck_detail_list),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework'))
]