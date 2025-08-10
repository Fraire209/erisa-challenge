from django.shortcuts import render
from claims.models import Claim
from django.core.paginator import Paginator

def home(request):
    page_number = request.GET.get("page", 1)
    claims_list = Claim.objects.all().order_by("id")  # Order for consistency
    paginator = Paginator(claims_list, 5)  # 5 rows per page

    page_obj = paginator.get_page(page_number)

    if request.headers.get("HX-Request"):  
        # If request comes from HTMX, return only the table body
        return render(request, "claims/claims_table_body.html", {"claims": page_obj})

    return render(request, "claims/base.html", {"claims": page_obj}) # returns full page upon initial load
