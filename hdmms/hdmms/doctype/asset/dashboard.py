from frappe import _

def get_data():
    return {
        "fieldname": "asset",
        "transactions": [
            {
                "label": _("Maintenance"),
                "items": ["Maintenance Request"]
            }
        ],
        "heatmap": True,
        "heatmap_message": _("This shows maintenance activity for this asset"),
    }