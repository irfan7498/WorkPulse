frappe.ui.form.on("Leave Application", {
  refresh(frm) {
    if (frm.is_new() || frm.doc.status !== "Open") return;

    workpulse_render(frm);
    frappe.realtime.off("workpulse_leave_impact_ready");
    frappe.realtime.on("workpulse_leave_impact_ready", (data) => {
      if (data.leave === frm.doc.name) workpulse_render(frm);
    });
  },
});

function workpulse_render(frm) {
  frappe.call({
    method: "workpulse.leave_impact.api.get_analysis",
    args: { leave_application: frm.doc.name },
    callback(response) {
      const analysis = response.message;
      if (!analysis) return;

      const color = { Low: "green", Medium: "orange", High: "red" }[analysis.risk_level];
      const evidence = (() => {
        try {
          return JSON.parse(analysis.evidence || "{}");
        } catch (error) {
          return {};
        }
      })();
      const escape = (value) => frappe.utils.escape_html(String(value ?? ""));
      const chain = (analysis.policy_chain || []).map(escape).join(" → ") || __("Default approver");
      frm.dashboard.clear_headline();
      frm.dashboard.set_headline_alert(
        `<b>WorkPulse:</b> ${escape(analysis.risk_level)} risk (${escape(analysis.risk_score)}/100) &middot; `
          + `Suggested: <b>${escape(analysis.suggested_action)}</b><br>`
          + `${escape(analysis.summary || "")}<br>`
          + `<b>${__("Approval chain")}:</b> ${chain} `
          + `<details><summary>${__("Evidence and mitigations")}</summary>`
          + `<p>${escape(__("Impacted tasks"))}: ${escape(evidence.impacted_tasks?.length || 0)} · `
          + `${escape(__("Teammates away"))}: ${escape(evidence.teammates_on_leave?.length || 0)}</p>`
          + `<div>${escape(analysis.mitigations || "")}</div></details>`,
        color,
      );

      if (frm.perm[0] && frm.perm[0].write) {
        frm.add_custom_button(
          "Re-run Impact Analysis",
          () => {
            frappe
              .call("workpulse.leave_impact.api.rerun", { leave_application: frm.doc.name })
              .then(() => frappe.show_alert("Analysis queued"));
          },
          "WorkPulse",
        );
      }
    },
  });
}