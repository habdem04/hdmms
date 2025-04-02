from frappe.model.document import Document
from frappe.query_builder import Field

class CustomStockEntry(Document):
    @staticmethod
    def get_list_query(query):
        if frappe.session.user == "Administrator":
            query = query.where(Field("stock_entry_type") != "Material Transfer")
        return query