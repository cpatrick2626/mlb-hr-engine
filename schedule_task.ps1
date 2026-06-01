param(
    [switch]$Remove,
    [switch]$Status
)

$TaskName = "MLB HR Engine Daily Ops"
$RepoRoot = "C:\Users\ChrisPatrick\OneDrive - Resilience\Desktop\MLB HR Engine\mlb-hr-engine-master"
$BatFile = Join-Path $RepoRoot "run_ops_daily.bat"

if ($Status) {
    $existing = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    if ($existing) {
        $info = Get-ScheduledTaskInfo -TaskName $TaskName -ErrorAction SilentlyContinue
        Write-Host "Task: $TaskName"
        Write-Host "State: $($existing.State)"
        Write-Host "Last Run: $($info.LastRunTime)"
        Write-Host "Last Result: $($info.LastTaskResult)"
        Write-Host "Next Run: $($info.NextRunTime)"
    } else {
        Write-Host "Task '$TaskName' is NOT registered."
    }
    exit 0
}

if ($Remove) {
    $existing = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    if ($existing) {
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
        Write-Host "Removed task: $TaskName"
    } else {
        Write-Host "Task '$TaskName' was not registered."
    }
    exit 0
}

if (-not (Test-Path $BatFile)) {
    Write-Error "Missing bat file: $BatFile"
    exit 1
}

$existing = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($existing) {
    Write-Host "Task '$TaskName' already exists. No changes made."
    exit 0
}

$Action = New-ScheduledTaskAction -Execute "cmd.exe" -Argument "/c `"$BatFile`"" -WorkingDirectory $RepoRoot
$Trigger = New-ScheduledTaskTrigger -Daily -At 8:00AM
$Settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Hours 2)
$Principal = New-ScheduledTaskPrincipal -UserId ([System.Security.Principal.WindowsIdentity]::GetCurrent().Name) -LogonType Interactive -RunLevel Highest

Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Settings $Settings -Principal $Principal -Description "MLB HR Engine Daily Ops" | Out-Null

Write-Host "Task registered successfully: $TaskName"
