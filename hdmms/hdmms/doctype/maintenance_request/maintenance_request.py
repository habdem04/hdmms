import frappe
from frappe.model.document import Document
from frappe.utils import nowdate

class MaintenanceRequest(Document):
    def validate(self):
        self.validate_team_assignment()
        self.set_default_dates()
    
    def before_submit(self):
        if self.status == "Draft":
            frappe.throw("Please change status from Draft before submitting")
    
    def on_submit(self):
        self.create_work_order_if_needed()
        self.create_first_material_requisition()
    
    def validate_team_assignment(self):
        if self.maintenance_team and self.assigned_to:
            team_members = frappe.get_all(
                "Team Member",
                filters={"parent": self.maintenance_team},
                fields=["employee"]
            )
            members = [m.employee for m in team_members]
            
            if self.assigned_to not in members:
                frappe.throw(f"Selected employee is not part of {self.maintenance_team}")
    
    def set_default_dates(self):
        if not self.request_date:
            self.request_date = nowdate()
    
    def create_work_order_if_needed(self):
        if self.status == "Open" and not self.work_order:
            wo = frappe.new_doc("Work Order")
            wo.production_item = "MAINTENANCE-SERVICE"
            wo.qty = 1
            wo.maintenance_request = self.name
            wo.asset = self.asset
            wo.company = frappe.defaults.get_user_default("company")
            wo.planned_start_date = self.request_date
            wo.insert()
            
            self.db_set("work_order", wo.name)
            frappe.msgprint(f"Work Order {wo.name} created")
    
    def create_first_material_requisition(self):
        if self.items and not self.material_requisitions:
            self.create_material_requisition()
    
    def create_material_requisition(self):
        """Create new Material Request"""
        if not self.items:
            frappe.throw("Please add items first")
        
        mr = frappe.new_doc("Material Request")
        mr.material_request_type = "Material Transfer"
        mr.maintenance_request = self.name
        mr.company = frappe.defaults.get_user_default("company")
        
        for item in self.items:
            mr.append("items", {
                "item_code": item.item_code,
                "qty": item.quantity,
                "uom": item.uom,
                "warehouse": "Stores - " + mr.company
            })
        
        mr.insert()
        mr.submit()
        
        self.append("material_requisitions", {
            "material_request": mr.name
        })
        
        self.save()
        frappe.msgprint(f"Material Request {mr.name} created")
    
    @frappe.whitelist()
    def get_linked_requisitions(self):
        """Return all linked Material Requests"""
        return frappe.get_all(
            "Material Request",
            filters={"maintenance_request": self.name},
            fields=["name", "status", "transaction_date"]
        )