from django.shortcuts import render, get_object_or_404, redirect
from claims.models import Claim,SystemFlag  #tables
from claims.forms import NoteForm   #form template for claim notes
from django.core.paginator import Paginator #split table into pages
from django.db.models import Q  # queries
from django.contrib.auth.decorators import login_required #make users log in to use the system
from django.contrib.auth.models import User #built in user model, only using username and password fields
from django.contrib import messages #allows for messages from views to templates
from django.contrib.auth import login #attaches user to session, allows for request.user

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
        username = request.POST.get("username")
        password = request.POST.get("password")

        #requires both fields
        if not username or not password:
            messages.error(request, "Please provide both username and password.")
        
        #requires uniqure username 
        elif User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
        
        #successful registration
        else:
            user = User.objects.create_user(username=username, password=password)
            login(request, user)  # logs in immediately
            return redirect("home") #redirects to home view
    
    #renders page again if there was an error
    return render(request, "registration/signup.html")
