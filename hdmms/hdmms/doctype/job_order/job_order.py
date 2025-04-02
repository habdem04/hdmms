import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime, time_diff_in_hours

class JobOrder(Document):
    def validate(self):
        self.validate_dates()
        self.calculate_material_amounts()
        self.update_task_durations()
    
    def before_submit(self):
        if self.status != "Completed":
            frappe.throw("Only Completed Job Orders can be submitted")
        
        if not self.material_requisitions:
            frappe.msgprint("No material requisitions created for this job", alert=True)
    
    def validate_dates(self):
        if self.expected_end_date and self.start_date:
            if self.expected_end_date < self.start_date:
                frappe.throw("Expected End Date cannot be before Start Date")
    
    def calculate_material_amounts(self):
        for item in self.required_materials:
            if item.quantity and item.rate:
                item.amount = flt(item.quantity) * flt(item.rate)
    
    def update_task_durations(self):
        for task in self.tasks:
            if task.start_time and task.end_time:
                task.duration = time_diff_in_hours(task.end_time, task.start_time)
    
    @frappe.whitelist()
    def create_material_requisition(self):
        if not self.required_materials:
            frappe.throw("No materials required for this job")
            
        mr = frappe.new_doc("Material Request")
        mr.update({
            "material_request_type": "Material Transfer",
            "job_order": self.name,
            "schedule_date": frappe.utils.add_days(now_datetime(), 1)
        })
        
        for item in self.required_materials:
            mr.append("items", {
                "item_code": item.item_code,
                "qty": item.quantity,
                "uom": item.uom,
                "warehouse": item.warehouse or "Stores - " + frappe.defaults.get_user_default("company"),
                "rate": item.rate
            })
        
        mr.insert()
        mr.submit()
        
        self.append("material_requisitions", {
            "material_request": mr.name,
            "status": mr.status,
            "date": now_datetime()
        })
        
        self.save()
        return mr.name