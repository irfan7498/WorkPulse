frappe.ui.form.on("Leave Impact Analysis", {
  refresh(frm) {
    if (!frm.doc.leave_application) return;
    frappe.call({
      method: "workpulse.leave_impact.api.get_analysis",
      args: { leave_application: frm.doc.leave_application },
    }).then(({ message }) => {
      const chain = message?.policy_chain || [];
      if (chain.length) {
        frm.dashboard.set_headline_alert(
          `<b>${__("Approval chain")}:</b> ${frappe.utils.escape_html(chain.join(" → "))}`,
          "blue",
        );
      }
    });
    frm.add_custom_button(
      __("Open Leave Application"),
      () => frappe.set_route("Form", "Leave Application", frm.doc.leave_application),
      __("WorkPulse"),
    );
  },
});
