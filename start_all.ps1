$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Python = Join-Path $Root ".venv\Scripts\python.exe"

if (-not (Test-Path $Python)) {
    throw "Virtual environment Python not found: $Python"
}

$RunId = Get-Date -Format "yyyyMMdd-HHmmss"
$LogDir = Join-Path $Root ".logs\stage5-$RunId"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

$Services = @(
    @{ Name = "registry";   Module = "registry";          Url = "http://localhost:10000"; Delay = 2 },
    @{ Name = "tax";        Module = "tax_agent";         Url = "http://localhost:10102"; Delay = 0 },
    @{ Name = "compliance"; Module = "compliance_agent";  Url = "http://localhost:10103"; Delay = 3 },
    @{ Name = "financial";  Module = "financial_agent";   Url = "http://localhost:10104"; Delay = 0 },
    @{ Name = "law";        Module = "law_agent";         Url = "http://localhost:10101"; Delay = 3 },
    @{ Name = "customer";   Module = "customer_agent";    Url = "http://localhost:10100"; Delay = 0 }
)

$Processes = @()

try {
    foreach ($Service in $Services) {
        $OutLog = Join-Path $LogDir "$($Service.Name).out.log"
        $ErrLog = Join-Path $LogDir "$($Service.Name).err.log"

        Write-Host "Starting $($Service.Name) service at $($Service.Url)..."
        $Process = Start-Process `
            -FilePath $Python `
            -ArgumentList @("-m", $Service.Module) `
            -WorkingDirectory $Root `
            -RedirectStandardOutput $OutLog `
            -RedirectStandardError $ErrLog `
            -WindowStyle Hidden `
            -PassThru

        $Processes += [pscustomobject]@{
            Name = $Service.Name
            Url = $Service.Url
            Process = $Process
            OutLog = $OutLog
            ErrLog = $ErrLog
        }

        if ($Service.Delay -gt 0) {
            Start-Sleep -Seconds $Service.Delay
        }
    }

    Write-Host ""
    Write-Host "All services started:"
    foreach ($Item in $Processes) {
        Write-Host ("  {0,-12} {1}  PID={2}" -f $Item.Name, $Item.Url, $Item.Process.Id)
    }
    Write-Host ""
    Write-Host "Logs: $LogDir"
    Write-Host ""
    Write-Host "Open another PowerShell terminal and run:"
    Write-Host "  .\.venv\Scripts\python.exe test_client.py"
    Write-Host ""
    Write-Host "Keep this window open. Press Ctrl+C here to stop all services."

    while ($true) {
        Start-Sleep -Seconds 2
        foreach ($Item in $Processes) {
            if ($Item.Process.HasExited) {
                Write-Warning "$($Item.Name) exited with code $($Item.Process.ExitCode). Check: $($Item.ErrLog)"
            }
        }
    }
}
finally {
    Write-Host ""
    Write-Host "Stopping services..."
    foreach ($Item in $Processes) {
        if (-not $Item.Process.HasExited) {
            Stop-Process -Id $Item.Process.Id -Force
            Write-Host "Stopped $($Item.Name) PID=$($Item.Process.Id)"
        }
    }
}
