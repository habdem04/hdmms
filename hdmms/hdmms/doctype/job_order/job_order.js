frappe.ui.form.on('Job Order', {
    refresh: function(frm) {
        // Create Material Requisition button
        if(frm.doc.docstatus === 0 && frm.doc.required_materials && frm.doc.required_materials.length > 0) {
            frm.add_custom_button(__('Create Material Requisition'), function() {
                frappe.call({
                    method: "hdmms.hdmms.api.create_material_requisition",
                    args: {
                        job_order: frm.doc.name
                    },
                    callback: function(r) {
                        if(!r.exc) {
                            frappe.show_alert(__("Material Requisition {0} created", [r.message]));
                            frm.refresh_field("material_requisitions");
                        }
                    }
                });
                
            }, __("Materials"));
        }
        
        // Open linked Maintenance Request
        if(frm.doc.maintenance_request) {
            frm.add_custom_button(__('Open Maintenance Request'), function() {
                frappe.set_route('Form', 'Maintenance Request', frm.doc.maintenance_request);
            }, __("Related"));
        }
        
        // Complete Job Order button
        if(frm.doc.docstatus === 0 && frm.doc.status !== "Completed") {
            frm.add_custom_button(__('Mark as Completed'), function() {
                frappe.prompt({
                    fieldtype: 'Datetime',
                    label: __('Actual Completion Time'),
                    fieldname: 'completion_time',
                    default: frappe.datetime.now_datetime(),
                    reqd: 1
                }, (values) => {
                    frm.set_value("status", "Completed");
                    frm.set_value("expected_end_date", values.completion_time);
                    frm.save();
                }, __('Complete Job'), __('Complete'));
            }, __("Status"));
        }
    },
    
    start_date: function(frm) {
        if(frm.doc.start_date && !frm.doc.status) {
            frm.set_value("status", "Scheduled");
        }
    }
});

// Task duration calculation
frappe.ui.form.on('Job Order Task', {
    start_time: function(frm, cdt, cdn) {
        calculate_task_duration(frm, cdt, cdn);
    },
    end_time: function(frm, cdt, cdn) {
        calculate_task_duration(frm, cdt, cdn);
    }
});

function calculate_task_duration(frm, cdt, cdn) {
    var task = frappe.get_doc(cdt, cdn);
    if(task.start_time && task.end_time) {
        frappe.model.set_value(cdt, cdn, 'duration', 
            frappe.datetime.time_diff_in_hours(task.end_time, task.start_time));
    }
}