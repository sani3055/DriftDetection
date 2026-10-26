param([string]$InputPptx, [string]$OutputPdf)
$ErrorActionPreference = 'Stop'
$powerPointApp = New-Object -ComObject PowerPoint.Application
try {
    $deck = $powerPointApp.Presentations.Open($InputPptx, $true, $false, $false)
    $deck.SaveAs($OutputPdf, 32)
    Write-Output "Slides: $($deck.Slides.Count)"
    $deck.Close()
} finally {
    $powerPointApp.Quit()
}
