frappe.ui.form.on("Task", {
  refresh(frm) {
    if (frm.is_new() || !frm.perm[0]?.write) return;
    frm.add_custom_button(__("Suggest assignee"), () => {
      frappe.call({
        method: "workpulse.workpulse.api.allocation.suggest",
        args: { task: frm.doc.name },
      }).then(({ message }) => {
        if (message?.name) frappe.set_route("Form", "WP Allocation Recommendation", message.name);
      });
    }, __("WorkPulse"));
  },
});
