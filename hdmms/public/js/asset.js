frappe.ui.form.on('Asset', {
    refresh: function(frm) {
        console.log("HDMMS Asset script loaded"); // Debug line
        
        // First button - View History
        frm.add_custom_button(
            __('View Maintenance History'), 
            function() {
                frappe.route_options = {
                    "asset": frm.doc.name,
                    "status": ["!=", "Cancelled"]  // Filter out cancelled requests
                };
                frappe.set_route("List", "Maintenance Request");
            },
            __('Maintenance')  // Group under Maintenance dropdown
        );
        
        // Second button - Create Request
        frm.add_custom_button(
            __('Create Maintenance Request'), 
            function() {
                frappe.new_doc("Maintenance Request", {
                    asset: frm.doc.name,
                    maintenance_type: "Corrective",
                    priority: "Medium"
                });
            },
            __('Maintenance')  // Same group
        );
        
        // Alternative: Add to form menu as fallback
        frm.page.add_menu_item(__('View Maintenance History'), function() {
            frappe.route_options = {"asset": frm.doc.name};
            frappe.set_route("List", "Maintenance Request");
        });
    }
});