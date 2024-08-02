from django.urls import path
from . import views 
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('login/', views.Login, name='login'),
    path('api/login', views.Login_Submit, name='login api'),
    path('', views.Home, name='Home'),
    path('logout/', views.Logout.as_view(), name='logout'),
    path("api/submit",views.Form_Submit,name="Form Submit"),
    path("password-reset/",views.Forget_Password ,name='Password reset'),
    path('password-reset-confirm/<uidb64>/<token>/', views.Reset_Password_Link ,name='password_reset_confirm'),
    # Upload
    path('automl',views.AutoML,name='automl'),
    path('api/upload',views.Dataset,name="Dataset")
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)



