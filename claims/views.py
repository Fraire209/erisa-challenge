from django.shortcuts import render, get_object_or_404
from claims.models import Claim,SystemFlag  #tables
from claims.forms import NoteForm, EditClaimForm   #form template for claim notes, and for file reupload
from django.core.paginator import Paginator #split table into pages
from django.db.models import Q, Count, Avg  # queries and math 
from django.contrib.auth.decorators import login_required #make users log in to use the system
from django.contrib.auth.models import User #built in user model, only using username and password fields
from django.contrib import messages #allows for messages from views to templates
from django.contrib.auth import login #attaches user to session, allows for request.user and instant login
import json #writing to json files
import csv  #writing to csv files
from pathlib import Path    #used for file path
from django.conf import settings    #used for absolute file path

#default view, renders the table and the pagination controls
@login_required     #forces log in 
def home(request):
    search_query = request.GET.get("q", "")
    page_number = request.GET.get("page", 1)
    claims_list = Claim.objects.all().order_by("id").prefetch_related('details','flags', 'notes')  # Order for consistency and fetches the associated details from ClaimDetails and Notes
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
        return render(request, "claims/claims_table_body.html", context) #avoids rerendering the search and filter, and detail notes/annotations and quick actions back to claim.0

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

#absolute file paths for each file
CLAIM_LIST_JSON = Path(settings.BASE_DIR) / "data" / "claim_list_data.json"
CLAIM_DETAIL_JSON = Path(settings.BASE_DIR) / "data" / "claim_detail_data.json"
CLAIM_LIST_CSV = Path(settings.BASE_DIR) / "data" / "claim_list_data.csv"
CLAIM_DETAIL_CSV = Path(settings.BASE_DIR) / "data" / "claim_detail_data.csv"

#write to claim_list_data files
def save_claim_list(claim):
    
    original_id = claim.claim_id  # not Django PK, actual claim id

    #JSON update
    try:
        with open(CLAIM_LIST_JSON, "r", encoding="utf-8") as f:             #open the file in read mode
            data = json.load(f)
    except FileNotFoundError:
        data = None
    
    if data is not None:                                                    #will only write if the file exists
        #bool check for update status 
        updated = False
        for item in data:
            if item.get("id") == original_id:                               #if id matches the claim id being edited, the attributes are updated with respective typecasting
                item.update({
                    "patient_name": str(claim.patient_name),
                    "billed_amount": float(claim.billed_amount),
                    "paid_amount": float(claim.paid_amount),
                    "insurer_name": str(claim.insurer_name),
                    "status": str(claim.status),
                    "discharge_date": str(claim.discharge_date),
                })
                updated = True  #set bool to true
                break

        #error case
        if not updated:
            print(f"Claim id={original_id} not found in JSON!")

        else:
            with open(CLAIM_LIST_JSON, "w", encoding="utf-8") as f:             #open file in write mode and overwrite with updated values
                json.dump(data, f, indent=2)

            #output message 
            print(f"JSON saved to: {CLAIM_LIST_JSON}")

    #CSV update
    try:
        with open(CLAIM_LIST_CSV, "r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f, delimiter="|")               # the csv files use pipe delimiter
            rows = list(reader)
            fieldnames = reader.fieldnames
    except FileNotFoundError:
        rows = None

    if rows is not None:                                             #will only write if the file exists
        #bool
        updated = False
        for row in rows:
            if int(row["id"]) == original_id:                        #if id matches the claim id being edited, the attributes are updated, all strings 
                row.update({
                    "patient_name": str(claim.patient_name),
                    "billed_amount": str(claim.billed_amount),
                    "paid_amount": str(claim.paid_amount),
                    "insurer_name": str(claim.insurer_name),
                    "status": str(claim.status),
                    "discharge_date": str(claim.discharge_date),
                })
                updated = True #update bool
                break

        #error case
        if not updated:
            print(f"Claim id={original_id} not found in CSV!")

        else:
            with open(CLAIM_LIST_CSV, "w", encoding="utf-8", newline="") as f:      #rewrite the file 
                writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter="|")
                writer.writeheader()
                writer.writerows(rows)

            #output message 
            print(f"CSV saved to: {CLAIM_LIST_CSV}")


#write to claim_detail_data files 
def save_claim_detail(claim_detail):
   
   #if no claim details, it ends the function call
    if not claim_detail:
        return

    original_id = claim_detail.claim.claim_id   # original id storing 

    #JSON update
    try:
        with open(CLAIM_DETAIL_JSON, "r", encoding="utf-8") as f:       #open file in read mode and load to data
            data = json.load(f)
    except FileNotFoundError:
        data = None
    
    if data is not None:                                                #will only write if the file exists
        #bool variable
        updated = False
        for item in data:                                                   #if there is a id match, update the denial and cpt, both strings
            if item.get("claim_id") == original_id:
                item.update({
                    "denial_reason": str(claim_detail.denial_reason),
                    "cpt_codes": str(claim_detail.cpt_codes),
                })
                updated = True  #update bool
                break

        #error case 
        if not updated:
            print(f"Claim_detail claim_id={original_id} not found in JSON!")

        else:
            with open(CLAIM_DETAIL_JSON, "w", encoding="utf-8") as f:           #open file in write mode and overwrite 
                json.dump(data, f, indent=2)

            #output message 
            print(f"JSON saved to: {CLAIM_DETAIL_JSON}")

    #CSV update
    try:
        with open(CLAIM_DETAIL_CSV, "r", encoding="utf-8", newline="") as f:    #open file in read mode
            reader = csv.DictReader(f, delimiter="|")                           #use pipe delimiters 
            rows = list(reader)
            fieldnames = reader.fieldnames
    except FileNotFoundError:
        rows = None
    
    if rows is not None:                                                         #will only write if the file exists
        #bool variable
        updated = False
        for row in rows:
            if int(row["claim_id"]) == original_id:                              #if there is a id match, update the denial and cpt, both strings
                row.update({
                    "denial_reason": str(claim_detail.denial_reason),
                    "cpt_codes": str(claim_detail.cpt_codes),
                })
                updated = True      #set bool to true
                break

        #error case
        if not updated:
            print(f"Claim_detail claim_id={original_id} not found in CSV!")

        else:
            with open(CLAIM_DETAIL_CSV, "w", encoding="utf-8", newline="") as f:      #open in write mode and overwrite data
                writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter="|")
                writer.writeheader()
                writer.writerows(rows)
            #output message 
            print(f"CSV saved to: {CLAIM_DETAIL_CSV}")

#edit claim function
def edit_claim(request, pk):
    claim = get_object_or_404(Claim, pk=pk) #get claim object
    claim_detail = claim.details.first()  # first instance of claim details for a claim, since there should only be one 

    #if the form was submitted
    if request.method == "POST":
        form = EditClaimForm(request.POST, instance=claim)
        if form.is_valid():                                     #check validity and save 
            form.save()                                         #updates the Claim model
            
            if claim_detail:
                cpt_codes = form.cleaned_data.get("cpt_codes")                  #get cpt and denial reason attribute values from form
                denial_reason = form.cleaned_data.get("denial_reason")
                cpt_mode = form.cleaned_data.get("cpt_mode", "overwrite")       #retrieves mode, sets overwrite as default
                denial_mode = form.cleaned_data.get("denial_mode", "overwrite") 
                print(denial_mode)

                if cpt_codes:                                                   #if cpt codes are being appended, seperate them with a comma
                    if cpt_mode == "Append":                                    #using "Append" since the clean form function capitalizes it 
                        claim_detail.cpt_codes = (
                            (claim_detail.cpt_codes + "," + cpt_codes)
                            if claim_detail.cpt_codes else cpt_codes            #if there was no codes to begin with, simply add the new codes
                        )
                    else:
                        claim_detail.cpt_codes = cpt_codes                      #overwrite option 

                if denial_reason:
                    if denial_mode == "Append":                                        #append denial reasons separated with period
                        claim_detail.denial_reason = (
                            (claim_detail.denial_reason + ". " + denial_reason)
                            if claim_detail.denial_reason else denial_reason    #no existing denial reasons case
                        )
                    else:
                        claim_detail.denial_reason = denial_reason              #overwrite option

                claim_detail.save()                                             #update ClaimDetails model 

            # Write to files
            save_claim_list(claim)
            save_claim_detail(claim_detail)

            # Return the form again with success message
            context = {"form": form, "claim": claim, "success": "Claim updated successfully!"}
            return render(request, "claims/edit_claim.html", context)
           

    else:

        form = EditClaimForm(instance=claim) #populated form with both claim and claim details
        
    #render the prepopulated form 
    return render(request, "claims/edit_claim.html", {"form": form, "claim": claim})