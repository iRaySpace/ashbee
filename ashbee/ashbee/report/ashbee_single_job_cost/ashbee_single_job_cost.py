# Copyright (c) 2013, 9t9IT and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe

from ashbee.helpers import new_column


def execute(filters=None):
    columns, data = get_columns(), get_data(filters)

    if data:
        material_total = _get_total_row(data)
        data.append(material_total)

        _fill_blank(data)

        timesheet_details = _get_timesheet_details(filters)
        data.append(timesheet_details)

        grand_total = _get_total_row(
            [material_total, timesheet_details],
            '<b>Grand Total</b>'
        )
        data.append(grand_total)

    return columns, data


def get_columns():
    return [
        new_column("Reference", "reference", "Data", 150),
        new_column("Date", "date", "Date", 95),
        new_column("Description", "description", "Data", 200),
        new_column("Income", "income", "Currency", 90),
        new_column("Qty", "qty", "Int", 90),
        new_column("Rate", "rate", "Currency", 90),
        new_column("Material+Direct", "material_direct", "Currency", 120),
        new_column("Labor Expenses", "labor_expenses", "Currency", 120),
        new_column("Central Labour", "central_labour", "Currency", 120),
        new_column("Central Expenses", "central_expenses", "Currency", 120),
        new_column("Indirect", "indirect", "Currency", 120),
        new_column("Overhead Charges", "overhead_charges", "Currency", 120)
    ]


def get_data(filters):
    data = []
    overhead_percent = filters.get('overhead_percent') / 100.00

    # TODO: know if project_expenses is by date range filters(?)
    project_expenses = _get_project_expenses(filters)
    project_expenses['overhead_charges'] = _fill_overhead_charges(
        project_expenses,
        overhead_percent
    )

    data.append(project_expenses)

    entries = [
        _get_stock_ledger_entries(filters)
    ]

    for entry in entries:
        data.extend(entry)

    return data


def _get_project_expenses(filters):
    return frappe.db.sql("""
        SELECT 
            total_costing_amount AS labor_expenses,
            (total_consumed_material_cost + ashbee_total_direct_cost + total_purchase_cost)
            AS material_direct,
            ashbee_total_central_cost AS central_expenses,
            ashbee_total_central_labor AS central_labour,
            ashbee_total_indirect_cost AS indirect
        FROM `tabProject`
        WHERE name=%(project)s
    """, filters, as_dict=1)[0]


def _get_stock_ledger_entries(filters):
    return frappe.db.sql("""
        SELECT 
            posting_date AS date, 
            voucher_no AS reference, 
            item_code AS description,
            valuation_rate AS rate,
            actual_qty AS qty
        FROM `tabStock Ledger Entry`
        WHERE project=%(project)s 
        AND posting_date BETWEEN %(from_date)s AND %(to_date)s
    """, filters, as_dict=1)


def _get_timesheet_details(filters):
    timesheet_row = {
        'description': 'Timesheet',
        'qty': 0,
        'rate': 0.00
    }

    timesheet_details = frappe.db.sql("""
        SELECT sum(costing_amount) AS rate, count(*) AS qty
        FROM `tabTimesheet Detail`
        INNER JOIN `tabTimesheet`
        ON `tabTimesheet Detail`.parent = `tabTimesheet`.name
        WHERE `tabTimesheet Detail`.project=%(project)s
        AND `tabTimesheet Detail`.docstatus=1
        AND start_date BETWEEN %(from_date)s AND %(to_date)s
    """, filters, as_dict=1)

    if timesheet_details:
        timesheet_detail = timesheet_details[0]
        timesheet_row['qty'] = timesheet_detail.get('qty')
        timesheet_row['rate'] = timesheet_detail.get('rate')

    return timesheet_row


def _get_total_row(data, description='Total'):
    total_qty = 0
    total_rate = 0.00
    for row in data:
        total_qty = total_qty + row.get('qty', 0)
        total_rate = total_rate + row.get('rate', 0.00)
    return {
        'description': description,
        'qty': total_qty,
        'rate': total_rate
    }


def _fill_overhead_charges(project_expenses, overhead_percent):
    material_direct = project_expenses.get('material_direct')
    labor_expenses = project_expenses.get('labor_expenses')
    indirect = project_expenses.get('indirect')

    return (material_direct + labor_expenses + indirect) * overhead_percent


def _fill_blank(data):
    data.append({})
