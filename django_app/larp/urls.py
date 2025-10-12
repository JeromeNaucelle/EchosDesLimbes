"""
URL configuration for cms project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path

from . import views
app_name = "larp"

urlpatterns = [
    path('', views.character_list, name='character_list'),
    path('my_inscriptions', views.my_inscriptions, name='my_inscriptions'),
    path('character_list', views.character_list, name='character_list'),
    path('profile', views.profile, name='profile'),
    path('test', views.test, name='test'),
    path('pnj_form/<int:pk>', views.pnj_form, name='pnj_form'),
    path('view_pnj/<int:pnjinfos_id>', views.view_pnj, name='view_pnj'),
    path('view_pnj/<int:pnjinfos_id>/pdf', views.view_pnj_pdf, name='view_pnj_pdf'),
    path('create_pj/<int:inscription_id>', views.create_pj, name='create_pj'),
    path('edit_pj/<int:pjinfos_id>', views.edit_pj, name='edit_pj'),
    path('view_pj/<int:pjinfos_id>', views.view_pj, name='view_pj'),
    path('view_pj/<int:pjinfos_id>/pdf', views.view_pj_pdf, name='view_pj_pdf'),
    path('complete_bg/<int:pjinfo_id>', views.complete_bg, name='complete_bg'),
    path('orga_gn_list', views.orga_gn_list, name='orga_gn_list'),
    path('orga_gn/<int:larp_id>', views.orga_gn, name='orga_gn')
]
