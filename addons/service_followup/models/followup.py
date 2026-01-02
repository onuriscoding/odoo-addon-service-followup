# -*- coding: utf-8 -*-
"""
This module contains the ServiceFollowup model for managing post-appointment
customer follow-ups.

Classes:
    ServiceFollowup: Main model handling follow-up records with state workflow,
                     customer ratings, and automated reminder scheduling.

Key Methods:
    - action_mark_sent(): Transitions follow-up to 'sent' state
    - action_log_reply(): Records customer response and transitions to 'replied'
    - action_close(): Closes the follow-up
    - cron_followup_reminder(): Scheduled action creating reminder activities
                                for overdue follow-ups
"""

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta


class ServiceFollowup(models.Model):
    _name = 'service.followup'
    _description = 'Service Follow-up'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'appointment_date desc, id desc'

    name = fields.Char(
        string='Subject',
        required=True,
        tracking=True,
    )
    partner_id = fields.Many2one(
        'res.partner',
        string='Customer',
        required=True,
        tracking=True,
    )
    appointment_date = fields.Datetime(
        string='Appointment Date',
        tracking=True,
    )
    assigned_user_id = fields.Many2one(
        'res.users',
        string='Assigned To',
        default=lambda self: self.env.user,
        tracking=True,
    )
    state = fields.Selection(
        [
            ('draft', 'Draft'),
            ('sent', 'Sent'),
            ('replied', 'Replied'),
            ('closed', 'Closed'),
        ],
        string='Status',
        default='draft',
        required=True,
        tracking=True,
    )
    sent_at = fields.Datetime(
        string='Sent At',
        readonly=False,
        tracking=True,
    )
    replied_at = fields.Datetime(
        string='Replied At',
        readonly=False,
        tracking=True,
    )
    rating = fields.Integer(
        string='Rating',
        tracking=True,
        help='Customer rating from 1 to 10',
    )
    feedback = fields.Text(
        string='Feedback',
        tracking=True,
    )
    chatbot_summary = fields.Text(
        string='Chatbot Summary',
        tracking=True,
    )

    @api.constrains('rating')
    def _check_rating_range(self):
        """Ensure rating is between 1 and 10 if set."""
        for record in self:
            if record.rating is not False and (record.rating < 1 or record.rating > 10):
                raise ValidationError(_('Rating must be between 1 and 10.'))

    def action_mark_sent(self):
        """Mark follow-up as sent."""
        for record in self:
            record.write({
                'state': 'sent',
                'sent_at': fields.Datetime.now(),
            })
            record.message_post(
                body=_('Follow-up marked as sent.'),
                message_type='notification',
            )

    def action_log_reply(self):
        """Log customer reply."""
        for record in self:
            record.write({
                'state': 'replied',
                'replied_at': fields.Datetime.now(),
            })
            record.message_post(
                body=_('Customer reply logged.'),
                message_type='notification',
            )

    def action_close(self):
        """Close follow-up."""
        for record in self:
            record.write({
                'state': 'closed',
            })
            record.message_post(
                body=_('Follow-up closed.'),
                message_type='notification',
            )

    @api.model
    def cron_followup_reminder(self):
        """
        Scheduled action to create reminder activities for follow-ups
        that have been sent but not replied to after 2 days.
        """
        now = fields.Datetime.now()
        cutoff_date = now - relativedelta(days=2)

        # Find follow-ups that need reminders
        followups = self.search([
            ('state', '=', 'sent'),
            ('sent_at', '!=', False),
            ('sent_at', '<=', cutoff_date),
            ('replied_at', '=', False),
        ], limit=50)

        # Get TODO activity type
        activity_type = self.env.ref(
            'mail.mail_activity_data_todo', raise_if_not_found=False)
        if not activity_type:
            # Fallback if the XML ID doesn't exist
            activity_type = self.env['mail.activity.type'].search(
                [('name', '=', 'To Do')], limit=1)

        if not activity_type:
            return

        for followup in followups:
            # Check if activity already exists for this follow-up
            existing_activity = self.env['mail.activity'].search([
                ('res_model', '=', 'service.followup'),
                ('res_id', '=', followup.id),
                ('activity_type_id', '=', activity_type.id),
                ('user_id', '=', followup.assigned_user_id.id),
                ('date_deadline', '>=', fields.Date.today()),
            ], limit=1)

            if not existing_activity:
                # Create reminder activity
                self.env['mail.activity'].create({
                    'res_model_id': self.env['ir.model']._get_id('service.followup'),
                    'res_id': followup.id,
                    'activity_type_id': activity_type.id,
                    'summary': _('Follow-up Reminder: %s', followup.name),
                    'note': _(
                        'This follow-up was sent on %s and has not received a reply yet. '
                        'Please check with the customer.',
                        followup.sent_at.strftime('%Y-%m-%d %H:%M')
                    ),
                    'user_id': followup.assigned_user_id.id,
                    'date_deadline': fields.Date.today(),
                })
