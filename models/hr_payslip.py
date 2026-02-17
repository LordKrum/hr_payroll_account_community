# -*- coding: utf-8 -*-
#############################################################################
#    A part of Open HRMS Project <https://www.openhrms.com>
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class HrPayslip(models.Model):
    """ Extends the standard 'hr.payslip' model to include additional fields
        for accounting purposes."""
    _inherit = 'hr.payslip'

    date = fields.Date(string='Date Account',
                       help="Keep empty to use the period of the "
                            "validation(Payslip) date.")
    journal_id = fields.Many2one('account.journal',
                                 string='Salary Journal',
                                 required=True,
                                 help="Select Salary Journal",
                                 default=lambda self: self._default_journal_id())
    
    def _default_journal_id(self):
        """Get default journal from contract if available, otherwise first general journal"""
        # Try to get journal from contract in context (when creating from employee)
        contract_id = self.env.context.get('default_contract_id')
        if contract_id:
            contract = self.env['hr.version'].browse(contract_id)
            if contract.exists() and contract.journal_id:
                return contract.journal_id.id
        
        # Try to get journal from employee's contract if employee is in context
        employee_id = self.env.context.get('default_employee_id')
        if employee_id:
            employee = self.env['hr.employee'].browse(employee_id)
            if employee.exists() and employee.version_id and employee.version_id.journal_id:
                return employee.version_id.journal_id.id
        
        # Fallback to first general journal
        journal = self.env['account.journal'].search([('type', '=', 'general')], limit=1)
        return journal.id if journal else False
    move_id = fields.Many2one('account.move',
                              string='Accounting Entry',
                              readonly=True, copy=False,
                              help="Accounting entry associated with "
                                   "this record")

    @api.model_create_multi
    def create(self, vals_list):
        journal_id = self.env.context.get('journal_id')
        if journal_id:
            for vals in vals_list:
                vals['journal_id'] = journal_id

        return super().create(vals_list)

    @api.onchange('contract_id')
    def onchange_contract_id(self):
        """Triggered when the contract associated with the payroll slip is
            changed.This method is called when the 'contract_id' field is
            modified. It invokes the parent class's onchange method and then
            sets the 'journal_id' field based on the 'contract_id's journal or
            the default journal if no contract is selected."""
        super(HrPayslip, self).onchange_contract_id()
        if self.contract_id and self.contract_id.journal_id:
            self.journal_id = self.contract_id.journal_id
        elif not self.contract_id:
            # If no contract, use default
            default_journal = self._default_journal_id()
            if default_journal:
                self.journal_id = default_journal
    
    @api.onchange('date_to')
    def _onchange_date_to(self):
        """Set Date Account to date_to when date_to changes, if date is not already set"""
        if self.date_to and not self.date:
            self.date = self.date_to

    def action_payslip_cancel(self):
        """Cancel the payroll slip and associated accounting entries.This
        method cancels the current payroll slip by canceling its associated
        accounting entries (moves). If a move is in the 'posted' state, it is
        first uncanceled, then all moves are unlinked. Finally, the method
        calls the parent class's action_payslip_cancel method."""
        moves = self.mapped('move_id')
        moves.filtered(lambda x: x.state == 'posted').button_cancel()
        moves.unlink()
        return super(HrPayslip, self).action_payslip_cancel()

    def action_payslip_done(self):
        """Finalize and post the payroll slip, creating accounting entries.This
         method is called when marking a payroll slip as done. It calculates
         the accounting entries based on the salary details, creates a move
         (journal entry),and posts it. If necessary, adjustment entries are
         added to balance the debit and credit amounts."""
        res = super(HrPayslip, self).action_payslip_done()
        for slip in self:
            line_ids = []
            debit_sum = 0.0
            credit_sum = 0.0
            name = _('Payslip of %s') % slip.employee_id.name
            move_dict = {
                'narration': name,
                'ref': slip.number,
                'journal_id': slip.journal_id.id,
                'date': slip.date or slip.date_to,
            }
            for line in slip.details_by_salary_rule_category_ids:
                # Only create accounting entries for actual salary rules (not category summaries)
                # and only if the rule has accounts configured
                if not line.salary_rule_id:
                    continue
                # Skip if rule doesn't appear on payslip (category totals shouldn't have separate entries)
                if not line.salary_rule_id.appears_on_payslip:
                    continue
                # Skip if no accounts are configured for this rule
                if not line.salary_rule_id.account_debit_id and not line.salary_rule_id.account_credit_id:
                    continue
                # Forcefully exclude Basic Salary from accounting entries
                if line.salary_rule_id.code.upper() in ('BASIC', 'BASIC_SALARY', 'BASIC_SAL') or \
                   'basic salary' in line.salary_rule_id.name.lower():
                    continue
                
                amount = slip.company_id.currency_id.round(
                    slip.credit_note and -line.total or line.total)
                if slip.company_id.currency_id.is_zero(amount):
                    continue
                debit_account_id = line.salary_rule_id.account_debit_id.id
                credit_account_id = line.salary_rule_id.account_credit_id.id
                
                # Check if this is Net Salary - it should always credit the payable account
                # Net Salary represents what we owe the employee, so it increases liability
                is_net_salary = (
                    line.salary_rule_id.code.upper() in ('NET', 'NET_SALARY', 'NET_SAL') or
                    'net salary' in line.salary_rule_id.name.lower()
                )
                
                # Determine the type of transaction
                # Check if this is a company contribution by rule_type or category code
                is_company_contribution = False
                if line.salary_rule_id:
                    # Check rule_type field if it exists
                    if hasattr(line.salary_rule_id, 'rule_type'):
                        is_company_contribution = line.salary_rule_id.rule_type == 'company_contribution'
                    # Fallback: check category code (company contributions often have 'COMPANY' or 'COMP' in category)
                    if not is_company_contribution and line.category_id:
                        category_code = line.category_id.code.upper() if line.category_id.code else ''
                        is_company_contribution = 'COMPANY' in category_code or 'COMP' in category_code
                
                is_deduction = amount < 0.0
                abs_amount = abs(amount)
                
                if debit_account_id:
                    # Debit Account (typically Expense accounts):
                    # - Always DEBIT expense account (increases expense)
                    # - Applies to: deductions, company contributions, and other expenses
                    debit_line = (0, 0, {
                        'name': line.name,
                        'partner_id': line._get_partner_id(
                            credit_account=False),
                        'account_id': debit_account_id,
                        'journal_id': slip.journal_id.id,
                        'date': slip.date or slip.date_to,
                        'debit': abs_amount,  # Always debit expense
                        'credit': 0.0,
                        'tax_line_id': line.salary_rule_id.account_tax_id.id,
                    })
                    line_ids.append(debit_line)
                    debit_sum += debit_line[2]['debit'] - debit_line[2][
                        'credit']
                if credit_account_id:
                    # Credit Account (typically Payable accounts):
                    # - For deductions (negative): CREDIT payable (increases liability - we owe more)
                    # - For company contributions (positive): CREDIT payable (increases liability - we owe more)
                    # - For Net Salary (positive): CREDIT payable (increases liability - we owe the employee)
                    # - For other additions (positive): DEBIT payable (decreases liability - we owe less)
                    should_credit_payable = is_deduction or is_company_contribution or is_net_salary
                    credit_line = (0, 0, {
                        'name': line.name,
                        'partner_id': line._get_partner_id(credit_account=True),
                        'account_id': credit_account_id,
                        'journal_id': slip.journal_id.id,
                        'date': slip.date or slip.date_to,
                        'debit': abs_amount if not should_credit_payable else 0.0,  # Debit payable only for non-deduction, non-contribution, non-net additions
                        'credit': abs_amount if should_credit_payable else 0.0,  # Credit payable for deductions, company contributions, and net salary
                        'tax_line_id': line.salary_rule_id.account_tax_id.id,
                    })
                    line_ids.append(credit_line)
                    credit_sum += credit_line[2]['credit'] - credit_line[2][
                        'debit']
            if slip.company_id.currency_id.compare_amounts(
                    credit_sum, debit_sum) == -1:
                acc_id = slip.journal_id.default_account_id.id
                if not acc_id:
                    raise UserError(
                        _('The Expense Journal "%s" has not properly '
                          'configured the Credit Account!') % (
                            slip.journal_id.name))
                adjust_credit = (0, 0, {
                    'name': _('Adjustment Entry'),
                    'partner_id': False,
                    'account_id': acc_id,
                    'journal_id': slip.journal_id.id,
                    'date': slip.date or slip.date_to,
                    'debit': 0.0,
                    'credit': slip.company_id.currency_id.round(
                        debit_sum - credit_sum),
                })
                line_ids.append(adjust_credit)
            elif slip.company_id.currency_id.compare_amounts(
                    debit_sum, credit_sum) == -1:
                acc_id = slip.journal_id.default_account_id.id
                if not acc_id:
                    raise UserError(
                        _('The Expense Journal "%s" has not properly '
                          'configured the Debit Account!') % (
                            slip.journal_id.name))
                adjust_debit = (0, 0, {
                    'name': _('Adjustment Entry'),
                    'partner_id': False,
                    'account_id': acc_id,
                    'journal_id': slip.journal_id.id,
                    'date': slip.date or slip.date_to,
                    'debit': slip.company_id.currency_id.round(
                        credit_sum - debit_sum),
                    'credit': 0.0,
                })
                line_ids.append(adjust_debit)
            move_dict['line_ids'] = line_ids
            move = self.env['account.move'].create(move_dict)
            slip.write({'move_id': move.id, 'date': slip.date or slip.date_to})
            if not move.line_ids:
                raise UserError(
                    _("As you installed the payroll accounting module you have"
                      " to choose Debit and Credit account for at least one "
                      "salary rule in the chosen Salary Structure."))
            move.action_post()
        return res
