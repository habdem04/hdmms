
def get_permission_query_conditions(user):
    if not user:
        user = frappe.session.user

    if user == "Administrator":
        return ""  # Administrator can see all records
    
    # For non-admin users, filter out Material Transfer stock entries
    return """(`tabStock Entry`.`stock_entry_type` != 'Material Receipt')"""