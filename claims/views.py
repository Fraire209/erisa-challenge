from django.shortcuts import render, get_object_or_404
from claims.models import Claim,SystemFlag  #tables
from claims.forms import NoteForm   #form template for claim notes
from django.core.paginator import Paginator #split table into pages
from django.db.models import Q, Count, Avg  # queries and math 
from django.contrib.auth.decorators import login_required #make users log in to use the system
from django.contrib.auth.models import User #built in user model, only using username and password fields
from django.contrib import messages #allows for messages from views to templates
from django.contrib.auth import login #attaches user to session, allows for request.user and instant login

#default view, renders the table and the pagination controls
@login_required     #forces log in 
def home(request):
    search_query = request.GET.get("q", "")
    page_number = request.GET.get("page", 1)
    claims_list = Claim.objects.all().order_by("id").prefetch_related('details','flags')  # Order for consistency and fetches the associated details from ClaimDetails
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

    insurers = Claim.objects.values_list('insurer_name', flat=True).distinct()  #only stores a single instance of each different insurance name or status for dropdown menu
    statuses = Claim.objects.values_list('status', flat=True).distinct()


    #information passed to the partial
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
        return render(request, "claims/claims_table_body.html", context) #avoids rerendering the search and filter sections

    return render(request, "claims/base.html", context) # returns full page upon initial load

#renders claim detail partial file and passes associated claim
def claim_detail(request, pk):
    claim = get_object_or_404(Claim, pk=pk)
    return render(request, "claims/claim_detail_partial.html", {"claim": claim})

#POST method for notes
def add_note(request, pk):
    claim = get_object_or_404(Claim, pk=pk) #gets claim from Claim with matching pk

    if request.method == "POST":
        form = NoteForm(request.POST)       #form instance 
        if form.is_valid():                 #validation
            note = form.save(commit=False)  #creates object without saving yet
            note.claim = claim              #links note with associating claim through fk
            note.created_by = request.user  #links to logged in user throguh django middleware
            note.save()                     #saves
    # Return updated notes partial
    return render(request, "claims/notes_partial.html", {"claim": claim})

#renders notes panel
def claim_notes_partial(request, pk):
    claim = get_object_or_404(Claim, pk=pk)
    notes = claim.notes.all()             #retrieves all notes associated with claim pk
    #Return updated notes partial
    return render(request, "claims/notes_partial.html", {"claim": claim, "notes": notes})

#POST method for flags
def add_flag(request, pk):
    claim = get_object_or_404(Claim, pk=pk)

    # Only create a flag if one doesn't already exist
    if not claim.flags.exists():
        SystemFlag.objects.create(
            claim=claim,
            message="Potential underpayment detected - review recommended."  # must match model field "message"
        )

    # Return updated flag panel for HTMX
    flags = claim.flags.all() 
    return render(request, "claims/flag_partial.html", {"claim": claim, "flags": flags})

#removes flag from claim
def remove_flag(request, pk):
    claim = get_object_or_404(Claim, pk=pk)
    claim.flags.all().delete()  # remove all flags for this claim
    flags = claim.flags.all()
    return render(request, "claims/flag_partial.html", {"claim": claim, "flags": flags})

#renders the flag panel 
def flag_partial(request, pk):
    claim = get_object_or_404(Claim, pk=pk)
    flags = claim.flags.all()
    return render(request, "claims/flag_partial.html", {"claim": claim, "flags": flags})

#renders the quick actions panel
def quick_actions_partial(request, pk):
    claim = get_object_or_404(Claim, pk=pk)
    return render(request, "claims/actions_partial.html", {"claim": claim})

#renders the signup view page, logic for adding a user
def signup_view(request):
    
    if request.method == "POST":
        firstname = request.POST.get("firstname", "").strip().title()   #first and last name used for display purposes
        lastname =  request.POST.get("lastname", "").strip().title()    #strip().title() capitalizes the first letter and makes the rest lowercase
        username = request.POST.get("username")                         #allows for a custom username now that first and last name are separate fields
        password = request.POST.get("password")

        #requires both fields
        if not firstname or not lastname:
            messages.error(request, "Please provide both first and last name.")

        if not firstname or not lastname or not username or not password:
            messages.error(request, "Please provide all of the fields")
        
        #requires uniqure username 
        elif User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
        
        #successful registration
        else:
            User.objects.create_user(username=username, password=password, first_name=firstname, last_name=lastname) #creates user
            messages.success(request, "Account created successfully! Please return to log in page.")
    
    #renders page again if there was an error
    return render(request, "registration/signup.html")

#admin dashboard
def admin_dashboard(request):
    #loads all claims
    claims = Claim.objects.all()
    total_claims = claims.count()   #counts number of claims
    paid_claims = claims.filter(status='Paid').count()     #counts number of Paid status claims
    denied_claims = claims.filter(status='Denied').count() #coutns number of Denied status claims

    #loads all flags
    flags = SystemFlag.objects.all()
    total_flags =  flags.count()    #counts number of flags

    # Percentages of paid and denied claims
    paid_percentage = round((paid_claims / total_claims) * 100, 1) 
    denied_percentage = round((denied_claims / total_claims) * 100, 1) 

    # Averages
    avg_billed = claims.aggregate(avg_billed=Avg('billed_amount'))['avg_billed'] #returns dict, value is in avg_billed
    avg_paid = claims.aggregate(avg_paid=Avg('paid_amount'))['avg_paid']

    # Claims by status
    status_data = claims.values('status').annotate(count=Count('id'))
    status_labels = [s['status'] for s in status_data]      #stores different status labels
    status_counts = [s['count'] for s in status_data]       #stores count for each different status

    # Claims by insurer
    insurer_data = claims.values('insurer_name').annotate(count=Count('id'))
    insurer_labels = [i['insurer_name'] for i in insurer_data]  #stores different insurer names
    insurer_counts = [i['count'] for i in insurer_data]         #stores count for each insurer

    context = {
        'total_claims': total_claims,
        'paid_percentage': paid_percentage,
        'denied_percentage': denied_percentage,
        'avg_billed': avg_billed,
        'avg_paid': avg_paid,
        'total_flags': total_flags,
        'status_labels': status_labels,
        'status_counts': status_counts,
        'insurer_labels': insurer_labels,
        'insurer_counts': insurer_counts,
    }

    #renders the admin dashboard with the corresponding values 
    return render(request, 'claims/admin_dashboard.html', context)
