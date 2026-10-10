### WorkPulse

AI-powered workforce and project intelligence for ERPNext

### Current foundation

The app now provides the WorkPulse foundation DocTypes (`WP Portfolio`, `WP Team`,
`WP Team Member`, `WP Team Requirement`, `WP Task Skill`, `WP Skill Alias`, and
`WP Workload Snapshot`). The daily scheduler runs
`workpulse.tasks.snapshots.enqueue_nightly_workload`; task saves update data-health
flags and debounce a snapshot refresh. The permission-checked explorer endpoints are
available at `workpulse.workpulse.api.explorer.get_tree` and
`workpulse.workpulse.api.explorer.get_employee_card`.

Build the desk assets into the image with:

The production image invokes `bench build --app workpulse` after installing the app.
WorkPulse does not provide a nested `package.json` build script because Frappe's
asset builder invokes app package scripts from inside that command; nesting another
`bench build` would deadlock the build lock.

### Demo data

After installing WorkPulse and HRMS on a demo site, seed the repeatable company,
employee, task, and leave records with:

```bash
bench --site <site-name> execute workpulse.setup.seed_demo_data.seed_demo_data
```

The command creates `Demo Company`, four demo employees, representative Tasks and
ToDos, overlapping Open Leave Applications, and local-only demo users with the
password `WorkPulseDemo123!`. Do not run it against a production site.

### Installation

You can install this app using the [bench](https://github.com/frappe/bench) CLI:

```bash
cd $PATH_TO_YOUR_BENCH
bench get-app $URL_OF_THIS_REPO --branch new
bench install-app workpulse
```

### Contributing

This app uses `pre-commit` for code formatting and linting. Please [install pre-commit](https://pre-commit.com/#installation) and enable it for this repository:

```bash
cd apps/workpulse
pre-commit install
```

Pre-commit is configured to use the following tools for checking and formatting your code:

- ruff
- eslint
- prettier
- pyupgrade
### CI

This app can use GitHub Actions for CI. The following workflows are configured:

- CI: Installs this app and runs unit tests on every push to `develop` branch.
- Linters: Runs [Frappe Semgrep Rules](https://github.com/frappe/semgrep-rules) and [pip-audit](https://pypi.org/project/pip-audit/) on every pull request.


### License

mit
