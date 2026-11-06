"""
Admin configuration for the transactions app.
"""

from django.contrib import admin
from .models import Department, Employee, PayrollTransaction, TransactionAudit


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'created_at')
    search_fields = ('name', 'code')


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('employee_id', 'full_name', 'email', 'department', 'employment_status', 'hire_date')
    list_filter = ('employment_status', 'department')
    search_fields = ('employee_id', 'first_name', 'last_name', 'email')
    raw_id_fields = ('user',)


@admin.register(PayrollTransaction)
class PayrollTransactionAdmin(admin.ModelAdmin):
    list_display = ('transaction_id', 'employee', 'transaction_type', 'amount', 'status', 'payment_method', 'transaction_date')
    list_filter = ('status', 'transaction_type', 'payment_method')
    search_fields = ('transaction_id', 'employee__first_name', 'employee__last_name', 'employee__employee_id')
    raw_id_fields = ('employee', 'processed_by')
    date_hierarchy = 'transaction_date'


@admin.register(TransactionAudit)
class TransactionAuditAdmin(admin.ModelAdmin):
    list_display = ('transaction', 'previous_status', 'new_status', 'changed_by', 'created_at')
    list_filter = ('new_status',)
    raw_id_fields = ('transaction', 'changed_by')
