from django.shortcuts import render


def index(request):
	"""Render desktop version of the page."""
	return render(request, 'usuarios/index.html')


def mobile(request):
	"""Render mobile version of the page."""
	return render(request, 'usuarios/mobile.html')
