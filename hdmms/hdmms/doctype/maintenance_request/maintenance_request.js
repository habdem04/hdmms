// Copyright (c) 2025, HDSD and contributors
// For license information, please see license.txt

// frappe.ui.form.on("Maintenance Request", {
// 	refresh(frm) {

// 	},
// });
frappe.ui.form.on('Maintenance Request', {
    refresh: function(frm) {
        // Add button to create Job Order if not already created
        if(frm.doc.docstatus === 1 && !frm.doc.job_order) {
            frm.add_custom_button(__('Create Job Order'), function() {
                frappe.call({
                    method: "hdmms.hdmms.api.create_job_order",
                    args: {
                        maintenance_request: frm.doc.name
                    },
                    callback: function(r) {
                        if(r.message) {
                            frappe.set_route("Form", "Job Order", r.message);
                        }
                    }
                });
            });
        }
        
        // If Job Order exists, add button to open it
        if(frm.doc.job_order) {
            frm.add_custom_button(__('Open Job Order'), function() {
                frappe.set_route("Form", "Job Order", frm.doc.job_order);
            });
        }
    },
    setup: function(frm) {
        // Set default maintenance team when form loads for new records
        if(frm.is_new()) {
            frappe.call({
                method: "hdmms.hdmms.api.get_default_maintenance_team",
                callback: function(r) {
                    if(r.message) {
                        frm.set_value("maintenance_team", r.message);
                    }
                }
            });
        }
    },
    priority: function(frm) {
        // Set default expected dates based on priority
        let days_to_add = 7;
        if(frm.doc.priority === "High") days_to_add = 3;
        if(frm.doc.priority === "Critical") days_to_add = 1;
        
        if(frm.doc.request_date && !frm.doc.expected_start_date) {
            let start_date = frappe.datetime.add_days(frm.doc.request_date, 1);
            frm.set_value("expected_start_date", start_date);
            
            let end_date = frappe.datetime.add_days(start_date, days_to_add);
            frm.set_value("expected_end_date", end_date);
        }
    }
});