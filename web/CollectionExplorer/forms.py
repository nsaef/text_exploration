from django import forms
from django.utils.safestring import mark_safe

class UploadForm(forms.Form):
    doc_file = forms.FileField(
        label='Dateien auswählen',
        help_text='',
        required=False,
        widget=forms.ClearableFileInput(attrs={'accept': '.zip'}) #attrs={'multiple': True}
    )
    remote = forms.BooleanField(label=mark_safe("<br/>Dateien aus lokalem Dateisystem hochladen"), initial=True, required=False)
    remote_path = forms.CharField(label=mark_safe("<br/>Dateipfad auf Server"), max_length=512, required=False)


class TextForm(forms.Form):
    text = forms.CharField(widget=forms.Textarea)

#TODO: Add_collection_form



class Word2VecForm(forms.Form):
    CURRENT_COLLECTION = "current"
    REFERENCE_COLLECTION = "reference"

    SOURCE_CHOICES = (
        (CURRENT_COLLECTION, "Aktuelle Sammlung"),
        (REFERENCE_COLLECTION, "Referenzvokabular")
    )

    source = forms.ChoiceField(choices=SOURCE_CHOICES, label="Datenquelle auswählen")
    word_a = forms.CharField(required=False, label="Wort A")
    word_b = forms.CharField(required=False, label="verhält sich zu Wort B")
    word_c = forms.CharField(required=False, label="wie Wort C zu")
    cmp_word = forms.CharField(required=False, label="Ähnliche Worte zu: ")