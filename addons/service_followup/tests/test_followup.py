# -*- coding: utf-8 -*-
"""
Test suite for the Service Follow-up module.

Test Cases:
    TestServiceFollowup: Contains all unit tests for the followup model
        - test_01_state_flow: Validates state transitions (draft→sent→replied→closed)
        - test_02_rating_constraint: Tests rating validation (must be 1-10)
        - test_03_cron_reminder: Tests automated reminder activity creation
"""

from odoo.tests import TransactionCase, tagged
from odoo.exceptions import ValidationError
from odoo import fields
from dateutil.relativedelta import relativedelta


@tagged('post_install', '-at_install')
class TestServiceFollowup(TransactionCase):

    def setUp(self):
        super(TestServiceFollowup, self).setUp()

        # Create test partner
        self.partner = self.env['res.partner'].create({
            'name': 'Test Customer',
            'email': 'test@example.com',
        })

        # Create test user
        self.user = self.env['res.users'].create({
            'name': 'Test User',
            'login': 'testuser',
            'email': 'testuser@example.com',
        })

    def test_01_state_flow(self):
        """Test state transitions from draft -> sent -> replied -> closed."""

        # Create follow-up in draft state
        followup = self.env['service.followup'].create({
            'name': 'Test Follow-up',
            'partner_id': self.partner.id,
            'assigned_user_id': self.user.id,
            'appointment_date': fields.Datetime.now(),
        })

        self.assertEqual(followup.state, 'draft',
                         'Initial state should be draft')
        self.assertFalse(followup.sent_at, 'sent_at should be empty initially')

        # Mark as sent
        followup.action_mark_sent()
        self.assertEqual(followup.state, 'sent',
                         'State should be sent after action_mark_sent')
        self.assertTrue(followup.sent_at,
                        'sent_at should be set after marking as sent')

        # Log reply
        followup.action_log_reply()
        self.assertEqual(followup.state, 'replied',
                         'State should be replied after action_log_reply')
        self.assertTrue(followup.replied_at,
                        'replied_at should be set after logging reply')

        # Close
        followup.action_close()
        self.assertEqual(followup.state, 'closed',
                         'State should be closed after action_close')

    def test_02_rating_constraint(self):
        """Test that rating constraint raises ValidationError for invalid ratings."""

        followup = self.env['service.followup'].create({
            'name': 'Test Follow-up with Rating',
            'partner_id': self.partner.id,
            'assigned_user_id': self.user.id,
        })

        # Valid rating should work
        followup.write({'rating': 5})
        self.assertEqual(followup.rating, 5, 'Valid rating should be accepted')

        followup.write({'rating': 1})
        self.assertEqual(followup.rating, 1, 'Rating 1 should be valid')

        followup.write({'rating': 10})
        self.assertEqual(followup.rating, 10, 'Rating 10 should be valid')

        # Invalid rating should raise ValidationError
        with self.assertRaises(ValidationError, msg='Rating above 10 should raise ValidationError'):
            followup.write({'rating': 11})

        with self.assertRaises(ValidationError, msg='Rating below 1 should raise ValidationError'):
            followup.write({'rating': 0})

    def test_03_cron_reminder(self):
        """Test that cron creates activities for overdue follow-ups."""

        # Create follow-up marked as sent 3 days ago (overdue for reminder)
        sent_at_date = fields.Datetime.now() - relativedelta(days=3)
        followup_overdue = self.env['service.followup'].create({
            'name': 'Overdue Follow-up',
            'partner_id': self.partner.id,
            'assigned_user_id': self.user.id,
            'state': 'sent',
            'sent_at': sent_at_date,
        })

        # Create follow-up marked as sent 1 day ago (not yet due for reminder)
        followup_recent = self.env['service.followup'].create({
            'name': 'Recent Follow-up',
            'partner_id': self.partner.id,
            'assigned_user_id': self.user.id,
            'state': 'sent',
            'sent_at': fields.Datetime.now() - relativedelta(days=1),
        })

        # Create follow-up that already has a reply (should not get reminder)
        followup_replied = self.env['service.followup'].create({
            'name': 'Replied Follow-up',
            'partner_id': self.partner.id,
            'assigned_user_id': self.user.id,
            'state': 'replied',
            'sent_at': sent_at_date,
            'replied_at': fields.Datetime.now(),
        })

        # Count activities before cron
        activities_before = self.env['mail.activity'].search_count([
            ('res_model', '=', 'service.followup'),
            ('res_id', 'in', [followup_overdue.id,
             followup_recent.id, followup_replied.id]),
        ])

        # Run cron
        self.env['service.followup'].cron_followup_reminder()

        # Count activities after cron
        activities_after = self.env['mail.activity'].search_count([
            ('res_model', '=', 'service.followup'),
            ('res_id', 'in', [followup_overdue.id,
             followup_recent.id, followup_replied.id]),
        ])

        # Should have created exactly 1 activity (for overdue follow-up only)
        self.assertEqual(
            activities_after - activities_before,
            1,
            'Cron should create exactly 1 activity for the overdue follow-up'
        )

        # Verify activity is for the overdue follow-up
        activity = self.env['mail.activity'].search([
            ('res_model', '=', 'service.followup'),
            ('res_id', '=', followup_overdue.id),
        ])
        self.assertTrue(
            activity, 'Activity should exist for overdue follow-up')
        self.assertEqual(activity.user_id, self.user,
                         'Activity should be assigned to the correct user')

        # Run cron again - should not create duplicate activity
        self.env['service.followup'].cron_followup_reminder()
        activities_after_second_run = self.env['mail.activity'].search_count([
            ('res_model', '=', 'service.followup'),
            ('res_id', '=', followup_overdue.id),
        ])
        self.assertEqual(
            activities_after_second_run,
            1,
            'Cron should not create duplicate activities'
        )
