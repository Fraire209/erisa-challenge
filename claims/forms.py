from django import forms
from .models import Note

class NoteForm(forms.ModelForm):   #builds form based on existing fields
    class Meta:
        model = Note               #ties model to Note db defined in models
        fields = ['text']          #edits only text field
        widgets = {
            'text': forms.Textarea(attrs={'rows': 3, 'class': 'w-full p-2 border rounded'}),    #stylization for the text area
        }
