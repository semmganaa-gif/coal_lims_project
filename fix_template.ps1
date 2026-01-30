$t = Get-Content "D:\coal_lims_project\app\templates\quality\control_charts.html" -Raw
Write-Host "Current length: " $t.Length


.\venv\Scripts\activate 
