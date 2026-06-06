# Allow LAN access to timeline server (port 8765). Run as Administrator once.
#Requires -RunAsAdministrator
netsh advfirewall firewall add rule name="HomeLab Timeline 8765" dir=in action=allow protocol=TCP localport=8765 profile=private,domain
Write-Host "Firewall rule added for TCP 8765 (private + domain networks)"
