# Mở file DOCX bằng Word (ẩn), cập nhật mọi trường (mục lục, danh mục hình/bảng,
# số caption, số trang), lưu lại và (tùy chọn) xuất PDF.
# Gọi từ build_report.py khi có cờ --word.
param(
    [Parameter(Mandatory = $true)][string]$Docx,
    [string]$Pdf = ""
)
$ErrorActionPreference = 'Stop'
$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = 0
try {
    $doc = $word.Documents.Open($Docx, $false, $false, $false)
    # Lượt 1 cập nhật số caption; lượt 2 cập nhật mục lục với số trang đã ổn định
    for ($i = 0; $i -lt 2; $i++) {
        $doc.Fields.Update() | Out-Null
        foreach ($t in $doc.TablesOfContents) { $t.Update() | Out-Null }
        foreach ($t in $doc.TablesOfFigures) { $t.Update() | Out-Null }
        $doc.Repaginate()
    }
    foreach ($s in $doc.Sections) {
        foreach ($h in $s.Headers) { $h.Range.Fields.Update() | Out-Null }
        foreach ($f in $s.Footers) { $f.Range.Fields.Update() | Out-Null }
    }
    $doc.Save()
    if ($Pdf -ne "") { $doc.ExportAsFixedFormat($Pdf, 17) }
    $doc.Close($false)
}
finally {
    $word.Quit()
}
