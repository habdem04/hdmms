from frappe import _

def get_data():
    return {
        "fieldname": "job_order",
        "transactions": [
            {
                "label": _("Reference"),
                "items": ["Maintenance Request", "Material Request"]
            },
            {
                "label": _("Activity"),
                "items": ["Timesheet", "Stock Entry"]
            }
        ],
        "heatmap": True,
        "heatmap_message": _("Job Order Activity"),
    }