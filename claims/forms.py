from django import forms
from .models import Note, Claim

class NoteForm(forms.ModelForm):   #builds form based on existing fields
    class Meta:
        model = Note               #ties model to Note db defined in models
        fields = ['text']          #edits only text field
        widgets = {
            'text': forms.Textarea(attrs={'rows': 3, 'class': 'w-full p-2 border rounded'}),    #stylization for the text area
        }
    
    #capitalizes first word of note
    def clean(self):
        cleaned_data = super().clean()      #get the forms cleaned data

        for field_name, value in cleaned_data.items():
            
            #capitalize only the first letter of the note
            cleaned_data[field_name] = value.capitalize()
        
        return cleaned_data


class EditClaimForm(forms.ModelForm):
    
    # Extra fields for ClaimDetail
    cpt_codes = forms.CharField(
        required=False,
        label="CPT Codes",
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border rounded',
            'placeholder': 'Enter CPT codes'
        })
    )
    
    denial_reason = forms.CharField(
        required=False, 
        label="Denial Reason",
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border rounded',
            'placeholder': 'Enter denial reason'
        })
    )

    #append or overwrite based on user selection 
    CHOICES = (
        ('overwrite', 'Overwrite existing'),
        ('append', 'Add to existing'),
    )
    
    #edit choices for both fields
    cpt_mode = forms.ChoiceField(
        choices=CHOICES,
        widget=forms.RadioSelect,
        initial='overwrite',
        label="CPT Codes Update Mode",
        required=False
    )

    denial_mode = forms.ChoiceField(
        choices=CHOICES,
        widget=forms.RadioSelect,
        initial='overwrite',
        label="Denial Reason Update Mode",
        required=False
    )

    #everything here will overwrite always if the user changes the value
    class Meta:
        model = Claim
        fields = ['patient_name', 'discharge_date', 'status', 'billed_amount', 'paid_amount', 'insurer_name']
        widgets = {
            'patient_name': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border rounded'}),
            'discharge_date': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border rounded'}),
            'status': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border rounded'}),
            'billed_amount': forms.NumberInput(attrs={'class': 'w-full px-3 py-2 border rounded'}),
            'paid_amount': forms.NumberInput(attrs={'class': 'w-full px-3 py-2 border rounded'}),
            'insurer_name': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border rounded'}),
        }

    #capitalizes every word for every character field, except denial reason where only first word is capitalized
    def clean(self):
        cleaned_data = super().clean()      #get the forms cleaned data

        for field_name, value in cleaned_data.items():
            if value and isinstance(value, str):  # only text fields
                
                if field_name == "denial_reason":
                    
                    #capitalize only the first letter
                    cleaned_data[field_name] = value.capitalize()

                else:
                    
                    #capitalize first letter of each word
                    cleaned_data[field_name] = value.title()

        return cleaned_data