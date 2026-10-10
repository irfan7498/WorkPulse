from frappe.model.document import Document


class LeaveImpactAnalysis(Document):
	def autoname(self):
		leave_number = (self.leave_application or "").rsplit("-", 1)[-1]
		self.name = f"LIA-{leave_number}" if leave_number.isdigit() else "LIA-NEW"