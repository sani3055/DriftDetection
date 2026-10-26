$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$outDir = Join-Path $root 'Project_XX_SHAP_CloudTrail_Drift\Presentation'
New-Item -ItemType Directory -Force $outDir | Out-Null
$pptxPath = Join-Path $outDir 'Capstone_IDP_Progress_Presentation.pptx'
if (Test-Path $pptxPath) { Remove-Item -LiteralPath $pptxPath -Force }

$ppt = New-Object -ComObject PowerPoint.Application
$ppt.Visible = -1
$pres = $ppt.Presentations.Add()
$pres.PageSetup.SlideWidth = 960
$pres.PageSetup.SlideHeight = 540

$navy = 0x5D3617
$blue = 0xB86A2F
$teal = 0xA47C26
$light = 0xF7F9FC
$dark = 0x1F2937
$muted = 0x667085
$white = 0xFFFFFF

function Set-Bg($slide, [int]$color) {
    $slide.FollowMasterBackground = 0
    $slide.Background.Fill.ForeColor.RGB = $color
}

function Add-Text($slide, [string]$text, [double]$x, [double]$y, [double]$w, [double]$h, [double]$size = 18, [bool]$bold = $false, [int]$color = $dark, [int]$align = 1) {
    $shape = $slide.Shapes.AddTextbox(1, $x, $y, $w, $h)
    $text = $text.Replace('\n', [Environment]::NewLine)
    $shape.TextFrame.MarginLeft = 4
    $shape.TextFrame.MarginRight = 4
    $shape.TextFrame.MarginTop = 2
    $shape.TextFrame.MarginBottom = 2
    $shape.TextFrame.WordWrap = -1
    $shape.TextFrame.TextRange.Text = $text
    $shape.TextFrame.TextRange.Font.Name = 'Arial'
    $shape.TextFrame.TextRange.Font.Size = $size
    $shape.TextFrame.TextRange.Font.Bold = if ($bold) { -1 } else { 0 }
    $shape.TextFrame.TextRange.Font.Color.RGB = $color
    $shape.TextFrame.TextRange.ParagraphFormat.Alignment = $align
    return $shape
}

function Add-Rect($slide, [double]$x, [double]$y, [double]$w, [double]$h, [int]$fill, [int]$line = $fill, [double]$radius = 0) {
    $shapeType = if ($radius -gt 0) { 5 } else { 1 }
    $shape = $slide.Shapes.AddShape($shapeType, $x, $y, $w, $h)
    $shape.Fill.ForeColor.RGB = $fill
    $shape.Line.ForeColor.RGB = $line
    $shape.Line.Weight = 1
    return $shape
}

function Add-Footer($slide, [string]$text = 'Source: project artifacts | Status: research prototype and submission package') {
    Add-Text $slide $text 48 512 864 18 9 $false $muted 1 | Out-Null
}

function Add-Title($slide, [string]$title, [string]$eyebrow = 'SHAP-GUIDED CLOUDTRAIL DRIFT DIAGNOSIS') {
    Add-Text $slide $eyebrow 48 28 864 20 11 $true $teal 1 | Out-Null
    Add-Text $slide $title 48 58 864 48 30 $true $navy 1 | Out-Null
}

function Add-Image($slide, [string]$path, [double]$x, [double]$y, [double]$w, [double]$h) {
    if (Test-Path $path) {
        $slide.Shapes.AddPicture($path, 0, -1, $x, $y, $w, $h) | Out-Null
    }
}

# 1. Title
$slide = $pres.Slides.Add($pres.Slides.Count + 1, 12); Set-Bg $slide $light
Add-Rect $slide 0 0 18 540 $teal $teal | Out-Null
Add-Text $slide 'CAPSTONE / IDP JOURNAL OUTCOME' 70 76 820 26 14 $true $teal 1 | Out-Null
Add-Text $slide 'SHAP-Guided Drift Diagnosis\nfor Adaptive AWS CloudTrail Anomaly Detection' 70 130 800 145 38 $true $navy 1 | Out-Null
Add-Text $slide 'Research implementation, PRISMA evidence package, and Q1/Q2 journal plan' 72 300 720 42 20 $false $muted 1 | Out-Null
Add-Text $slide 'Project folder placeholder: Project_XX - replace XX with assigned number' 72 430 700 28 13 $false $dark 1 | Out-Null
Add-Footer $slide 'Prepared for supervisor progress review | 26 October 2026' 

# 2. Problem
$slide = $pres.Slides.Add($pres.Slides.Count + 1, 12); Set-Bg $slide $white; Add-Title $slide 'The research problem is deciding when to adapt'
Add-Text $slide 'Cloud activity changes for legitimate reasons: new services, regions, identities, and automation. A feature alarm alone cannot tell us whether the detector should be retrained.' 58 135 470 90 20 $false $dark 1 | Out-Null
Add-Rect $slide 590 130 290 78 0xE8F1F8 0xD6E4F0 1 | Out-Null; Add-Text $slide 'Feature drift' 610 145 250 26 22 $true $navy 1 | Out-Null; Add-Text $slide 'The observed records changed' 610 176 250 22 15 $false $muted 1 | Out-Null
Add-Rect $slide 590 235 290 78 0xEAF6F4 0xD5EEE9 1 | Out-Null; Add-Text $slide 'Attribution drift' 610 250 250 26 22 $true $teal 1 | Out-Null; Add-Text $slide 'The detector relies differently' 610 281 250 22 15 $false $muted 1 | Out-Null
Add-Rect $slide 590 340 290 78 0xFFF4E5 0xF2DFC0 1 | Out-Null; Add-Text $slide 'Adaptation gate' 610 355 250 26 22 $true $blue 1 | Out-Null; Add-Text $slide 'Retrain only with evidence' 610 386 250 22 15 $false $muted 1 | Out-Null
Add-Text $slide 'Research question: does combining feature drift with SHAP-attribution drift reduce unnecessary adaptation without losing controlled security sensitivity?' 58 355 470 80 21 $true $navy 1 | Out-Null
Add-Footer $slide

# 3. Study design
$slide = $pres.Slides.Add($pres.Slides.Count + 1, 12); Set-Bg $slide $light; Add-Title $slide 'The study separates observation from labelled evaluation'
Add-Rect $slide 58 140 380 270 0xE8F1F8 0xD6E4F0 1 | Out-Null
Add-Text $slide 'TRACK A - REAL CORPUS' 82 165 330 26 18 $true $navy 1 | Out-Null
Add-Text $slide '- 1,939,207 CloudTrail-style records\n- 45 chronological monthly windows\n- feature and SHAP drift timelines\n- no attack labels -> observational claims only' 82 210 325 150 20 $false $dark 1 | Out-Null
Add-Rect $slide 520 140 380 270 0xEAF6F4 0xD5EEE9 1 | Out-Null
Add-Text $slide 'TRACK B - CONTROLLED BENCHMARK' 544 165 330 26 18 $true $teal 1 | Out-Null
Add-Text $slide '- semantic benign/security perturbations\n- validation-tuned thresholds\n- held-out seeds and scenarios\n- diagnosis and adaptation metrics' 544 210 325 150 20 $false $dark 1 | Out-Null
Add-Footer $slide 'Source: data_manifest/real_cloudtrail_manifest.json; data/benchmark/*'

# 4. Data + method
$slide = $pres.Slides.Add($pres.Slides.Count + 1, 12); Set-Bg $slide $white; Add-Title $slide 'The real corpus is large, but the protocol respects its limits'
$metrics = @(@('1.94M','records'),@('45','months'),@('18','columns'),@('0','attack labels'))
$x=58
foreach($m in $metrics){ Add-Rect $slide $x 135 180 110 0xF7F9FC 0xD9E2EC 1 | Out-Null; Add-Text $slide $m[0] $x 153 180 42 30 $true $navy 2 | Out-Null; Add-Text $slide $m[1] $x 195 180 24 15 $false $muted 2 | Out-Null; $x += 208 }
Add-Text $slide 'Chronological protocol' 58 300 280 28 20 $true $teal 1 | Out-Null
Add-Text $slide '27 train months  ->  9 validation months  ->  9 held-out test months' 58 340 800 34 21 $false $dark 1 | Out-Null
Add-Text $slide 'The richer raw export confirms day/hour timestamps exist, but it is the same underlying corpus - not independent validation.' 58 405 800 45 16 $false $muted 1 | Out-Null
Add-Footer $slide

# 5. Pipeline
$slide = $pres.Slides.Add($pres.Slides.Count + 1, 12); Set-Bg $slide $light; Add-Title $slide 'Dual-signal diagnosis gates protected adaptation'
$steps = @(@('1','Encode','Train-only category maps'),@('2','Detect','Isolation Forest anomaly score'),@('3','Explain','TreeSHAP attribution vectors'),@('4','Monitor','Feature + attribution drift'),@('5','Adapt','Replay + normal-candidate retraining'))
$x=42
foreach($s in $steps){ Add-Rect $slide $x 180 160 150 0xFFFFFF 0xD9E2EC 1 | Out-Null; Add-Text $slide $s[0] $x+12 195 30 30 22 $true $teal 1 | Out-Null; Add-Text $slide $s[1] $x+12 235 136 28 18 $true $navy 1 | Out-Null; Add-Text $slide $s[2] $x+12 278 136 45 14 $false $muted 1 | Out-Null; $x += 180 }
Add-Text $slide 'Stable -> benign drift -> security-relevant drift -> review required' 80 390 800 35 22 $true $blue 2 | Out-Null
Add-Footer $slide

# 6. Results
$slide = $pres.Slides.Add($pres.Slides.Count + 1, 12); Set-Bg $slide $white; Add-Title $slide 'The benchmark shows lower unnecessary adaptation, not universal F1 gains'
Add-Image $slide (Join-Path $root 'figures\adaptation_policy_comparison.png') 55 130 530 320
Add-Rect $slide 625 145 285 260 0xF7F9FC 0xD9E2EC 1 | Out-Null
Add-Text $slide 'Measured result' 650 170 230 25 18 $true $teal 1 | Out-Null
Add-Text $slide 'Dual-signal vs static:\n\nF1 difference\n-0.0028\n\nFalse-positive-rate difference\n-0.0885\n\nBH-adjusted q = 0.00043' 650 210 230 170 19 $false $dark 1 | Out-Null
Add-Footer $slide 'Source: results/paired_inference.csv; semi-synthetic benchmark only'

# 7. Robustness
$slide = $pres.Slides.Add($pres.Slides.Count + 1, 12); Set-Bg $slide $light; Add-Title $slide 'Ablations expose detector and window-size sensitivity'
Add-Text $slide 'Independent labelled CloudTrail validation' 58 135 420 28 20 $true $navy 1 | Out-Null
Add-Text $slide 'Isolation Forest: recall 0.7137 | F1 0.4519 | FPR 0.1738\nLOF: recall 0.9954 | F1 0.5334 | FPR 0.2088\nOne-Class SVM: recall 0.0008 | F1 0.0015 | FPR 0.0042\nExternal temporal checkpoint: all policies F1 0.9524; FPR 0.5000' 58 180 470 120 18 $false $dark 1 | Out-Null
Add-Text $slide 'Window-size ablation' 58 335 300 28 20 $true $teal 1 | Out-Null
Add-Text $slide 'Security recall: 100 rows = 0.0884\n200 rows = 0.4918\n500 rows = 0.4152' 58 380 360 82 18 $false $dark 1 | Out-Null
Add-Image $slide (Join-Path $root 'figures\diagnosis_confusion_matrix.png') 585 140 310 300
Add-Footer $slide 'Source: data/robustness/*; data/external_validation/*'

# 8. Submission package
$slide = $pres.Slides.Add($pres.Slides.Count + 1, 12); Set-Bg $slide $white; Add-Title $slide 'The submission package is prepared; four actions remain'
Add-Rect $slide 58 135 390 280 0xEAF6F4 0xD5EEE9 1 | Out-Null
Add-Text $slide 'READY NOW' 84 160 300 25 18 $true $teal 1 | Out-Null
Add-Text $slide '[OK] Working implementation and results\n[OK] 100-record 2022-2026 evidence set\n[OK] PRISMA protocol and flow accounting\n[OK] Consolidated Word review\n[OK] Project report draft\n[OK] Presentation and journal shortlist' 84 205 330 170 19 $false $dark 1 | Out-Null
Add-Rect $slide 510 135 390 280 0xFFF4E5 0xF2DFC0 1 | Out-Null
Add-Text $slide 'MANUAL BEFORE SENDING' 536 160 330 25 18 $true $blue 1 | Out-Null
Add-Text $slide '1. Replace Project_XX with assigned number\n2. Two-reviewer title/abstract/full-text screening\n3. Recheck current Q1/Q2 status and author guidelines\n4. Supervisor/team review and Google Drive upload' 536 205 330 170 19 $false $dark 1 | Out-Null
Add-Text $slide 'Working target: IEEE Transactions on Cloud Computing (Q1 in the attached 2023 JCR list)' 58 450 800 28 18 $true $navy 1 | Out-Null
Add-Footer $slide 'The package is transparent about what is complete and what still requires human confirmation.'

$pres.SaveAs($pptxPath, 24)
$pres.Close()
$ppt.Quit()
Write-Output $pptxPath
