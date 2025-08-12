from django.shortcuts import render, get_object_or_404
from claims.models import Claim
from django.core.paginator import Paginator
from django.db.models import Q  # queries

def home(request):
    search_query = request.GET.get("q", "")
    page_number = request.GET.get("page", 1)
    claims_list = Claim.objects.all().order_by("id").prefetch_related('details')  # Order for consistency and fetches the associated details from ClaimDetails
    selected_insurer = request.GET.get("insurer", "")
    selected_status = request.GET.get("status", "")

    filters = Q()  # start empty

    #search by text fields 
    if search_query:
        text_filters = (
            Q(patient_name__icontains=search_query) |
            Q(status__icontains=search_query) |
            Q(insurer_name__icontains=search_query)
        )
        #search by exact digit claim id 
        if search_query.isdigit():
            text_filters |= Q(claim_id=int(search_query))
        filters &= text_filters

    # filter by selected insurer 
    if selected_insurer:
        filters &= Q(insurer_name=selected_insurer)

    # filter by selected status 
    if selected_status:
        filters &= Q(status=selected_status)
        
    #applies combined filters
    claims_list = claims_list.filter(filters)

    paginator = Paginator(claims_list, 5)  # 5 rows per page
    page_obj = paginator.get_page(page_number) #gets contents of page 

    insurers = Claim.objects.values_list('insurer_name', flat=True).distinct()
    statuses = Claim.objects.values_list('status', flat=True).distinct()



    context = {
        "claims": page_obj,
        "q": search_query,
        "insurers": insurers,
        "statuses": statuses,
        "selected_insurer": selected_insurer,
        "selected_status": selected_status,
    }

    if request.headers.get("HX-Request"):  
        # If request comes from HTMX, return only the table body
        return render(request, "claims/claims_table_body.html", context)

    return render(request, "claims/base.html", context) # returns full page upon initial load

def claim_detail(request, pk):
    claim = get_object_or_404(Claim, pk=pk)
    return render(request, "claims/claim_detail_partial.html", {"claim": claim})
