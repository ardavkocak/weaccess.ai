"""office_bot icin basit form siniflari (Bootstrap uyumlu, portal temasiyla)."""
from django import forms


class EmployeeForm(forms.Form):
    full_name = forms.CharField(label="Ad Soyad", max_length=100, widget=forms.TextInput(attrs={"class": "form-control"}))
    discord_user_id = forms.CharField(
        label="Discord Kullanıcı ID", required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "İsteğe bağlı"}),
    )
    is_active = forms.BooleanField(label="Aktif", required=False, initial=True, widget=forms.CheckboxInput(attrs={"class": "form-check-input"}))
    position = forms.CharField(label="Sıra No", required=False, widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Boş = sona ekle"}))


class MealUploadForm(forms.Form):
    excel_file = forms.FileField(label="Excel Dosyası (.xlsx)")
    replace_all = forms.BooleanField(label="Mevcut tüm menüleri sil", required=False)
