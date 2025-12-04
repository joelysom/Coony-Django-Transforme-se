from django.contrib import admin
from .models import Usuario, EmpresaProfile, EmpresaAnuncio


@admin.register(Usuario)
class UsuarioAdmin(admin.ModelAdmin):
	list_display = ('nome', 'email', 'telefone')
	search_fields = ('nome', 'email', 'username')


@admin.register(EmpresaProfile)
class EmpresaProfileAdmin(admin.ModelAdmin):
	list_display = ('nome_empresa', 'tipo', 'email', 'telefone')
	search_fields = ('nome_empresa', 'cnpj', 'email')
	list_filter = ('tipo',)


@admin.register(EmpresaAnuncio)
class EmpresaAnuncioAdmin(admin.ModelAdmin):
	list_display = ('titulo', 'profile', 'categoria', 'preco', 'is_active', 'created_at')
	search_fields = ('titulo', 'descricao', 'profile__nome_empresa')
	list_filter = ('categoria', 'is_active')
