frappe.ui.form.on('Job Order', {
    refresh: function(frm) {
        // ------------------------------
        // Create Material Requisition button (group: Materials)
        if (frm.doc.docstatus === 0 && frm.doc.required_materials && frm.doc.required_materials.length > 0) {
            frm.add_custom_button(__('Create Material Requisition'), function() {
                frappe.call({
                    method: "hdmms.hdmms.api.create_material_requisition",  // adjust module path if needed
                    args: {
                        job_order: frm.doc.name
                    },
                    callback: function(r) {
                        if (!r.exc) {
                            frappe.show_alert(__("Material Requisition {0} created", [r.message]));
                            frm.refresh_field("material_requisitions");
                        }
                    }
                });
            }, __("Materials"));
        }
        
        // ------------------------------
        // Unlink Maintenance Request button (group: Materials)
        if (frm.doc.maintenance_request) {
            frm.add_custom_button(__('Unlink Maintenance Request'), function() {
                frappe.call({
                    method: "hdmms.hdmms.api.unlink_mr_from_job_order",  // adjust module path if needed
                    args: {
                        job_order_name: frm.doc.name
                    },
                    callback: function(r) {
                        if (r.message) {
                            frappe.msgprint(r.message);
                            frm.reload_doc();
                        }
                    }
                });
            }, __("Materials"));
        }
        
        // ------------------------------
        // Open linked Maintenance Request button (group: Related)
        if (frm.doc.maintenance_request) {
            frm.add_custom_button(__('Open Maintenance Request'), function() {
                frappe.set_route('Form', 'Maintenance Request', frm.doc.maintenance_request);
            }, __("Related"));
        }
        
        // ------------------------------
        // Mark as Completed button (group: Status)
        // When clicked, the prompt asks for the actual completion time.
        // After that, if a Maintenance Request is linked, it calculates KPI actual response time.
        if (frm.doc.docstatus === 0 && frm.doc.status !== "Completed") {
            frm.add_custom_button(__('Mark as Completed'), function() {
                frappe.prompt({
                    fieldtype: 'Datetime',
                    label: __('Actual Completion Time'),
                    fieldname: 'completion_time',
                    default: frappe.datetime.now_datetime(),
                    reqd: 1
                }, (values) => {
                    // Set status as Completed and update expected end date
                    frm.set_value("status", "Completed");
                    frm.set_value("expected_end_date", values.completion_time);
                    
                    // If a Maintenance Request is linked, calculate KPI actual response time.
                    if (frm.doc.maintenance_request) {
                        frappe.call({
                            method: "frappe.client.get_value",
                            args: {
                                doctype: "Maintenance Request",
                                filters: { name: frm.doc.maintenance_request },
                                fieldname: "request_date"
                            },
                            callback: function(r) {
                                if (r.message && r.message.request_date) {
                                    var reqDate = new Date(r.message.request_date);
                                    var compTime = new Date(values.completion_time);
                                    var diffMs = compTime - reqDate;
                                    var diffHrs = diffMs / (1000 * 60 * 60);
                                    // Set the actual_response_time field (rounded to 2 decimals)
                                    frm.set_value("actual_response_time", diffHrs.toFixed(2));
                                } else {
                                    frappe.msgprint(__("Maintenance Request does not have a request_date"));
                                }
                                frm.save();
                            }
                        });
                    } else {
                        frm.save();
                    }
                }, __('Complete Job'), __('Complete'));
            }, __("Status"));
        }
    },
    
    start_date: function(frm) {
        if (frm.doc.start_date && !frm.doc.status) {
            frm.set_value("status", "Scheduled");
        }
    }
});

// ------------------------------
// Task duration calculation on Job Order Task
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
        frappe.model.set_value(cdt, cdn, 'duration', frappe.datetime.time_diff_in_hours(task.end_time, task.start_time));
    }
}