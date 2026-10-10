frappe.pages["workforce-explorer"].on_page_load = function (wrapper) {
  const page = frappe.ui.make_app_page({
    parent: wrapper,
    title: __("Workforce Explorer"),
    single_column: true,
  });
  page.main.html(`
    <div class="workpulse-page wp-explorer-page">
      <div class="wp-explorer-toolbar">
        <div>
          <span class="wp-kicker">${__("WORKFORCE EXPLORER")}</span>
          <h2>${__("Portfolio, project, team, and member view")}</h2>
        </div>
        <button class="btn btn-default wp-explorer-refresh">${__("Refresh")}</button>
      </div>
      <div class="wp-explorer-filters">
        <input class="form-control wp-explorer-search" placeholder="${__("Search employees")}">
        <select class="form-control wp-explorer-department"><option value="">${__("All departments")}</option></select>
        <select class="form-control wp-explorer-status">
          <option value="Active">${__("Active employees")}</option>
          <option value="">${__("All employee statuses")}</option>
        </select>
      </div>
      <div class="wp-explorer-layout">
        <section class="wp-explorer-tree-panel">
          <div class="wp-panel-heading"><h3>${__("Workforce tree")}</h3></div>
          <div class="wp-explorer-tree" role="tree" aria-label="${__("Workforce tree")}"><div class="wp-loading">${__("Loading workforce…")}</div></div>
        </section>
        <aside class="wp-explorer-card"><div class="wp-empty">${__("Select an employee to view details.")}</div></aside>
      </div>
    </div>
  `);

  const $main = page.main;
  const $tree = $main.find(".wp-explorer-tree");
  let filters = { employee_status: "Active" };
  let $selected_node = null;

  load_departments();
  load_root();

  function load_departments() {
    frappe.db.get_list("Employee", {
      fields: ["department"],
      filters: { status: "Active", department: ["is", "set"] },
      limit: 500,
    }).then((rows) => {
      [...new Set(rows.map((row) => row.department).filter(Boolean))].sort().forEach((department) => {
        $main.find(".wp-explorer-department").append(
          $("<option>").val(department).text(department)
        );
      });
    });
  }

  function load_root() {
    $tree.html(`<div class="wp-loading">${__("Loading workforce…")}</div>`);
    frappe.call({
      method: "workpulse.workpulse.api.explorer.get_tree",
      args: { node_type: "portfolio", filters },
    }).then(({ message }) => {
      $tree.empty();
      if (!message?.length) {
        $tree.html(`<div class="wp-empty">${__("No visible workforce records.")}</div>`);
        return;
      }
      message.forEach((node) => render_node(node, $tree, 0));
    }).catch(() => {
      $tree.html(`<div class="wp-inline-error">${__("Workforce data could not be loaded.")}</div>`);
    });
  }

  function render_node(node, $target, depth) {
    const tree_attributes = node.has_children
      ? `aria-expanded="false"`
      : `aria-selected="false"`;
    const $item = $(`
      <button class="wp-explorer-node" style="--node-depth:${depth}" type="button" role="treeitem" aria-level="${depth + 1}" ${tree_attributes}>
        <span class="wp-explorer-chevron">${node.has_children ? "▸" : "•"}</span>
        <span class="wp-explorer-node-label"></span>
        <span class="wp-explorer-node-meta"></span>
      </button>
    `);
    $item.find(".wp-explorer-node-label").text(node.label);
    $item.find(".wp-explorer-node-meta").text(node.progress != null ? `${node.progress}%` : node.type);
    $target.append($item);
    if (node.type === "employee") {
      $item.on("click", () => {
        $selected_node?.removeClass("is-selected").attr("aria-selected", "false");
        $selected_node = $item.addClass("is-selected").attr("aria-selected", "true");
        load_card(node.id);
      });
    }
    if (node.has_children) {
      const $children = $('<div class="wp-explorer-children" role="group"></div>').hide();
      $target.append($children);
      $item.on("click", () => {
        const expanded = $children.is(":visible");
        $item.find(".wp-explorer-chevron").text(expanded ? "▸" : "▾");
        $item.attr("aria-expanded", expanded ? "false" : "true");
        if (expanded) return $children.slideUp(100);
        if (!$children.children().length) {
          const nextType = node.type === "portfolio" ? "project" : node.type === "project" ? "team" : "member";
          frappe.call({
            method: "workpulse.workpulse.api.explorer.get_tree",
            args: { parent: node.id, node_type: nextType, filters },
          }).then(({ message }) => (message || []).forEach((child) => render_node(child, $children, depth + 1)));
        }
        $children.slideDown(100);
      });
    }
  }

  function load_card(employee) {
    const $card = $main.find(".wp-explorer-card").html(`<div class="wp-loading">${__("Loading employee details…")}</div>`);
    frappe.call({
      method: "workpulse.workpulse.api.explorer.get_employee_card",
      args: { employee },
    }).then(({ message }) => {
      const row = message.employee;
      const contribution = message.contribution || {};
      $card.html(`
        <div class="wp-card-header">
          <span class="wp-kicker">${__("EMPLOYEE 360")}</span>
          <h2>${escape(row.employee_name || row.name)}</h2>
          <p>${escape(row.designation || __("Role not set"))} · ${escape(row.department || __("Department not set"))}</p>
        </div>
        <div class="wp-card-metrics">
          ${card_metric(__("Logged hours"), contribution.logged_hours)}
          ${card_metric(__("Tasks"), contribution.task_count)}
          ${card_metric(__("Open tasks"), contribution.open_task_count)}
          ${card_metric(__("Timesheet entries"), contribution.timesheet_entries)}
        </div>
        <h3>${__("Workload forecast")}</h3>
        <div class="wp-card-snapshots">${(message.snapshots || []).map(snapshot_row).join("") || `<p class="text-muted">${__("No snapshots available.")}</p>`}</div>
        <h3>${__("Project history")}</h3>
        <div class="wp-card-history">${(message.history || []).map(history_row).join("") || `<p class="text-muted">${__("No project history available.")}</p>`}</div>
      `);
    }).catch(() => $card.html(`<div class="wp-inline-error">${__("Employee details could not be loaded.")}</div>`));
  }

  function snapshot_row(snapshot) {
    const load = Number(snapshot.workload_pct || 0);
    const state = load >= 100 ? "is-high" : load >= 85 ? "is-warn" : "is-ok";
    return `<div class="wp-card-row"><span>${escape(snapshot.week_start)}</span><strong class="${state}">${load.toFixed(1)}%</strong><small>${Number(snapshot.planned_h || 0).toFixed(1)}h / ${Number(snapshot.capacity_h || 0).toFixed(1)}h</small></div>`;
  }

  function history_row(history) {
    return `<div class="wp-card-row"><span>${escape(history.project)}</span><strong>${escape(history.role || __("Contributor"))}</strong><small>${escape(history.tasks_done || 0)} tasks · ${escape(history.on_time_pct || 0)}% on time</small></div>`;
  }

  function card_metric(label, value) {
    return `<div><span>${escape(label)}</span><strong>${escape(value ?? 0)}</strong></div>`;
  }

  function escape(value) {
    return frappe.utils.escape_html(String(value ?? "—"));
  }

  $main.find(".wp-explorer-refresh").on("click", load_root);
  $main.find(".wp-explorer-search").on("input", frappe.utils.debounce(function () {
    filters.search = this.value;
    load_root();
  }, 250));
  $main.find(".wp-explorer-department").on("change", function () {
    filters.department = this.value;
    load_root();
  });
  $main.find(".wp-explorer-status").on("change", function () {
    filters.employee_status = this.value;
    load_root();
  });
};
