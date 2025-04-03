import frappe
from frappe import _
from frappe.utils import nowdate, add_days, now_datetime

def calculate_expected_end_date(priority):
    """Calculate expected end date based on priority."""
    sla_days = {
        "Low": 14,
        "Medium": 7,
        "High": 3,
        "Critical": 1
    }.get(priority, 7)
    return add_days(now_datetime(), sla_days)

def get_default_maintenance_item():
    """Returns default maintenance item code."""
    default_item = "MAINTENANCE_SERVICE"
    if not frappe.db.exists("Item", default_item):
        item = frappe.new_doc("Item")
        item.update({
            "item_code": default_item,
            "item_name": "Maintenance Service",
            "item_group": "Services",
            "stock_uom": "Hour",
            "is_stock_item": 0
        })
        item.insert(ignore_permissions=True)
    return default_item

@frappe.whitelist()
def get_default_maintenance_team():
    """Returns default maintenance team.
    If the team doesn't exist, it creates one and populates it with up to 3 active Maintenance employees.
    """
    default_team = "Factory Maintenance Team"
    if not frappe.db.exists("Asset Maintenance Team", default_team):
        try:
            team = frappe.new_doc("Asset Maintenance Team")
            team.maintenance_team_name = default_team
            team.company = frappe.defaults.get_user_default("company")
            
            employees = frappe.get_all("Employee",
                filters={"department": "Maintenance", "status": "Active"},
                fields=["name as team_member", "employee_name as full_name"],
                limit=3
            )
            
            for emp in employees:
                # Append each employee as a team member
                team.append("maintenance_team_members", {
                    "team_member": emp.team_member,
                    "full_name": emp.full_name,
                    "maintenance_role": "Technician"
                })
            
            team.insert(ignore_permissions=True)
            frappe.db.commit()
        except Exception:
            frappe.log_error("Failed to create default maintenance team")
    return default_team

@frappe.whitelist()
def get_default_technician(team_name):
    """
    Returns the first available technician's Employee record from the maintenance team.
    The child table "maintenance_team_members" stores "team_member" which is a User.
    We then look up the corresponding Employee using the user_id.
    """
    if not frappe.db.exists("Asset Maintenance Team", team_name):
        return None
        
    team = frappe.get_doc("Asset Maintenance Team", team_name)
    if team.get("maintenance_team_members"):
        default_user = team.maintenance_team_members[0].team_member
        employee = frappe.db.get_value("Employee", {"user_id": default_user}, "name")
        return employee if employee else None
    return None

def validate_technician(technician_email):
    """
    Validates if the technician exists by checking if a User exists and then
    retrieves the corresponding Employee record (via the user_id field).
    If no Employee record is found, logs an error and returns an empty string.
    """
    if not technician_email:
        return ""
    
    if frappe.db.exists("User", technician_email):
        employee = frappe.db.get_value("Employee", {"user_id": technician_email}, "name")
        if employee:
            return employee
        else:
            frappe.log_error("User found but no Employee record linked for technician: {0}".format(technician_email))
            return ""
    return ""

@frappe.whitelist()
def create_job_order(maintenance_request):
    """Creates a Job Order with technician validation and fallback mechanism."""
    try:
        mr = frappe.get_doc("Maintenance Request", maintenance_request)
        
        if not mr.asset:
            frappe.throw(_("Asset is required before creating Job Order"))
        
        # Use the maintenance team specified in the request or get the default one.
        maintenance_team = mr.maintenance_team or get_default_maintenance_team()
        
        # Validate the technician; if invalid, fall back to the default technician.
        assigned_to = validate_technician(mr.assigned_to)
        if not assigned_to:
            assigned_to = get_default_technician(maintenance_team)
            if not assigned_to:
                frappe.log_error(
                    "No valid technician assigned",
                    "Maintenance Request: {0}".format(mr.name)
                )
        
        # Create the Job Order with the validated or fallback technician.
        job_order = frappe.new_doc("Job Order")
        job_order.update({
            "maintenance_request": mr.name,
            "asset": mr.asset,
            "maintenance_team": maintenance_team,
            "assigned_to": assigned_to,  # Valid Employee record.
            "priority": mr.priority or "Medium",
            "description": mr.description or "Maintenance work required",
            "status": "Draft",
            "start_date": add_days(now_datetime(), 1),
            "expected_end_date": calculate_expected_end_date(mr.priority or "Medium"),
            "requested_from_cost_center": mr.get("requested_from_cost_center")
        })

        # Append default required material if not provided in the Maintenance Request.
        if not mr.get("required_materials"):
            job_order.append("required_materials", {
                "item_code": get_default_maintenance_item(),
                "quantity": 1,
                "uom": "Hour",
                "required_date": nowdate()
            })
        
        job_order.insert(ignore_permissions=True)
        
        frappe.db.set_value("Maintenance Request", mr.name, {
            "job_order": job_order.name,
            "status": "Assigned"
        })
        
        return job_order.name
        
    except Exception as e:
        error_message = "Failed to create Job Order for {0}".format(maintenance_request)
        frappe.log_error(
            title=error_message[:140],
            message=frappe.get_traceback()
        )
        frappe.throw(_(error_message))

@frappe.whitelist()
def create_material_requisition(job_order):
    """Creates a Material Requisition for the given Job Order."""
    job_order_doc = frappe.get_doc("Job Order", job_order)
    if not job_order_doc.get("required_materials"):
        frappe.throw(_("No materials required for this job"))
    
    mr = frappe.new_doc("Material Request")
    mr.update({
        "material_request_type": "Material Transfer",
        "job_order": job_order_doc.name,
        "schedule_date": add_days(now_datetime(), 1)
    })
    
    for item in job_order_doc.required_materials:
        mr.append("items", {
            "item_code": item.item_code,
            "qty": item.quantity,
            "uom": item.uom,
            "warehouse": item.warehouse or "Stores - " + frappe.defaults.get_user_default("company"),
            "rate": item.rate if hasattr(item, "rate") else 0
        })
    
    mr.insert(ignore_permissions=True)
    mr.submit()
    
    job_order_doc.append("material_requisitions", {
        "material_request": mr.name,
        "status": mr.status,
        "date": now_datetime()
    })
    
    job_order_doc.save()
    return mr.name
