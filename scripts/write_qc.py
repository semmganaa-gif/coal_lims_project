content = """{% extends "base.html" %}
{% block content %}
<style>
.qc-dashboard{padding:1.5rem;background:linear-gradient(135deg,#f8fafc,#e2e8f0);min-height:calc(100vh - 60px)}
.qc-header{background:#fff;border-radius:16px;padding:1.25rem 1.5rem;margin-bottom:1.5rem;box-shadow:0 4px 20px rgba(0,0,0,.08);display:flex;justify-content:space-between;align-items:center}
.qc-title{font-size:1.5rem;font-weight:800;background:linear-gradient(135deg,#1e40af,#7c3aed);-webkit-background-clip:text;-webkit-text-fill-color:transparent;margin:0}
</style>
{% endblock %}"""

with open("D:/coal_lims_project/app/templates/quality/control_charts.html", "w") as f:
    f.write(content)
print("Done")
