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
        """Get default journal from contract if available, otherwise from settings, then first general journal"""
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
        
        # Try to get journal from settings (config parameter)
        default_journal_id = self.env['ir.config_parameter'].sudo().get_param(
            'hr_payroll_account_community.salary_journal_id')
        if default_journal_id:
            journal = self.env['account.journal'].browse(int(default_journal_id))
            if journal.exists() and journal.type == 'general':
                return journal.id
        
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
                abs_amount = abs(amount)

                # Sign-aware posting:
                # * amount > 0 (earnings, employer contributions, NET):
                #     Dr the rule's Debit Account (expense),
                #     Cr the rule's Credit Account (liability) — whichever
                #     side(s) are configured.
                # * amount < 0 (employee deductions / recoveries):
                #     Cr the liability/asset with the absolute amount. The
                #     account is taken from the Credit slot, falling back to
                #     the Debit slot so either configuration works. If both
                #     slots are set, the Debit slot is mirrored as a debit.
                # The gross expense already contains the deductions, so a
                # deduction only ever needs its liability credit.
                def _post(account_id, debit, credit, on_credit_side):
                    vals = (0, 0, {
                        'name': line.name,
                        'partner_id': line._get_partner_id(
                            credit_account=on_credit_side),
                        'account_id': account_id,
                        'journal_id': slip.journal_id.id,
                        'date': slip.date or slip.date_to,
                        'debit': debit,
                        'credit': credit,
                        'tax_line_id': line.salary_rule_id.account_tax_id.id,
                    })
                    line_ids.append(vals)
                    return debit - credit

                if amount > 0:
                    if debit_account_id:
                        debit_sum += _post(debit_account_id, abs_amount, 0.0,
                                           False)
                    if credit_account_id:
                        credit_sum -= _post(credit_account_id, 0.0,
                                            abs_amount, True)
                else:
                    liability_account_id = credit_account_id \
                        or debit_account_id
                    credit_sum -= _post(liability_account_id, 0.0, abs_amount,
                                        True)
                    if credit_account_id and debit_account_id:
                        debit_sum += _post(debit_account_id, abs_amount, 0.0,
                                           False)
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
