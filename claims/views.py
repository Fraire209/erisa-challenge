from django.shortcuts import render
from claims.models import Claim # make sure to match your model name

def home(request):
    # Fetch all rows from the table Claim
    claims = Claim.objects.all()
    return render(request, "base.html", {"claims": claims}) #passes the table to the base.html template, data sent as dictionaries

# Create your views here.
