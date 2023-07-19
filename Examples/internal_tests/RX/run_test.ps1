$param1=$args[0]
py $param1
if (Test-Path .\$param1.log) {
    Remove-Item .\$param1.log
}
Rename-Item -Path .\app.log -NewName .\$param1.log