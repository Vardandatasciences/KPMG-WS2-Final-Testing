from django import forms
from django.core.validators import FileExtensionValidator
from .models import Vendor, VendorCapability, VendorCertification


class VendorSearchForm(forms.Form):
    """
    Form for searching vendors
    """
    search_term = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full h-11 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'Search vendors by name, capabilities, or certifications...'
        })
    )
    filter_type = forms.ChoiceField(
        required=False,
        choices=[
            ('all', 'All Vendors'),
            ('high-match', 'High Match (90%+)'),
            ('certified', 'Highly Certified'),
        ],
        initial='all',
        widget=forms.HiddenInput()
    )


class VendorManualEntryForm(forms.ModelForm):
    """
    Form for manually entering vendor information
    """
    capabilities = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'Enter capabilities separated by commas (e.g., Cloud Expert, DevOps, Security)'
        })
    )
    
    certifications = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'Enter certifications separated by commas (e.g., ISO 27001, SOC 2)'
        })
    )
    
    class Meta:
        model = Vendor
        fields = [
            'company_name', 'legal_name', 'website', 'headquarters_country',
            'industry_sector', 'employee_count', 'description', 
            'capabilities', 'certifications'
        ]

        # NOTE: email, phone, location, experience_years removed as they don't exist in vendors table
        # - email/phone: Should be added to vendor_contacts table
        # - location: Use headquarters_country instead
        # - experience_years: Calculated from onboarding_date
        
        widgets = {
            'company_name': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'Company Name'
            }),
            'legal_name': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'Legal Name'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'Contact Email'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'Contact Phone'
            }),
            'website': forms.URLInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'Website URL'
            }),
            'headquarters_country': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'Country (e.g., United States, India)'
            }),
            'industry_sector': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'Industry Sector'
            }),
            'employee_count': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'Number of Employees'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'Company Description',
                'rows': 3
            }),
        }
    
    def save(self, commit=True):
        vendor = super().save(commit=False)
        
        # Set default values
        if not vendor.risk_level:
            vendor.risk_level = 'MEDIUM'
        if not vendor.status:
            vendor.status = 'DRAFT'
        
        if commit:
            vendor.save()
            
            # Save capabilities
            capabilities = self.cleaned_data.get('capabilities', '')
            if capabilities:
                for cap in capabilities.split(','):
                    cap = cap.strip()
                    if cap:
                        VendorCapability.objects.create(
                            vendor=vendor,
                            capability_name=cap
                        )
            
            # Save certifications
            certifications = self.cleaned_data.get('certifications', '')
            if certifications:
                for cert in certifications.split(','):
                    cert = cert.strip()
                    if cert:
                        VendorCertification.objects.create(
                            vendor=vendor,
                            certification_name=cert
                        )
        
        return vendor


class VendorBulkUploadForm(forms.Form):
    """
    Form for bulk uploading vendors via CSV
    """
    csv_file = forms.FileField(
        validators=[FileExtensionValidator(allowed_extensions=['csv'])],
        widget=forms.FileInput(attrs={
            'class': 'hidden',
            'accept': '.csv'
        })
    )


class RFPVendorSelectionForm(forms.Form):
    """
    Form for selecting vendors for an RFP
    """
    selected_vendors = forms.MultipleChoiceField(
        required=False,
        widget=forms.CheckboxSelectMultiple
    )
    
    def __init__(self, *args, **kwargs):
        vendors = kwargs.pop('vendors', None)
        super().__init__(*args, **kwargs)
        
        if vendors:
            self.fields['selected_vendors'].choices = [(vendor.vendor_id, vendor.company_name) for vendor in vendors]
