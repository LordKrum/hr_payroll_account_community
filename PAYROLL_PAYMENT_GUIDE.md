# Payroll Payment Recording Guide

## Overview

When you confirm a payslip, it creates journal entries with payable accounts (liabilities). To record the actual payment to employees, you need to create a separate payment entry that debits these payable accounts and credits your bank/cash account.

## Accounting Flow

### Step 1: Payslip Confirmation (Automatic)
When you confirm a payslip, it creates journal entries like:
- **Debit**: Salaries & Wages Expense (Gross amount)
- **Credit**: PAYE Payable (Tax deductions)
- **Credit**: Salaries Payable (Net amount owed to employee)
- **Credit**: Other Payables (e.g., NSSF, SACCO, etc.)

### Step 2: Payment Recording (Manual)
When you actually pay the employee, you need to record:
- **Debit**: Salaries Payable (reducing liability)
- **Debit**: PAYE Payable (reducing liability - when you remit to tax authority)
- **Credit**: Bank/Cash Account (money going out)

---

## Method 1: Manual Journal Entry (Recommended)

This is the most straightforward method and gives you full control.

### Steps:

1. **Go to Accounting → Journal Entries → New**

2. **Create the Payment Entry:**
   - **Journal**: Select your Bank or Cash journal
   - **Date**: Payment date
   - **Reference**: e.g., "Salary Payment - [Employee Name] - [Period]"

3. **Add Journal Items:**

   **For Net Salary Payment:**
   - **Account**: Salaries and Wages Payable (200.01.01)
   - **Partner**: Employee name
   - **Debit**: Net Salary amount (e.g., 1,000,000)
   - **Credit**: 0.00
   - **Label**: "Salary Payment - [Employee Name]"

   **For Bank/Cash:**
   - **Account**: Bank Account (e.g., 101.01.01)
   - **Partner**: Employee name
   - **Debit**: 0.00
   - **Credit**: Net Salary amount (e.g., 1,000,000)
   - **Label**: "Salary Payment - [Employee Name]"

4. **Post the Entry**

### Example Entry:
```
Account                    | Partner        | Debit      | Credit
---------------------------|----------------|------------|------------
Salaries Payable (200.01.01) | John Doe     | 1,000,000  | 0
Bank Account (101.01.01)   | John Doe       | 0          | 1,000,000
```

---

## Method 2: Payment Register (If Using Odoo Payment Module)

If you have the `account_payment` module installed, you can use the payment register.

### Steps:

1. **Go to Accounting → Vendors → Payments**

2. **Create Payment:**
   - **Payment Type**: Outbound
   - **Partner**: Employee (must be set up as a vendor/contact)
   - **Amount**: Net Salary amount
   - **Payment Method**: Bank Transfer or Check
   - **Journal**: Bank Journal

3. **Post Payment**

4. **Reconcile:**
   - Go to Accounting → Reconciliation
   - Match the payment with the payable account entries from the payslip

---

## Method 3: Batch Payment (Multiple Employees)

If paying multiple employees at once:

### Steps:

1. **Go to Accounting → Journal Entries → New**

2. **Create Batch Payment Entry:**
   - **Journal**: Bank Journal
   - **Date**: Payment date
   - **Reference**: "Salary Payments - [Period]"

3. **Add Multiple Lines:**

   **For Each Employee:**
   - **Account**: Salaries Payable
   - **Partner**: Employee name
   - **Debit**: Their net salary
   - **Credit**: 0.00

   **Single Bank Line:**
   - **Account**: Bank Account
   - **Partner**: (leave empty or use company)
   - **Debit**: 0.00
   - **Credit**: Total of all net salaries

4. **Post the Entry**

### Example Batch Entry:
```
Account                    | Partner        | Debit      | Credit
---------------------------|----------------|------------|------------
Salaries Payable           | John Doe       | 1,000,000  | 0
Salaries Payable           | Jane Smith     | 1,200,000  | 0
Salaries Payable           | Bob Johnson    | 800,000    | 0
Bank Account               |                | 0          | 3,000,000
```

---

## Method 4: Remitting Deductions (PAYE, NSSF, etc.)

When you remit deductions to authorities:

### Steps:

1. **Go to Accounting → Journal Entries → New**

2. **Create Remittance Entry:**
   - **Journal**: Bank Journal
   - **Date**: Remittance date
   - **Reference**: "PAYE Remittance - [Period]"

3. **Add Journal Items:**

   **For PAYE Remittance:**
   - **Account**: PAYE Payable (202.01.01)
   - **Partner**: (leave empty or use tax authority)
   - **Debit**: Total PAYE amount
   - **Credit**: 0.00

   **For Bank:**
   - **Account**: Bank Account
   - **Partner**: (leave empty or use tax authority)
   - **Debit**: 0.00
   - **Credit**: Total PAYE amount

4. **Post the Entry**

---

## Reconciliation

After recording payments, reconcile the accounts:

1. **Go to Accounting → Reconciliation**

2. **Select Account**: Salaries Payable (or PAYE Payable)

3. **Match Entries:**
   - Payslip entry (Credit) with Payment entry (Debit)
   - Odoo will automatically suggest matches based on partner and amount

4. **Reconcile**: Click "Reconcile" to mark as paid

---

## Important Notes

1. **Partner Field**: Always include the employee as the partner in payment entries. This enables automatic reconciliation and proper reporting.

2. **Payment Timing**: You can record payments:
   - Immediately after payslip confirmation
   - At the end of the pay period (batch payments)
   - When actual bank transfer occurs

3. **Multiple Payables**: If a payslip creates multiple payable accounts (Salaries Payable, PAYE Payable, NSSF Payable, etc.), you can:
   - Pay them all in one entry (multiple debit lines, one credit line)
   - Pay them separately (especially if remittance dates differ)

4. **Bank Reconciliation**: After recording payments, reconcile your bank statement to ensure all payments are accounted for.

---

## Quick Reference: Account Types

- **Expense Accounts** (Debit in payslip): Salaries & Wages Expense
- **Payable Accounts** (Credit in payslip): 
  - Salaries Payable (Net Salary)
  - PAYE Payable (Tax deductions)
  - NSSF Payable (Social security)
  - Other deduction payables
- **Bank/Cash Accounts** (Credit in payment): Your payment method account

---

## Troubleshooting

**Issue**: Can't find payable account entries
- **Solution**: Ensure payslip is confirmed (state = "Done") and journal entry is posted

**Issue**: Reconciliation not working
- **Solution**: Ensure partner field matches between payslip entry and payment entry

**Issue**: Payment amount doesn't match
- **Solution**: Check if you're paying net salary only, or if you need to include other amounts
