### Kmu Erp Austria

ERPNext APP with Austrian default settings.

## Dev Container Setup in IntelliJ

[Hier](https://code.ransoft.at/ran-soft/intern/wiki/-/wikis/ERPNext/Frappe-Docker-Dev-Container-Setup-in-IntelliJ) wird beschrieben wie du ein Frappe Docker Projekt mithilfe von Dev Container in IntelliJ aufmachen kannst.

### Installation

You can install this app using the [bench](https://github.com/frappe/bench) CLI:

```bash
cd /development/frappe-bench
bench get-app https://<username>:<personal_access_token>@code.ransoft.at/ran-soft/intern/kmu-erp/kmu-erp-austria.git --branch main
bench --site development.localhost install-app koolcontrol_frappe_backend
```

### License

mit
