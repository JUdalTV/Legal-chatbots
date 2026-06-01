<#
.SYNOPSIS
    Mở backend local (uvicorn :8000) ra Internet bằng Cloudflare quick tunnel (free).
    URL https://*.trycloudflare.com đổi mỗi lần chạy — dán vào ô "API base" của UI.

.DESCRIPTION
    Quy trình public UI + backend local:
      1. Bật backend:   .\.venv\Scripts\python.exe -m uvicorn api.main:app --port 8000
      2. Chạy script:   .\tunnel.ps1
      3. Copy URL in ra (đã tự copy vào clipboard) → dán vào ô "API base" trong UI.
    UI có thể nằm trên GitHub Pages; CORS backend đã mở (allow_origin_regex=".*").

.PARAMETER Port
    Cổng backend local (mặc định 8000).

.EXAMPLE
    .\tunnel.ps1
    .\tunnel.ps1 -Port 8001
#>
param([int]$Port = 8000)

$exe = (Get-Command cloudflared -ErrorAction SilentlyContinue).Source
if (-not $exe) { $exe = "C:\Program Files (x86)\cloudflared\cloudflared.exe" }
if (-not (Test-Path $exe)) {
    Write-Host "Không tìm thấy cloudflared. Cài: winget install Cloudflare.cloudflared" -ForegroundColor Red
    exit 1
}

Write-Host "Cloudflare quick tunnel -> http://localhost:$Port" -ForegroundColor Cyan
Write-Host "URL đổi mỗi lần chạy; dán vào ô 'API base' của UI. Ctrl+C để dừng.`n" -ForegroundColor DarkGray

$seen = ""
& $exe tunnel --url "http://localhost:$Port" 2>&1 | ForEach-Object {
    $line = "$_"
    if ($line -match "https://[a-z0-9-]+\.trycloudflare\.com") {
        $u = $Matches[0]
        if ($u -ne $seen) {
            $seen = $u
            Write-Host ""
            Write-Host "  ===> PUBLIC API URL: $u" -ForegroundColor Green
            try { Set-Clipboard -Value $u; Write-Host "       (đã copy vào clipboard)" -ForegroundColor DarkGray } catch {}
            Write-Host ""
        }
    }
    else {
        Write-Host $line -ForegroundColor DarkGray
    }
}
