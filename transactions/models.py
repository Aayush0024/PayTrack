"""
Models for the Employee Payment Transaction platform.

Employee → Department (many-to-one)
Employee → PayrollTransaction (one-to-many)  each transaction represents a salary / bonus / deduction payment
TransactionAudit → tracks status changes on each transaction
"""

from django.db import models
from django.contrib.auth.models import User


class Department(models.Model):
    """Represents an organizational department."""

    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=10, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.code})"


class Employee(models.Model):
    """Represents an employee who receives payment transactions."""

    class EmploymentStatus(models.TextChoices):
        ACTIVE = 'ACTIVE', 'Active'
        ON_LEAVE = 'ON_LEAVE', 'On Leave'
        TERMINATED = 'TERMINATED', 'Terminated'

    user = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True)
    employee_id = models.CharField(max_length=20, unique=True, help_text="Unique company employee ID")
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, related_name='employees')
    designation = models.CharField(max_length=100, blank=True)
    base_salary = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    employment_status = models.CharField(
        max_length=20, choices=EmploymentStatus.choices, default=EmploymentStatus.ACTIVE
    )
    hire_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['last_name', 'first_name']

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def __str__(self):
        return f"{self.employee_id} – {self.full_name}"


class PayrollTransaction(models.Model):
    """Represents a single payment transaction for an employee."""

    class TransactionType(models.TextChoices):
        SALARY = 'SALARY', 'Salary'
        BONUS = 'BONUS', 'Bonus'
        DEDUCTION = 'DEDUCTION', 'Deduction'
        REIMBURSEMENT = 'REIMBURSEMENT', 'Reimbursement'
        ADVANCE = 'ADVANCE', 'Advance'

    class PaymentStatus(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        APPROVED = 'APPROVED', 'Approved'
        PROCESSING = 'PROCESSING', 'Processing'
        PAID = 'PAID', 'Paid'
        REJECTED = 'REJECTED', 'Rejected'

    class PaymentMethod(models.TextChoices):
        BANK_TRANSFER = 'BANK_TRANSFER', 'Bank Transfer'
        CHEQUE = 'CHEQUE', 'Cheque'
        CASH = 'CASH', 'Cash'
        UPI = 'UPI', 'UPI'

    transaction_id = models.CharField(max_length=30, unique=True, editable=False)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=20, choices=TransactionType.choices)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    description = models.TextField(blank=True)
    payment_method = models.CharField(max_length=20, choices=PaymentMethod.choices, default=PaymentMethod.BANK_TRANSFER)
    status = models.CharField(max_length=20, choices=PaymentStatus.choices, default=PaymentStatus.PENDING)
    pay_period = models.CharField(max_length=20, help_text="e.g. 2026-11 or 2026-W44")
    processed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    transaction_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.transaction_id:
            import uuid
            self.transaction_id = f"TXN{uuid.uuid4().hex[:12].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.transaction_id} – {self.employee.full_name} – {self.amount}"


class TransactionAudit(models.Model):
    """Tracks every status change on a PayrollTransaction."""

    transaction = models.ForeignKey(PayrollTransaction, on_delete=models.CASCADE, related_name='audits')
    previous_status = models.CharField(max_length=20, blank=True)
    new_status = models.CharField(max_length=20)
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    remark = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.transaction.transaction_id}: {self.previous_status} → {self.new_status}"
