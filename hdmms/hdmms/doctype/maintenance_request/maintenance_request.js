// Copyright (c) 2025, HDSD and contributors
// For license information, please see license.txt

// frappe.ui.form.on("Maintenance Request", {
// 	refresh(frm) {

// 	},
// });
frappe.ui.form.on('Maintenance Request', {
    refresh: function(frm) {
        // Add button to create material requisition
        if(!frm.doc.__islocal && frm.doc.status !== "Completed") {
            frm.add_custom_button(__('Create Material Requisition'), function() {
                frappe.call({
                    method: "hdmms.hdmms.doctype.maintenance_request.maintenance_request.create_material_requisition",
                    args: {
                        docname: frm.doc.name
                    },
                    callback: function(r) {
                        if(!r.exc) {
                            frm.refresh_field("material_requisitions");
                        }
                    }
                });
            });
        }
        
        // Open Work Order button
        if(frm.doc.work_order) {
            frm.add_custom_button(__('Open Work Order'), function() {
                frappe.set_route('Form', 'Work Order', frm.doc.work_order);
            });
        }
    },
    
    maintenance_team: function(frm) {
        // Update assigned_to options when team changes
        if(frm.doc.maintenance_team) {
            frappe.call({
                method: "frappe.client.get",
                args: {
                    doctype: "Maintenance Team",
                    name: frm.doc.maintenance_team
                },
                callback: function(r) {
                    if(r.message) {
                        let team_leader = r.message.team_leader;
                        frm.set_value("assigned_to", team_leader);
                        
                        // Update dropdown options
                        let members = r.message.team_members || [];
                        let options = members.map(m => m.employee);
                        options.unshift(team_leader);
                        
                        frm.set_df_property("assigned_to", "options", options);
                    }
                }
            });
        }
    }
});

// Calculate amount for items
frappe.ui.form.on('Maintenance Item', {
    item_code: function(frm, cdt, cdn) {
        let item = frappe.get_doc(cdt, cdn);
        if(item.item_code) {
            frappe.model.set_value(cdt, cdn, 'item_name', 
                frappe.db.get_value("Item", item.item_code, "item_name"));
            frappe.model.set_value(cdt, cdn, 'uom', 
                frappe.db.get_value("Item", item.item_code, "stock_uom"));
        }
    }
});