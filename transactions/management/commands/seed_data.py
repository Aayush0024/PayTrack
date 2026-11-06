"""
Management command to populate the database with sample data.

Usage:
    python manage.py seed_data
"""

import datetime
import random
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from transactions.models import Department, Employee, PayrollTransaction, TransactionAudit


class Command(BaseCommand):
    help = 'Seeds the database with sample departments, employees, and transactions'

    def handle(self, *args, **kwargs):
        self.stdout.write('Seeding sample data...')

        admin = User.objects.filter(is_superuser=True).first()

        # Departments
        dept_data = [
            ('Engineering', 'ENG', 'Software development and infrastructure'),
            ('Human Resources', 'HR', 'Employee management and recruitment'),
            ('Finance', 'FIN', 'Financial operations and payroll'),
            ('Marketing', 'MKT', 'Marketing and brand management'),
            ('Operations', 'OPS', 'Day-to-day business operations'),
        ]
        departments = {}
        for name, code, desc in dept_data:
            dept, _ = Department.objects.get_or_create(
                code=code,
                defaults={'name': name, 'description': desc}
            )
            departments[code] = dept

        # Employees
        employee_data = [
            ('EMP001', 'Rahul', 'Sharma', 'rahul.sharma@company.com', 'ENG', 'Software Engineer', 85000),
            ('EMP002', 'Priya', 'Patel', 'priya.patel@company.com', 'ENG', 'Senior Developer', 110000),
            ('EMP003', 'Amit', 'Kumar', 'amit.kumar@company.com', 'HR', 'HR Manager', 75000),
            ('EMP004', 'Sneha', 'Reddy', 'sneha.reddy@company.com', 'FIN', 'Financial Analyst', 68000),
            ('EMP005', 'Vikram', 'Singh', 'vikram.singh@company.com', 'MKT', 'Marketing Lead', 72000),
            ('EMP006', 'Anita', 'Desai', 'anita.desai@company.com', 'OPS', 'Operations Executive', 55000),
            ('EMP007', 'Karan', 'Mehta', 'karan.mehta@company.com', 'ENG', 'DevOps Engineer', 95000),
            ('EMP008', 'Divya', 'Nair', 'divya.nair@company.com', 'FIN', 'Accountant', 60000),
            ('EMP009', 'Rohan', 'Gupta', 'rohan.gupta@company.com', 'MKT', 'Content Strategist', 50000),
            ('EMP010', 'Meera', 'Iyer', 'meera.iyer@company.com', 'HR', 'Recruitment Specialist', 58000),
            ('EMP011', 'Arjun', 'Rao', 'arjun.rao@company.com', 'ENG', 'Tech Lead', 130000),
            ('EMP012', 'Pooja', 'Joshi', 'pooja.joshi@company.com', 'OPS', 'Logistics Coordinator', 48000),
        ]

        statuses = ['ACTIVE', 'ACTIVE', 'ACTIVE', 'ACTIVE', 'ACTIVE', 'ACTIVE', 'ACTIVE', 'ACTIVE', 'ACTIVE', 'ACTIVE', 'ACTIVE', 'ON_LEAVE']
        employees = []
        for i, (emp_id, fname, lname, email, dept_code, designation, salary) in enumerate(employee_data):
            emp, created = Employee.objects.get_or_create(
                employee_id=emp_id,
                defaults={
                    'first_name': fname,
                    'last_name': lname,
                    'email': email,
                    'department': departments[dept_code],
                    'designation': designation,
                    'base_salary': Decimal(str(salary)),
                    'employment_status': statuses[i],
                    'hire_date': datetime.date(2022 + i % 3, (i % 12) + 1, 15),
                }
            )
            employees.append(emp)

        # Transactions
        txn_types = ['SALARY', 'SALARY', 'SALARY', 'BONUS', 'DEDUCTION', 'REIMBURSEMENT', 'ADVANCE']
        payment_methods = ['BANK_TRANSFER', 'BANK_TRANSFER', 'UPI', 'CHEQUE']
        status_choices = ['PENDING', 'APPROVED', 'PROCESSING', 'PAID', 'PAID', 'PAID', 'REJECTED']

        for emp in employees:
            for month in range(1, 7):  # Jan to Jun 2026
                txn_type = random.choice(txn_types)
                if txn_type == 'SALARY':
                    amount = emp.base_salary
                elif txn_type == 'BONUS':
                    amount = Decimal(str(random.randint(5000, 25000)))
                elif txn_type == 'DEDUCTION':
                    amount = Decimal(str(random.randint(500, 5000)))
                elif txn_type == 'REIMBURSEMENT':
                    amount = Decimal(str(random.randint(1000, 8000)))
                else:
                    amount = Decimal(str(random.randint(5000, 30000)))

                status = random.choice(status_choices)
                txn_date = datetime.date(2026, month, random.randint(1, 28))

                txn = PayrollTransaction.objects.create(
                    employee=emp,
                    transaction_type=txn_type,
                    amount=amount,
                    description=f'{txn_type.title()} payment for {emp.full_name} – 2026-{month:02d}',
                    payment_method=random.choice(payment_methods),
                    status=status,
                    pay_period=f'2026-{month:02d}',
                    processed_by=admin if admin else None,
                    transaction_date=txn_date,
                )
                TransactionAudit.objects.create(
                    transaction=txn,
                    previous_status='',
                    new_status=status,
                    changed_by=admin,
                    remark='Transaction created (seeded)',
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully seeded: {len(departments)} departments, '
                f'{len(employees)} employees, and their transactions.'
            )
        )
