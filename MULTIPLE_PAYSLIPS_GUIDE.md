# Multiple Payslips per Employee Guide

## Problem
Board employees need 2 separate payslips with different wages:
- Board Meeting Fee payslip
- Committee Meeting Fee payslip

Currently, an employee can only have one active contract with one wage at a time.

## Solution Options

### Option 1: Multiple Contracts (RECOMMENDED) ✅

**Best for:** Different payment types with different wages and potentially different salary structures.

#### How It Works:
1. Create **two separate contracts** for the same employee:
   - Contract 1: "Board Meeting Fees" with board meeting wage
   - Contract 2: "Committee Meeting Fees" with committee meeting wage

2. Both contracts can be **active simultaneously** (they're just different versions)

3. When creating payslips:
   - Select the appropriate contract for each payslip
   - Each payslip will use the wage and structure from its selected contract

#### Implementation Steps:

1. **Create Contracts:**
   ```
   Employee: John Doe
   
   Contract 1:
   - Name: "Board Meeting Fees - John Doe"
   - Date Version: [Start Date]
   - Wage: [Board Meeting Fee Amount]
   - Structure: [Board Meeting Structure] (optional, can use same structure)
   
   Contract 2:
   - Name: "Committee Meeting Fees - John Doe"
   - Date Version: [Start Date]
   - Wage: [Committee Meeting Fee Amount]
   - Structure: [Committee Meeting Structure] (optional)
   ```

2. **Create Payslips:**
   - Payslip 1: Select Employee → Select "Board Meeting Fees" contract → Compute
   - Payslip 2: Select Employee → Select "Committee Meeting Fees" contract → Compute

#### Advantages:
- ✅ Clean separation of payment types
- ✅ Different salary structures per payment type (if needed)
- ✅ Easy to track and report separately
- ✅ No code changes required
- ✅ Works with existing payroll system

#### Disadvantages:
- ⚠️ Need to maintain multiple contracts per employee
- ⚠️ Contract name should clearly indicate the payment type

---

### Option 2: Payslip Type/Category Field

**Best for:** When you want to differentiate payslips but use the same contract structure.

#### Implementation:
Add a field to distinguish payment types and use inputs or override wage calculation.

**Code Changes Needed:**
1. Add `payslip_type` field to `hr.payslip`
2. Modify wage calculation based on type
3. Update views to show the field

#### Advantages:
- ✅ Single contract per employee
- ✅ Clear differentiation in payslip

#### Disadvantages:
- ⚠️ Requires code changes
- ⚠️ More complex wage calculation logic
- ⚠️ May need to modify salary rules

---

### Option 3: Payslip Inputs Only

**Best for:** When the base wage is the same but you add different amounts.

#### How It Works:
1. Use the same contract for both payslips
2. Use **Payslip Inputs** to add:
   - Board Meeting Fee amount
   - Committee Meeting Fee amount
3. Create salary rules that use these inputs

#### Advantages:
- ✅ Single contract
- ✅ Flexible amounts per payslip

#### Disadvantages:
- ⚠️ Base wage is the same (may not fit your use case)
- ⚠️ Requires salary rule configuration
- ⚠️ Less clear separation

---

## Recommended Implementation: Option 1

### Step-by-Step Guide:

#### 1. Create Board Meeting Contract

1. Go to **Employees → [Employee] → Contracts**
2. Click **Create**
3. Fill in:
   - **Name**: "Board Meeting Fees - [Employee Name]"
   - **Date Version**: Start date
   - **Wage**: Board meeting fee amount (e.g., 50,000)
   - **Structure**: Select appropriate salary structure
   - **Journal**: Select salary journal (if different from default)
4. Save

#### 2. Create Committee Meeting Contract

1. Go to **Employees → [Employee] → Contracts**
2. Click **Create**
3. Fill in:
   - **Name**: "Committee Meeting Fees - [Employee Name]"
   - **Date Version**: Start date (can be same as board contract)
   - **Wage**: Committee meeting fee amount (e.g., 30,000)
   - **Structure**: Select appropriate salary structure
   - **Journal**: Select salary journal (if different from default)
4. Save

#### 3. Create Payslips

**For Board Meeting Payslip:**
1. Go to **Payroll → Payslips → Create**
2. Select:
   - **Employee**: [Employee Name]
   - **Contract**: "Board Meeting Fees - [Employee Name]"
   - **Date From/To**: Pay period
3. Click **Compute Sheet**
4. Review and confirm

**For Committee Meeting Payslip:**
1. Go to **Payroll → Payslips → Create**
2. Select:
   - **Employee**: [Employee Name]
   - **Contract**: "Committee Meeting Fees - [Employee Name]"
   - **Date From/To**: Pay period (can be same period)
3. Click **Compute Sheet**
4. Review and confirm

### Tips:

1. **Contract Naming Convention:**
   - Use clear names: "Board Fees - John Doe", "Committee Fees - John Doe"
   - This makes it easy to select the right contract when creating payslips

2. **Contract Dates:**
   - Both contracts can have the same start date
   - They can both be active simultaneously
   - The system allows multiple active contracts per employee

3. **Salary Structures:**
   - You can use the same structure for both contracts
   - Or create separate structures if rules differ (e.g., different deductions)

4. **Reporting:**
   - Each payslip will have separate journal entries
   - Easy to filter and report by contract type
   - Can create custom reports grouping by contract name

5. **Bulk Creation:**
   - When creating payslips in batch (Payslip Run), you'll need to:
     - Create separate payslip runs for each payment type, OR
     - Manually select contracts when creating individual payslips

---

## Alternative: Enhanced Contract Type Field

If you want to make contract selection easier, you could add a "Contract Type" field:

### Implementation:
1. Add `contract_type` field to `hr.version` (contract model)
2. Add selection: `[('board', 'Board Meeting'), ('committee', 'Committee Meeting'), ('regular', 'Regular Salary')]`
3. Add filter in payslip creation to show contracts by type
4. This makes it easier to identify which contract to use

**Would you like me to implement this enhancement?**

---

## Summary

**Recommended Approach:** Use **Option 1 (Multiple Contracts)**

- ✅ No code changes required
- ✅ Works immediately with existing system
- ✅ Clean separation of payment types
- ✅ Easy to maintain and report
- ✅ Flexible for future requirements

Simply create two contracts per board employee and select the appropriate contract when creating each payslip.
