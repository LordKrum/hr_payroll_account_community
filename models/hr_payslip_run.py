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
from odoo import fields, models


class HrPayslipRun(models.Model):
    """Extends the standard 'hr.payslip.run' model to include additional fields
    for managing payroll runs.
    Methods:
        compute_total_amount: Compute the total amount of the payroll run."""
    _inherit = 'hr.payslip.run'

    journal_id = fields.Many2one(comodel_name='account.journal',
                                 string='Salary Journal',
                                 required=True, help="Journal associated with "
                                                     "the record",
                                 default=lambda self: self._default_journal_id())
    
    def _default_journal_id(self):
        """Get default journal from settings, otherwise first general journal"""
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
