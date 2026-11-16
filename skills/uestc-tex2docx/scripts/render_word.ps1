param([string]$InputDoc,[string]$Pdf,[switch]$Refresh)
$ErrorActionPreference = 'Stop'
$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = 0
$document = $null
try {
  Write-Output 'Opening'
  $document = $word.Documents.Open([IO.Path]::GetFullPath($InputDoc), $false, (-not $Refresh.IsPresent))
  Write-Output 'Opened'
  if ($Refresh) {
    $document.Fields.Update() | Out-Null
    Write-Output 'Fields updated'
    $tocCount = $document.TablesOfContents.Count
    for ($tocIndex = 1; $tocIndex -le $tocCount; $tocIndex++) { $document.TablesOfContents.Item($tocIndex).Update() }
    Write-Output 'TOC updated'
    $document.Repaginate()
    Write-Output 'Paginated'
    $updatedPath = [IO.Path]::GetFullPath($InputDoc).Replace('.docx','-updated.docx')
    $document.SaveAs2($updatedPath, 16)
    Write-Output 'Saved'
  }
  Write-Output 'Exporting'
  $document.ExportAsFixedFormat([IO.Path]::GetFullPath($Pdf), 17)
  Write-Output ('Pages: ' + $document.ComputeStatistics(2))
} finally {
  if ($document) { $document.Close(0) }
  $word.Quit()
  [Runtime.InteropServices.Marshal]::ReleaseComObject($word) | Out-Null
}
