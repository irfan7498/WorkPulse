frappe.pages['workpulse'].on_page_load = function (wrapper) {
    var page = frappe.ui.make_app_page({
        parent: wrapper,
        title: __('WorkPulse'),
        single_column: true,
    });

    const views = {
        overview: { label: __('Overview') },
        workforce: {
            label: __('People'),
            title: __('Workforce'),
            doctype: 'Employee',
            fields: ['name', 'employee_name', 'department', 'designation', 'status'],
            columns: [
                { label: __('ID'), field: 'name' },
                { label: __('Employee'), field: 'employee_name' },
                { label: __('Department'), field: 'department' },
                { label: __('Role'), field: 'designation' },
                { label: __('Status'), field: 'status' },
            ],
        },
        workload: {
            label: __('Workload'),
            title: __('Workload snapshots'),
            doctype: 'WP Workload Snapshot',
            fields: ['employee', 'week_start', 'capacity_h', 'planned_h', 'workload_pct', 'flags'],
            columns: [
                { label: __('Employee'), field: 'employee' },
                { label: __('Week'), field: 'week_start' },
                { label: __('Capacity'), field: 'capacity_h' },
                { label: __('Planned'), field: 'planned_h' },
                { label: __('Load'), field: 'workload_pct' },
                { label: __('Flags'), field: 'flags' },
            ],
            order_by: 'week_start desc',
        },
        allocation: {
            label: __('Allocation'),
            title: __('Active tasks'),
            doctype: 'Task',
            fields: ['name', 'subject', 'project', 'priority', 'status', 'expected_time'],
            filters: { status: ['not in', ['Completed', 'Cancelled']] },
            columns: [
                { label: __('Task'), field: 'subject' },
                { label: __('Project'), field: 'project' },
                { label: __('Priority'), field: 'priority' },
                { label: __('Status'), field: 'status' },
                { label: __('Estimate'), field: 'expected_time' },
            ],
            order_by: 'modified desc',
        },
        leave: {
            label: __('Leave'),
            title: __('Leave impact'),
            doctype: 'Leave Impact Analysis',
            fields: ['name', 'leave_application', 'employee_name', 'risk_level', 'risk_score', 'status'],
            columns: [
                { label: __('Leave Application'), field: 'leave_application' },
                { label: __('Employee'), field: 'employee_name' },
                { label: __('Risk'), field: 'risk_level' },
                { label: __('Score'), field: 'risk_score' },
                { label: __('Status'), field: 'status' },
            ],
            order_by: 'modified desc',
        },
        projects: {
            label: __('Projects'),
            title: __('Project portfolio'),
            doctype: 'Project',
            fields: ['name', 'project_name', 'status', 'percent_complete', 'expected_end_date'],
            columns: [
                { label: __('Project'), field: 'project_name' },
                { label: __('Status'), field: 'status' },
                { label: __('Progress'), field: 'percent_complete' },
                { label: __('Expected End'), field: 'expected_end_date' },
            ],
            order_by: 'modified desc',
        },
        talent: {
            label: __('Recruitment'),
            title: __('Candidates'),
            doctype: 'Job Applicant',
            fields: ['name', 'applicant_name', 'email_id', 'status', 'modified'],
            columns: [
                { label: __('Applicant'), field: 'applicant_name' },
                { label: __('Email'), field: 'email_id' },
                { label: __('Status'), field: 'status' },
                { label: __('Updated'), field: 'modified' },
            ],
            order_by: 'modified desc',
        },
        intelligence: { label: __('AI & Models') },
    };
    const $body = $(page.body);
    let activeView = 'overview';

    page.set_title(__('WorkPulse'));
    $body.html(`
        <div class="workpulse-page">
        <main class="wp-shell">
            <header class="wp-masthead">
                <div>
                    <div class="wp-eyebrow">WORKPULSE <span>/</span> OPERATIONS</div>
                    <h1>Workforce &amp; delivery</h1>
                    <p>One view of capacity, delivery, and people decisions.</p>
                </div>
                <div class="wp-masthead-mark" aria-hidden="true">WP</div>
            </header>
            <nav class="wp-nav" role="tablist" aria-label="WorkPulse sections">
                ${Object.entries(views).map(([key, view]) => `
                    <button type="button" class="wp-nav-item" data-view="${key}" role="tab">${view.label}</button>
                `).join('')}
            </nav>
            <section class="wp-content" aria-live="polite"></section>
        </main>
        </div>
    `);

    const $content = $body.find('.wp-content');
    const escape = (value) => frappe.utils.escape_html(String(value ?? '—'));
    const countLabel = (value) => value == null ? '—' : Number(value).toLocaleString();

    function setActiveView(viewName) {
        activeView = viewName;
        $body.find('.wp-nav-item').each(function () {
            const selected = this.dataset.view === viewName;
            $(this).toggleClass('is-active', selected).attr('aria-selected', selected);
        });

        if (viewName === 'overview') return renderOverview();
        if (viewName === 'intelligence') return renderIntelligence();
        if (viewName === 'projects') return renderProjects();
        if (viewName === 'talent') return renderTalent();
        return renderList(views[viewName]);
    }

    function renderOverview() {
        $content.html(`
            <div class="wp-section-heading">
                <div><span class="wp-kicker">LIVE WORKSPACE</span><h2>Operating picture</h2></div>
                <button type="button" class="wp-text-button" data-action="refresh">${__('Refresh')}</button>
            </div>
            <div class="wp-metrics" data-metrics>
                <div class="wp-loading">${__('Loading current records…')}</div>
            </div>
            <div class="wp-overview-grid">
                <section class="wp-panel wp-queue-panel">
                    <div class="wp-panel-heading"><div><span class="wp-kicker">NEXT ACTIONS</span><h2>Review queues</h2></div></div>
                    <button type="button" class="wp-queue-row" data-view="allocation"><span class="wp-queue-index">01</span><span><strong>${__('Active task queue')}</strong><small>${__('Review current tasks and estimates')}</small></span><span class="wp-arrow">↗</span></button>
                    <button type="button" class="wp-queue-row" data-route="/desk/query-report/WorkPulse Data Health"><span class="wp-queue-index">02</span><span><strong>${__('Data health')}</strong><small>${__('Inspect incomplete task records')}</small></span><span class="wp-arrow">↗</span></button>
                    <button type="button" class="wp-queue-row" data-view="leave"><span class="wp-queue-index">03</span><span><strong>${__('Leave impact')}</strong><small>${__('Review analyses and affected requests')}</small></span><span class="wp-arrow">↗</span></button>
                </section>
                <section class="wp-panel wp-capabilities">
                    <div class="wp-panel-heading"><div><span class="wp-kicker">WORKPULSE MODULES</span><h2>Intelligence areas</h2></div></div>
                    <button type="button" class="wp-capability-row" data-view="workload"><span class="wp-status-dot is-pending"></span><span><strong>${__('Capacity & workload')}</strong><small>${__('No snapshots computed yet')}</small></span><span class="wp-arrow">↗</span></button>
                    <button type="button" class="wp-capability-row" data-view="allocation"><span class="wp-status-dot is-pending"></span><span><strong>${__('Smart allocation')}</strong><small>${__('Ranking engine; recommendations next')}</small></span><span class="wp-arrow">↗</span></button>
                    <button type="button" class="wp-capability-row" data-view="projects"><span class="wp-status-dot is-pending"></span><span><strong>${__('Project intelligence')}</strong><small>${__('Risk engine; project snapshots next')}</small></span><span class="wp-arrow">↗</span></button>
                    <button type="button" class="wp-capability-row" data-view="talent"><span class="wp-status-dot is-pending"></span><span><strong>${__('Recruitment')}</strong><small>${__('Scoring engine; shortlist next')}</small></span><span class="wp-arrow">↗</span></button>
                    <button type="button" class="wp-capability-row" data-view="intelligence"><span class="wp-status-dot is-pending"></span><span><strong>${__('AI & models')}</strong><small>${__('Feature controls')}</small></span><span class="wp-arrow">↗</span></button>
                </section>
            </div>
        `);

        frappe.call({ method: 'workpulse.workpulse.page.workpulse.workpulse.get_dashboard_data' })
            .then((response) => {
                const metrics = response.message?.metrics || [];
                $content.find('[data-metrics]').html(metrics.map((metric, index) => `
                    <div class="wp-metric" style="--metric-index:${index}">
                        <span>${escape(metric.label)}</span>
                        <strong>${countLabel(metric.value)}</strong>
                    </div>
                `).join(''));
                const snapshotCount = metrics.find((metric) => metric.key === 'snapshots')?.value || 0;
                const $workload = $content.find('.wp-capability-row[data-view="workload"]');
                $workload.find('.wp-status-dot').toggleClass('is-pending', !snapshotCount);
                $workload.find('small').text(snapshotCount
                    ? __('Live snapshots available: {0}', [countLabel(snapshotCount)])
                    : __('No snapshots computed yet'));
                const health = response.message?.project_health;
                const $projects = $content.find('.wp-capability-row[data-view="projects"]');
                $projects.find('.wp-status-dot').toggleClass('is-pending', !health?.total);
                $projects.find('small').text(health?.total
                    ? __('{0} projects tracked · {1} high risk', [countLabel(health.total), countLabel(health.high)])
                    : __('No project snapshots computed yet'));
            })
            .catch(() => {
                $content.find('[data-metrics]').html(`<div class="wp-inline-error">${__('Could not load the live overview. Refresh to try again.')}</div>`);
            });
    }

    function renderProjects() {
        $content.html(`
            <div class="wp-section-heading">
                <div><span class="wp-kicker">PROJECT INTELLIGENCE</span><h2>${__('Portfolio health')}</h2></div>
                <button type="button" class="wp-text-button" data-action="refresh">${__('Refresh')}</button>
            </div>
            <div class="wp-table-wrap"><div class="wp-loading">${__('Loading project snapshots…')}</div></div>
        `);
        frappe.call({
            method: 'workpulse.workpulse.api.project.list_snapshots',
            args: { limit: 50 },
        }).then((response) => {
            const rows = response.message || [];
            const $table = $content.find('.wp-table-wrap');
            if (!rows.length) {
                $table.html(`<div class="wp-empty"><span class="wp-empty-mark">—</span><h3>${__('No project snapshots')}</h3><p>${__('Run the daily snapshot job to populate project health.')}</p></div>`);
                return;
            }

            $table.html(`
                <table class="wp-table">
                    <thead><tr><th>${__('Project')}</th><th>${__('Risk')}</th><th>${__('Progress')}</th><th>${__('Planned')}</th><th>${__('SPI')}</th><th>${__('Delay')}</th></tr></thead>
                    <tbody>${rows.map((row) => `
                        <tr data-name="${escape(row.project)}">
                            <td><button type="button" class="wp-record-link">${escape(row.project)}</button></td>
                            <td>${escape(row.risk_level)} (${escape(row.risk_score)})</td>
                            <td>${escape(Number(row.weighted_progress || 0).toFixed(1))}%</td>
                            <td>${escape(Number(row.planned_progress || 0).toFixed(1))}%</td>
                            <td>${escape(Number(row.spi || 0).toFixed(2))}</td>
                            <td>${escape(Number(row.delay_probability || 0).toFixed(1))}%</td>
                        </tr>
                    `).join('')}</tbody>
                </table>
                <div class="wp-table-foot">${__('Showing')} ${rows.length} ${__('snapshots')}</div>
            `);
            $table.find('.wp-record-link').on('click', function () {
                frappe.set_route('Form', 'Project', $(this).closest('tr').attr('data-name'));
            });
        }).catch(() => {
            $content.find('.wp-table-wrap').html(`<div class="wp-inline-error">${__('Project snapshots could not be loaded. Check your permissions and retry.')}</div>`);
        });
    }

    function renderTalent() {
        $content.html(`
            <div class="wp-section-heading">
                <div><span class="wp-kicker">RECRUITMENT INTELLIGENCE</span><h2>${__('Candidate review queue')}</h2></div>
                <div class="wp-section-actions">
                    <button type="button" class="btn btn-default wp-score-applicants">${__('Score new applicants')}</button>
                    <button type="button" class="wp-text-button" data-action="refresh">${__('Refresh')}</button>
                </div>
            </div>
            <div class="wp-table-wrap"><div class="wp-loading">${__('Loading candidate scores…')}</div></div>
        `);
        $content.find('.wp-score-applicants').on('click', score_new_applicants);
        frappe.call({
            method: 'workpulse.workpulse.api.recruitment.list_review_queue',
            args: { limit: 50 },
        }).then((response) => {
            const rows = response.message || [];
            const $table = $content.find('.wp-table-wrap');
            if (!rows.length) {
                $table.html(`<div class="wp-empty"><span class="wp-empty-mark">—</span><h3>${__('No scored candidates')}</h3><p>${__('Score a Job Applicant to populate this review queue.')}</p></div>`);
                return;
            }
            $table.html(`
                <table class="wp-table">
                    <thead><tr><th>${__('Applicant')}</th><th>${__('Score')}</th><th>${__('Status')}</th><th>${__('Explanation')}</th><th>${__('Review')}</th></tr></thead>
                    <tbody>${rows.map((row) => `
                        <tr data-name="${escape(row.name)}">
                            <td><button type="button" class="wp-record-link">${escape(row.job_applicant)}</button></td>
                            <td>${escape((Number(row.total || 0) * 100).toFixed(1))}%</td>
                            <td>${escape(row.status)}</td>
                            <td>${escape(row.explanation)}</td>
                            <td>
                                <button type="button" class="btn btn-xs btn-success wp-review-action" data-status="Shortlisted">${__('Shortlist')}</button>
                                <button type="button" class="btn btn-xs btn-danger wp-review-action" data-status="Rejected">${__('Reject')}</button>
                            </td>
                        </tr>
                    `).join('')}</tbody>
                </table>
                <div class="wp-table-foot">${__('Showing')} ${rows.length} ${__('candidates')}</div>
            `);
            $table.find('.wp-record-link').on('click', function () {
                frappe.set_route('Form', 'WP Candidate Score', $(this).closest('tr').attr('data-name'));
            });
            $table.find('.wp-review-action').on('click', function () {
                const $button = $(this);
                const original_label = $button.text();
                $button.prop('disabled', true).text(__('Saving…'));
                frappe.call({
                    method: 'workpulse.workpulse.api.recruitment.update_review',
                    args: {
                        score_name: $button.closest('tr').attr('data-name'),
                        status: $button.data('status'),
                    },
                }).then(() => {
                    frappe.show_alert({ message: __('Candidate marked as {0}.', [$button.data('status')]), indicator: 'green' });
                    renderTalent();
                }).catch(() => {
                    $button.prop('disabled', false).text(original_label);
                    frappe.msgprint(__('The candidate review could not be saved. Check your permissions and try again.'));
                });
            });
        }).catch(() => {
            $content.find('.wp-table-wrap').html(`<div class="wp-inline-error">${__('Candidate scores could not be loaded. Check your permissions and retry.')}</div>`);
        });
    }

    function score_new_applicants() {
        const $button = $content.find('.wp-score-applicants');
        $button.prop('disabled', true).text(__('Scoring…'));
        frappe.db.get_list('Job Applicant', {
            fields: ['name'],
            order_by: 'modified desc',
            limit: 100,
        }).then((applicants) => {
            if (!applicants.length) {
                frappe.show_alert({ message: __('No job applicants are available to score.'), indicator: 'orange' });
                return [];
            }
            return Promise.all(applicants.map((applicant) => frappe.call({
                method: 'workpulse.workpulse.api.recruitment.score_applicant',
                args: { job_applicant: applicant.name },
            })));
        }).then((results) => {
            if (results?.length) {
                frappe.show_alert({ message: __('Scored {0} applicants.', [results.length]), indicator: 'green' });
            }
            renderTalent();
        }).catch(() => {
            $button.prop('disabled', false).text(__('Score new applicants'));
            frappe.msgprint(__('Applicants could not be scored. Check your permissions and retry.'));
        });
    }

    function renderList(view) {
        $content.html(`
            <div class="wp-section-heading">
                <div><span class="wp-kicker">${escape(view.doctype.toUpperCase())}</span><h2>${escape(view.title)}</h2></div>
                <button type="button" class="wp-text-button" data-list-doctype="${escape(view.doctype)}">${__('Open list')} ↗</button>
            </div>
            <div class="wp-table-wrap"><div class="wp-loading">${__('Loading records…')}</div></div>
        `);

        frappe.db.get_list(view.doctype, {
            fields: view.fields,
            filters: view.filters || {},
            order_by: view.order_by || 'modified desc',
            limit: 25,
        }).then((rows) => {
            const $table = $content.find('.wp-table-wrap');
            if (!rows.length) {
                $table.html(`<div class="wp-empty"><span class="wp-empty-mark">—</span><h3>${__('No records to show')}</h3><p>${__('Records will appear here when available to your account.')}</p></div>`);
                return;
            }

            $table.html(`
                <table class="wp-table">
                    <thead><tr>${view.columns.map((column) => `<th>${escape(column.label)}</th>`).join('')}</tr></thead>
                    <tbody>${rows.map((row) => {
                        return `<tr data-name="${escape(row.name)}"><td><button type="button" class="wp-record-link">${escape(row[view.columns[0].field] || row.name)}</button></td>${view.columns.slice(1).map((column) => `<td>${escape(row[column.field])}</td>`).join('')}</tr>`;
                    }).join('')}</tbody>
                </table>
                <div class="wp-table-foot">${__('Showing')} ${rows.length} ${__('records')}</div>
            `);
            $table.find('.wp-record-link').on('click', function () {
                const name = $(this).closest('tr').attr('data-name');
                frappe.set_route('Form', view.doctype, name);
            });
        }).catch(() => {
            $content.find('.wp-table-wrap').html(`<div class="wp-inline-error">${__('Records could not be loaded. Check your permissions and retry.')}</div>`);
        });
    }

    function renderIntelligence() {
        $content.html(`
            <div class="wp-section-heading">
                <div><span class="wp-kicker">CONFIGURATION</span><h2>${__('AI & model controls')}</h2></div>
                <button type="button" class="wp-text-button" data-route="/desk/workpulse-settings/WorkPulse Settings">${__('Open settings')} ↗</button>
            </div>
            <div class="wp-settings-list"><div class="wp-loading">${__('Loading controls…')}</div></div>
            <div class="wp-models">
                <div class="wp-panel-heading"><div><span class="wp-kicker">MODEL REGISTRY</span><h3>${__('Versioned models')}</h3></div></div>
                <div class="wp-table-wrap"><div class="wp-loading">${__('Loading model versions…')}</div></div>
            </div>
            <div class="wp-assistant">
                <h3>${__('Guarded assistant')}</h3>
                <p>${__('Read-only answers use only data available to your WorkPulse role.')}</p>
                <div class="wp-assistant-row">
                    <input type="text" class="form-control" data-assistant-question placeholder="${__('Ask about workload or project health')}" />
                    <button type="button" class="btn btn-primary" data-assistant-ask>${__('Ask')}</button>
                </div>
                <div class="wp-assistant-result" data-assistant-result></div>
            </div>
            <p class="wp-note">${__('Recommendations remain reviewable; enable each model only after its data and evaluation gates are met.')}</p>
        `);
        Promise.all([
            frappe.db.get_single_value('WorkPulse Settings', 'ml_enabled'),
            frappe.db.get_single_value('WorkPulse Settings', 'llm_enabled'),
            frappe.call({ method: 'workpulse.workpulse.api.intelligence.provider_status' }),
        ]).then(([mlEnabled, llmEnabled, providerResponse]) => {
            const provider = providerResponse.message || {};
            $content.find('.wp-settings-list').html([
                [__('Predictive models'), mlEnabled],
                [__('Language assistant'), llmEnabled],
                [__('Provider configuration'), provider.configured ? __('API key configured') : __('Using safe fallback')],
            ].map(([label, enabled]) => `
                <div class="wp-setting-row"><span><strong>${label}</strong><small>${typeof enabled === 'boolean' ? (enabled ? __('Enabled') : __('Disabled')) : enabled}</small></span><span class="wp-state ${enabled === true ? 'is-on' : ''}">${typeof enabled === 'boolean' ? (enabled ? __('ON') : __('OFF')) : __('INFO')}</span></div>
            `).join(''));
        }).catch(() => {
            $content.find('.wp-settings-list').html(`<div class="wp-inline-error">${__('Settings are not available to your account.')}</div>`);
        });
        frappe.call({
            method: 'workpulse.workpulse.api.intelligence.list_model_versions',
            args: { limit: 25 },
        }).then((response) => {
            const rows = response.message || [];
            const $table = $content.find('.wp-models .wp-table-wrap');
            if (!rows.length) {
                $table.html(`<div class="wp-empty"><span class="wp-empty-mark">—</span><p>${__('No model versions registered.')}</p></div>`);
                return;
            }
            $table.html(`
                <table class="wp-table">
                    <thead><tr><th>${__('Model')}</th><th>${__('Version')}</th><th>${__('Status')}</th><th>${__('Evaluation')}</th></tr></thead>
                    <tbody>${rows.map((row) => `
                        <tr>
                            <td>${escape(row.model_name)}</td>
                            <td>${escape(row.version)}</td>
                            <td>${escape(row.status)}</td>
                            <td>${row.evaluation_passed ? __('Passed') : __('Pending')}</td>
                        </tr>
                    `).join('')}</tbody>
                </table>
            `);
        }).catch(() => {
            $content.find('.wp-models .wp-table-wrap').html(`<div class="wp-inline-error">${__('Model registry is not available to your account.')}</div>`);
        });
    }

    $body.on('click', '[data-view]', function () {
        setActiveView(this.dataset.view);
    });
    $body.on('click', '[data-route]', function () {
        window.location.href = this.dataset.route;
    });
    $body.on('click', '[data-list-doctype]', function () {
        frappe.set_route('List', this.dataset.listDoctype, 'List');
    });
    $body.on('click', '[data-action="refresh"]', function () {
        setActiveView(activeView);
    });
    $body.on('click', '[data-assistant-ask]', function () {
        const $input = $body.find('[data-assistant-question]');
        const $result = $body.find('[data-assistant-result]');
        $result.text(__('Working…'));
        frappe.call({
            method: 'workpulse.workpulse.api.intelligence.ask',
            args: { question: $input.val() },
        }).then((response) => {
            $result.text(response.message?.answer || __('No answer available.'));
        }).catch((error) => {
            $result.text(error.message || __('The assistant request failed.'));
        });
    });

    setActiveView('overview');
};
