# -*- coding: utf-8 -*-
# Copyright (c) 2019, 9t9IT and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document


class GratuityClaim(Document):
	def on_submit(self):
		total_gratuity_paid = _get_total_gratuity_paid(self.employee, self.claimed_amount)
		frappe.db.set_value('Employee', self.employee, 'ashbee_gratuity_paid_till_date', total_gratuity_paid)

	def on_cancel(self):
		total_gratuity_paid = _get_total_gratuity_paid(self.employee, -self.claimed_amount)
		frappe.db.set_value('Employee', self.employee, 'ashbee_gratuity_paid_till_date', total_gratuity_paid)


def _get_total_gratuity_paid(employee, claimed_amount):
	gratuity_paid_till_date = frappe.db.get_value('Employee', employee, 'ashbee_gratuity_paid_till_date')
	return gratuity_paid_till_date + claimed_amount
