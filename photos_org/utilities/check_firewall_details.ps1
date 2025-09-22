# Detailed Firewall Rule Check
Write-Host "=== Detailed PhotoSystem Firewall Rules ===" -ForegroundColor Green
Write-Host ""

$rules = Get-NetFirewallRule | Where-Object { $_.DisplayName -like "*photosystem*" }

foreach ($rule in $rules) {
    Write-Host "Rule Name: $($rule.DisplayName)" -ForegroundColor Yellow
    Write-Host "  Enabled: $($rule.Enabled)"
    Write-Host "  Direction: $($rule.Direction)"
    Write-Host "  Action: $($rule.Action)"
    Write-Host "  Profile: $($rule.Profile)"

    # Check if rule has port information
    $portFilter = $rule | Get-NetFirewallPortFilter
    if ($portFilter) {
        Write-Host "  Protocol: $($portFilter.Protocol)"
        Write-Host "  Local Port: $($portFilter.LocalPort)"
        Write-Host "  Remote Port: $($portFilter.RemotePort)"
    }

    # Check application filter
    $appFilter = $rule | Get-NetFirewallApplicationFilter
    if ($appFilter) {
        Write-Host "  Program: $($appFilter.Program)"
    }

    Write-Host ""
}

# Test specific port 8000
Write-Host "=== Testing Port 8000 Access ===" -ForegroundColor Green
Write-Host ""

# Test if we can access port 8000 from another machine
Write-Host "Testing connectivity to 192.168.110.40:8000..." -ForegroundColor Yellow
try {
    $tcpClient = New-Object System.Net.Sockets.TcpClient
    $connectResult = $tcpClient.BeginConnect("192.168.110.40", 8000, $null, $null)
    $waitResult = $connectResult.AsyncWaitHandle.WaitOne(5000)  # 5 second timeout

    if ($waitResult) {
        $tcpClient.EndConnect($connectResult)
        Write-Host "SUCCESS: TCP connection to port 8000 established" -ForegroundColor Green
    } else {
        Write-Host "FAILED: TCP connection to port 8000 timed out" -ForegroundColor Red
    }
    $tcpClient.Close()
} catch {
    Write-Host "ERROR: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""
Write-Host "=== Check Complete ===" -ForegroundColor Green
