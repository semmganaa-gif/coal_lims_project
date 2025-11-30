from pathlib import Path

path = Path(r'app/templates/analysis_forms/mass_workspace_form.html')
text = path.read_text(encoding='utf-8')
first = text.index('<script>')
second = text.index('</script>', first)
prefix = text[:first]
suffix = text[second+len('</script>'):]
new_block = """<script src=\"{{ url_for('static', filename='js/aggrid_helpers.js') }}\"></script>\n<script>\n(() => {\n  const gridEl     = document.getElementById('massGrid');\n  const = document.getElementById('btnRefresh');\n  const    = document.getElementById('btnSave');\n  const  = document.getElementById('markReadyToggle');\n  const  = document.getElementById('toggleIncludeReady');\n  const     = document.getElementById('searchCode');\n  let gridApi = null;\n\n  const readyBadge = (isReady) => isReady\n    ? '<span class=\\\"badge text-bg-success mw-badge\\\">Ready</span>'\n    : '<span class=\\\"badge text-bg-secondary mw-badge\\\">New</span>'\n\n  const columnDefs = [\n    {\n      headerName:'',\n      width:55,\n      checkboxSelection:true,\n      headerCheckboxSelection:true,\n      headerCheckboxSelectionFilteredOnly:true,\n      pinned:'left',\n      sortable:false,\n      resizable:false\n    },\n    { headerName:'ID', field:'id', width:80, pinned:'left', cellClass:'text-muted' },\n    { headerName:'??????? ???', field:'sample_code', minWidth:220,\n      cellRenderer:p=><div class=\\\"d-flex flex-column gap-1\\\">\n          <span class=\\\"fw-semibold text-primary\\\">...</script>"""
text = prefix + new_block + suffix
path.write_text(text, encoding='utf-8')
