"""
Views for the Employee Payment Transaction platform.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count, Q
from django.db.models.functions import TruncMonth
from django.http import JsonResponse

from .models import Department, Employee, PayrollTransaction, TransactionAudit
from .forms import (
    DepartmentForm,
    EmployeeForm,
    PayrollTransactionForm,
    TransactionStatusForm,
    SignUpForm,
)


# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------

def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, 'Account created. Please log in.')
            return redirect('login')
    else:
        form = SignUpForm()
    return render(request, 'registration/signup.html', {'form': form})


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

@login_required
def dashboard(request):
    total_employees = Employee.objects.count()
    active_employees = Employee.objects.filter(
        employment_status=Employee.EmploymentStatus.ACTIVE
    ).count()
    total_departments = Department.objects.count()
    total_transactions = PayrollTransaction.objects.count()

    pending_txns = PayrollTransaction.objects.filter(
        status=PayrollTransaction.PaymentStatus.PENDING
    ).count()
    paid_txns = PayrollTransaction.objects.filter(
        status=PayrollTransaction.PaymentStatus.PAID
    ).count()

    total_paid_amount = PayrollTransaction.objects.filter(
        status=PayrollTransaction.PaymentStatus.PAID
    ).aggregate(total=Sum('amount'))['total'] or 0

    recent_txns = PayrollTransaction.objects.select_related('employee', 'employee__department')[:10]

    # Monthly payout summary
    monthly = (
        PayrollTransaction.objects
        .filter(status=PayrollTransaction.PaymentStatus.PAID)
        .annotate(month=TruncMonth('transaction_date'))
        .values('month')
        .annotate(total=Sum('amount'))
        .order_by('month')
    )

    # Transactions by type
    by_type = (
        PayrollTransaction.objects
        .values('transaction_type')
        .annotate(count=Count('id'), total=Sum('amount'))
    )

    # Transactions by department
    by_dept = (
        PayrollTransaction.objects
        .select_related('employee__department')
        .values('employee__department__name')
        .annotate(count=Count('id'), total=Sum('amount'))
    )

    context = {
        'total_employees': total_employees,
        'active_employees': active_employees,
        'total_departments': total_departments,
        'total_transactions': total_transactions,
        'pending_txns': pending_txns,
        'paid_txns': paid_txns,
        'total_paid_amount': total_paid_amount,
        'recent_txns': recent_txns,
        'monthly': monthly,
        'by_type': by_type,
        'by_dept': by_dept,
    }
    return render(request, 'transactions/dashboard.html', context)


# ---------------------------------------------------------------------------
# Department views
# ---------------------------------------------------------------------------

@login_required
def department_list(request):
    departments = Department.objects.annotate(employee_count=Count('employees'))
    return render(request, 'transactions/department_list.html', {'departments': departments})


@login_required
def department_create(request):
    if request.method == 'POST':
        form = DepartmentForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Department created successfully.')
            return redirect('department_list')
    else:
        form = DepartmentForm()
    return render(request, 'transactions/form.html', {'form': form, 'title': 'Create Department'})


@login_required
def department_update(request, pk):
    department = get_object_or_404(Department, pk=pk)
    if request.method == 'POST':
        form = DepartmentForm(request.POST, instance=department)
        if form.is_valid():
            form.save()
            messages.success(request, 'Department updated successfully.')
            return redirect('department_list')
    else:
        form = DepartmentForm(instance=department)
    return render(request, 'transactions/form.html', {'form': form, 'title': 'Edit Department'})


@login_required
def department_delete(request, pk):
    department = get_object_or_404(Department, pk=pk)
    if request.method == 'POST':
        department.delete()
        messages.success(request, 'Department deleted.')
        return redirect('department_list')
    return render(request, 'transactions/confirm_delete.html', {'object': department, 'type': 'department'})


# ---------------------------------------------------------------------------
# Employee views
# ---------------------------------------------------------------------------

@login_required
def employee_list(request):
    employees = Employee.objects.select_related('department').all()
    return render(request, 'transactions/employee_list.html', {'employees': employees})


@login_required
def employee_detail(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    txns = employee.transactions.all()
    total_paid = txns.filter(status=PayrollTransaction.PaymentStatus.PAID).aggregate(
        total=Sum('amount')
    )['total'] or 0
    return render(request, 'transactions/employee_detail.html', {
        'employee': employee, 'txns': txns, 'total_paid': total_paid
    })


@login_required
def employee_create(request):
    if request.method == 'POST':
        form = EmployeeForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Employee created successfully.')
            return redirect('employee_list')
    else:
        form = EmployeeForm()
    return render(request, 'transactions/form.html', {'form': form, 'title': 'Create Employee'})


@login_required
def employee_update(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    if request.method == 'POST':
        form = EmployeeForm(request.POST, instance=employee)
        if form.is_valid():
            form.save()
            messages.success(request, 'Employee updated successfully.')
            return redirect('employee_list')
    else:
        form = EmployeeForm(instance=employee)
    return render(request, 'transactions/form.html', {'form': form, 'title': 'Edit Employee'})


@login_required
def employee_delete(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    if request.method == 'POST':
        employee.delete()
        messages.success(request, 'Employee deleted.')
        return redirect('employee_list')
    return render(request, 'transactions/confirm_delete.html', {'object': employee, 'type': 'employee'})


# ---------------------------------------------------------------------------
# Transaction views
# ---------------------------------------------------------------------------

@login_required
def transaction_list(request):
    txns = PayrollTransaction.objects.select_related('employee', 'employee__department', 'processed_by').all()

    # Filters
    status = request.GET.get('status')
    txn_type = request.GET.get('type')
    employee_q = request.GET.get('q')

    if status:
        txns = txns.filter(status=status)
    if txn_type:
        txns = txns.filter(transaction_type=txn_type)
    if employee_q:
        txns = txns.filter(
            Q(employee__first_name__icontains=employee_q) |
            Q(employee__last_name__icontains=employee_q) |
            Q(employee__employee_id__icontains=employee_q)
        )

    return render(request, 'transactions/transaction_list.html', {
        'txns': txns,
        'status_choices': PayrollTransaction.PaymentStatus.choices,
        'type_choices': PayrollTransaction.TransactionType.choices,
        'selected_status': status or '',
        'selected_type': txn_type or '',
        'search_q': employee_q or '',
    })


@login_required
def transaction_detail(request, pk):
    txn = get_object_or_404(PayrollTransaction, pk=pk)
    audits = txn.audits.all()

    if request.method == 'POST':
        status_form = TransactionStatusForm(request.POST)
        if status_form.is_valid():
            new_status = status_form.cleaned_data['new_status']
            old_status = txn.status

            if new_status != old_status:
                txn.status = new_status
                txn.processed_by = request.user
                txn.save()

                TransactionAudit.objects.create(
                    transaction=txn,
                    previous_status=old_status,
                    new_status=new_status,
                    changed_by=request.user,
                    remark=status_form.cleaned_data.get('remark', ''),
                )
                messages.success(request, f'Transaction status updated to {new_status}.')
            return redirect('transaction_detail', pk=txn.pk)
    else:
        status_form = TransactionStatusForm()

    return render(request, 'transactions/transaction_detail.html', {
        'txn': txn, 'audits': audits, 'status_form': status_form,
    })


@login_required
def transaction_create(request):
    if request.method == 'POST':
        form = PayrollTransactionForm(request.POST)
        if form.is_valid():
            txn = form.save(commit=False)
            txn.processed_by = request.user
            txn.save()
            TransactionAudit.objects.create(
                transaction=txn,
                previous_status='',
                new_status=txn.status,
                changed_by=request.user,
                remark='Transaction created',
            )
            messages.success(request, 'Transaction created successfully.')
            return redirect('transaction_list')
    else:
        form = PayrollTransactionForm()
    return render(request, 'transactions/form.html', {'form': form, 'title': 'Create Transaction'})


@login_required
def transaction_update(request, pk):
    txn = get_object_or_404(PayrollTransaction, pk=pk)
    if txn.status != PayrollTransaction.PaymentStatus.PENDING:
        messages.error(request, 'Only pending transactions can be edited.')
        return redirect('transaction_detail', pk=txn.pk)

    if request.method == 'POST':
        form = PayrollTransactionForm(request.POST, instance=txn)
        if form.is_valid():
            form.save()
            messages.success(request, 'Transaction updated successfully.')
            return redirect('transaction_list')
    else:
        form = PayrollTransactionForm(instance=txn)
    return render(request, 'transactions/form.html', {'form': form, 'title': 'Edit Transaction'})


@login_required
def transaction_delete(request, pk):
    txn = get_object_or_404(PayrollTransaction, pk=pk)
    if request.method == 'POST':
        txn.delete()
        messages.success(request, 'Transaction deleted.')
        return redirect('transaction_list')
    return render(request, 'transactions/confirm_delete.html', {'object': txn, 'type': 'transaction'})


# ---------------------------------------------------------------------------
# API – JSON endpoints for charts
# ---------------------------------------------------------------------------

@login_required
def api_chart_data(request):
    """Returns JSON for the dashboard charts."""
    by_type = (
        PayrollTransaction.objects
        .values('transaction_type')
        .annotate(count=Count('id'), total=Sum('amount'))
    )
    by_status = (
        PayrollTransaction.objects
        .values('status')
        .annotate(count=Count('id'))
    )
    monthly = (
        PayrollTransaction.objects
        .filter(status=PayrollTransaction.PaymentStatus.PAID)
        .annotate(month=TruncMonth('transaction_date'))
        .values('month')
        .annotate(total=Sum('amount'))
        .order_by('month')
    )

    return JsonResponse({
        'by_type': list(by_type),
        'by_status': list(by_status),
        'monthly': [
            {'month': m['month'].strftime('%Y-%m'), 'total': float(m['total'])}
            for m in monthly
        ],
    })
