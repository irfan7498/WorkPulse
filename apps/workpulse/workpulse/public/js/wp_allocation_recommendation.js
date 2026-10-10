frappe.ui.form.on("WP Allocation Recommendation", {
  refresh(frm) {
    if (frm.is_new() || frm.doc.status !== "Suggested" || !frm.perm[0]?.write) return;
    frm.add_custom_button(__("Approve recommendation"), () => {
      let candidates = [];
      try {
        candidates = JSON.parse(frm.doc.candidates || "[]");
      } catch (error) {
        frappe.msgprint(__("Candidate data is invalid and cannot be approved."));
        return;
      }
      if (!candidates.length) {
        frappe.msgprint(__("No eligible candidates were found."));
        return;
      }
      const options = candidates.map((candidate) =>
        `${candidate.employee} (${Number(candidate.score || 0).toFixed(3)})`
      );
      frappe.prompt(
        [{ fieldname: "employee", fieldtype: "Select", label: __("Employee"), options: options.join("\n"), reqd: 1 }],
        (values) => {
          const selected = candidates[Number(values.employee.split(" ")[0]) - 1] || candidates.find((candidate) => values.employee.startsWith(candidate.employee));
          frappe.call({
            method: "workpulse.workpulse.api.allocation.approve",
            args: { recommendation: frm.doc.name, employee: selected.employee },
          }).then(() => frm.reload_doc());
        },
        __("Approve allocation"),
        __("Approve")
      );
    }, __("WorkPulse"));
  },
});
