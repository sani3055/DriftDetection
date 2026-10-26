param([string]$InputDocx, [string]$OutputPdf, [switch]$RefreshFields)
$ErrorActionPreference = 'Stop'
$wordApp = New-Object -ComObject Word.Application
$wordApp.Visible = $false
$wordApp.DisplayAlerts = 0
$wordApp.AutomationSecurity = 3
try {
    $wordDoc = $wordApp.Documents.Open($InputDocx, $false, (-not $RefreshFields), $false, '', '', $false, '', '', 0, 0, $false, $false, 0, $true)
    if ($RefreshFields) {
        $wordDoc.Repaginate()
        $wordDoc.Fields.Update() | Out-Null
        $wordDoc.Repaginate()
        $wordDoc.Fields.Update() | Out-Null
        $wordDoc.Save()
    }
    $wordDoc.ExportAsFixedFormat($OutputPdf, 17)
    $pages = $wordDoc.ComputeStatistics(2)
    Write-Output "Pages: $pages"
    $wordDoc.Close(0)
} finally {
    $wordApp.Quit(0)
}
