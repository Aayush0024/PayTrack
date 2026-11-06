"""
Forms for creating and updating employees, departments, and transactions.
"""

from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Department, Employee, PayrollTransaction


class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = ['name', 'code', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }


class EmployeeForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = [
            'employee_id', 'first_name', 'last_name', 'email', 'phone',
            'department', 'designation', 'base_salary', 'employment_status', 'hire_date',
        ]
        widgets = {
            'hire_date': forms.DateInput(attrs={'type': 'date'}),
            'base_salary': forms.NumberInput(attrs={'step': '0.01'}),
        }


class PayrollTransactionForm(forms.ModelForm):
    class Meta:
        model = PayrollTransaction
        fields = [
            'employee', 'transaction_type', 'amount', 'description',
            'payment_method', 'pay_period', 'transaction_date',
        ]
        widgets = {
            'transaction_date': forms.DateInput(attrs={'type': 'date'}),
            'amount': forms.NumberInput(attrs={'step': '0.01'}),
            'description': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show active employees in the dropdown
        self.fields['employee'].queryset = Employee.objects.filter(
            employment_status=Employee.EmploymentStatus.ACTIVE
        )


class TransactionStatusForm(forms.Form):
    """Form to update the status of a transaction (used in the detail view)."""

    STATUS_CHOICES = [('', '--- Select status ---')] + PayrollTransaction.PaymentStatus.choices
    new_status = forms.ChoiceField(choices=STATUS_CHOICES)
    remark = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 2}))


class SignUpForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = __import__('django.contrib.auth.models', fromlist=['User']).User
        fields = ('username', 'email', 'first_name', 'last_name')
