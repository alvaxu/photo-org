# PhotoSystem Network Diagnosis Script
Write-Host "=== PhotoSystem Network Diagnosis ===" -ForegroundColor Green
Write-Host ""

# 1. Check port listening status
Write-Host "1. Checking port 8000 listening status..." -ForegroundColor Yellow
$listening = netstat -ano | findstr ":8000" | findstr "LISTENING"
if ($listening) {
    Write-Host "OK: Port 8000 is listening" -ForegroundColor Green
    Write-Host $listening
} else {
    Write-Host "ERROR: Port 8000 is not listening" -ForegroundColor Red
}
Write-Host ""

# 2. Check firewall status
Write-Host "2. Checking firewall status..." -ForegroundColor Yellow
$firewallProfiles = Get-NetFirewallProfile
foreach ($profile in $firewallProfiles) {
    Write-Host "$($profile.Name): $($profile.Enabled)"
}
Write-Host ""

# 3. Check PhotoSystem firewall rules
Write-Host "3. Checking PhotoSystem firewall rules..." -ForegroundColor Yellow
$rules = Get-NetFirewallRule | Where-Object { $_.DisplayName -like "*PhotoSystem*" -or $_.DisplayName -like "*photosystem*" }
if ($rules.Count -gt 0) {
    Write-Host "OK: Found $($rules.Count) PhotoSystem firewall rules" -ForegroundColor Green
    $rules | Select-Object DisplayName, Enabled, Direction, Action, Profile | Format-Table
} else {
    Write-Host "ERROR: No PhotoSystem firewall rules found" -ForegroundColor Red
}
Write-Host ""

# 4. Check network configuration
Write-Host "4. Checking network configuration..." -ForegroundColor Yellow
$networks = Get-NetConnectionProfile
foreach ($net in $networks) {
    Write-Host "Network: $($net.Name) - Type: $($net.NetworkCategory)"
}
Write-Host ""

# 5. Check IP addresses
Write-Host "5. Checking IP addresses..." -ForegroundColor Yellow
$ips = Get-NetIPAddress | Where-Object { $_.AddressFamily -eq "IPv4" -and $_.IPAddress -notlike "127.*" }
foreach ($ip in $ips) {
    Write-Host "IP: $($ip.IPAddress) - Interface: $($ip.InterfaceAlias)"
}
Write-Host ""

# 6. Test local connection
Write-Host "6. Testing local connection..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://127.0.0.1:8000" -TimeoutSec 5 -ErrorAction Stop
    Write-Host "OK: Local connection successful - Status: $($response.StatusCode)" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Local connection failed: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

Write-Host "=== Diagnosis Complete ===" -ForegroundColor Green
