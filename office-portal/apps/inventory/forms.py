"""Envanter uygulamasi icin tum ModelForm siniflari."""
from django import forms
from django.utils import timezone

from .mixins import BootstrapFormMixin, HtmlDateInput
from .models import Assignment, Company, Device, Employee


class EmployeeForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Employee
        fields = [
            "first_name",
            "last_name",
            "email",
            "tc_kimlik_no",
            "hire_date",
            "company",
            "profile_photo",
            "is_active",
        ]
        labels = {
            "first_name": "Ad",
            "last_name": "Soyad",
            "email": "E-posta",
            "tc_kimlik_no": "TC Kimlik No",
            "hire_date": "Ise Giris Tarihi",
            "company": "Sirket",
            "profile_photo": "Profil Fotografi",
            "is_active": "Aktif Calisan",
        }
        widgets = {
            "hire_date": HtmlDateInput(),
            "tc_kimlik_no": forms.TextInput(
                attrs={"inputmode": "numeric", "maxlength": "11", "placeholder": "11 haneli TC Kimlik No"}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_bootstrap_classes()

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        qs = Employee.objects.filter(email__iexact=email).exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("Bu e-posta adresi baska bir calisan tarafindan kullaniliyor.")
        return email

    def clean_tc_kimlik_no(self):
        """TC Kimlik No'yu bicim ve benzersizlik acisindan dogrular."""
        value = self.cleaned_data["tc_kimlik_no"].strip()
        if not value.isdigit():
            raise forms.ValidationError("TC Kimlik No yalnizca rakamlardan olusmalidir.")
        if len(value) != 11:
            raise forms.ValidationError("TC Kimlik No 11 haneli olmalidir.")
        if Employee.objects.filter(tc_kimlik_no=value).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("Bu TC Kimlik No baska bir personele kayitli.")
        return value


class EmployeePhotoForm(BootstrapFormMixin, forms.ModelForm):
    """Profil sayfasindan sadece fotograf guncellemek icin kullanilan sade form."""

    class Meta:
        model = Employee
        fields = ["profile_photo"]
        labels = {"profile_photo": "Profil Fotografi"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_bootstrap_classes()


class DeviceForm(BootstrapFormMixin, forms.ModelForm):
    """Cihaz stok kaydi formu. Yalnizca cihaz adi ve toplam adet girilir."""

    class Meta:
        model = Device
        fields = ["name", "total_quantity"]
        labels = {"name": "Cihaz Adi", "total_quantity": "Toplam Adet"}
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "Orn: Apple MacBook Air M4"}),
            "total_quantity": forms.NumberInput(attrs={"min": "0", "step": "1"}),
        }
        help_texts = {"name": "Marka ve modeli tek isim olarak yazin."}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_bootstrap_classes()

    def clean_name(self):
        value = self.cleaned_data["name"].strip()
        if Device.objects.filter(name__iexact=value).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("Bu isimde bir cihaz zaten var. Mevcut kaydin adedini guncelleyin.")
        return value

    def clean_total_quantity(self):
        """Toplam adet, halihazirda zimmette olan adedin altina dusurulemez."""
        value = self.cleaned_data["total_quantity"]
        if self.instance.pk:
            assigned = self.instance.assignments.filter(returned=False).count()
            if value < assigned:
                raise forms.ValidationError(
                    f"Bu cihazdan {assigned} adet zimmette. Toplam adet {assigned} degerinin altina dusurulemez."
                )
        return value


class CompanyForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Company
        fields = ["name"]
        labels = {"name": "Sirket Adi"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_bootstrap_classes()


class AssignmentCreateForm(BootstrapFormMixin, forms.ModelForm):
    """Yeni zimmet olusturma formunun ortak (cihazdan bagimsiz) alanlari.

    Zimmetlenecek cihazlar bu formda degil, AssignmentItemFormSet icindeki
    'cihaz + adet' satirlarinda toplanir.
    """

    class Meta:
        model = Assignment
        fields = ["employee", "assigned_date", "expected_return_date", "notes"]
        labels = {
            "employee": "Calisan",
            "assigned_date": "Teslim Tarihi",
            "expected_return_date": "Beklenen Iade Tarihi",
            "notes": "Not",
        }
        widgets = {
            "assigned_date": HtmlDateInput(),
            "expected_return_date": HtmlDateInput(),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["employee"].queryset = Employee.objects.filter(is_active=True).select_related("company")
        self.fields["assigned_date"].initial = timezone.localdate()
        self._apply_bootstrap_classes()


class AssignmentItemForm(BootstrapFormMixin, forms.Form):
    """Zimmet formundaki tek bir 'cihaz + adet' satiri."""

    device = forms.ModelChoiceField(
        queryset=Device.objects.none(), label="Cihaz", empty_label="Cihaz seciniz..."
    )
    quantity = forms.IntegerField(
        label="Adet",
        min_value=1,
        initial=1,
        widget=forms.NumberInput(attrs={"min": "1", "step": "1"}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Yalnizca bosta adedi olan cihazlar secilebilir.
        self.fields["device"].queryset = Device.objects.with_available_stock().order_by("name")
        self._apply_bootstrap_classes()

    def clean(self):
        cleaned_data = super().clean()
        device = cleaned_data.get("device")
        quantity = cleaned_data.get("quantity")
        if device and quantity and device.available_count < quantity:
            self.add_error(
                "quantity",
                f"{device} icin bosta yalnizca {device.available_count} adet var.",
            )
        return cleaned_data


# Zimmet formundaki cihaz satirlari. En az bir satir doldurulmasi zorunludur;
# "+ Urun Ekle" butonu istenildigi kadar satir ekleyebilir.
# extra=0: form tek satirla acilir (Django toplam satiri max(initial, min_num) +
# extra olarak hesaplar; extra=1 olsaydi acilista bos iki satir gorunurdu).
AssignmentItemFormSet = forms.formset_factory(
    AssignmentItemForm,
    extra=0,
    min_num=1,
    validate_min=True,
)


class AssignmentReturnForm(BootstrapFormMixin, forms.ModelForm):
    """Bir zimmetin iade islemi icin kullanilan form.

    Secilen iade durumu, iade tutanagindaki kutucugu isaretler.
    """

    class Meta:
        model = Assignment
        fields = ["returned_date", "return_condition", "damage_description", "return_notes"]
        labels = {
            "returned_date": "Iade Tarihi",
            "return_condition": "Iade Durumu",
            "damage_description": "Hasar / Eksik Aciklamasi",
            "return_notes": "Iade Notu",
        }
        widgets = {
            "returned_date": HtmlDateInput(),
            "return_condition": forms.RadioSelect(),
            "damage_description": forms.Textarea(
                attrs={"rows": 3, "placeholder": "Hasarli ya da eksik teslim edildiyse detayini yaziniz."}
            ),
            "return_notes": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["return_condition"].required = True
        self.fields["return_condition"].choices = Assignment.ReturnCondition.choices
        # Varsayilan olarak bugun gelir, ama eski kayitlari sisteme gecirirken
        # (geriye donuk tarihli iade) degistirilebilir olsun diye zorunlu
        # kilinmaz — bos birakilirsa services.return_device bugunu kullanir.
        # NOT: field.initial degil form.initial['returned_date'] set edilir —
        # ModelForm, henuz iade edilmemis instance'tan (returned_date=None)
        # gelen None degeri initial dict'e zaten yazdigi icin field.initial
        # devreye girmez; alanin dolu gorunmesi icin bu sart.
        self.fields["returned_date"].required = False
        self.initial["returned_date"] = self.instance.returned_date or timezone.localdate()
        self._apply_bootstrap_classes()

    def clean(self):
        cleaned_data = super().clean()
        condition = cleaned_data.get("return_condition")
        description = (cleaned_data.get("damage_description") or "").strip()
        if condition in (Assignment.ReturnCondition.DAMAGED, Assignment.ReturnCondition.MISSING) and not description:
            self.add_error(
                "damage_description",
                "Hasarli ya da eksik teslimde hasar/eksik aciklamasi zorunludur.",
            )
        return cleaned_data


class DeviceImportForm(BootstrapFormMixin, forms.Form):
    """Excel (.xlsx) dosyasindan toplu cihaz stogu eklemek icin kullanilan form."""

    excel_file = forms.FileField(
        label="Excel Dosyasi (.xlsx)",
        help_text="Sutunlar: Cihaz Adi, Toplam Adet",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_bootstrap_classes()

    def clean_excel_file(self):
        file = self.cleaned_data["excel_file"]
        if not file.name.lower().endswith(".xlsx"):
            raise forms.ValidationError("Lutfen .xlsx uzantili bir Excel dosyasi yukleyin.")
        return file


class DeviceSearchForm(forms.Form):
    """Cihaz listesi icin arama formu."""

    q = forms.CharField(required=False, label="Ara")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["q"].widget.attrs.update({"class": "form-control", "placeholder": "Cihaz adi ara..."})


class EmployeeSearchForm(forms.Form):
    """Calisan listesi icin arama ve filtreleme formu."""

    q = forms.CharField(required=False, label="Ara")
    company = forms.ModelChoiceField(queryset=Company.objects.all(), required=False, label="Sirket")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["q"].widget.attrs.update(
            {"class": "form-control", "placeholder": "Ad, soyad, e-posta, TC kimlik no..."}
        )
        self.fields["company"].widget.attrs["class"] = "form-select"


class AssignmentSearchForm(forms.Form):
    """Zimmet listesi icin arama ve filtreleme formu."""

    q = forms.CharField(required=False, label="Ara")
    status = forms.ChoiceField(
        choices=[
            ("", "Tumu"),
            ("active", "Aktif (Iade Edilmemis)"),
            ("returned", "Iade Edilmis"),
            ("overdue", "Gecikmis"),
        ],
        required=False,
        label="Durum",
    )
    date_from = forms.DateField(required=False, label="Teslim (Baslangic)", widget=HtmlDateInput())
    date_to = forms.DateField(required=False, label="Teslim (Bitis)", widget=HtmlDateInput())
    return_date_from = forms.DateField(
        required=False, label="Iade (Baslangic)", widget=HtmlDateInput()
    )
    return_date_to = forms.DateField(
        required=False, label="Iade (Bitis)", widget=HtmlDateInput()
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["q"].widget.attrs.update({"class": "form-control", "placeholder": "Calisan veya cihaz ara..."})
        self.fields["status"].widget.attrs["class"] = "form-select"
        for field_name in ("date_from", "date_to", "return_date_from", "return_date_to"):
            self.fields[field_name].widget.attrs["class"] = "form-control"
