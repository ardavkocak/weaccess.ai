"""Doğum & Yıl Takibi icin ModelForm'lar — PDF disinda manuel kayit ekleme/duzenleme icin."""
from django import forms

from apps.inventory.mixins import BootstrapFormMixin, HtmlDateInput

from .models import HrEmployee


class HrEmployeeForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = HrEmployee
        fields = [
            "full_name", "department", "role", "hire_date",
            "work_model", "birth_date", "blood_type", "allergy_info",
        ]
        widgets = {
            "hire_date": HtmlDateInput(),
            "birth_date": HtmlDateInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_bootstrap_classes()
