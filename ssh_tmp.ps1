Import-Module Posh-SSH

# Try as root (since the user's prompt shows root@iZ2vc...)
$cred = New-Object System.Management.Automation.PSCredential('root', (ConvertTo-SecureString 'abc123456' -AsPlainText -Force))
$session = New-SSHSession -ComputerName '47.109.191.13' -Credential $cred -AcceptKey -Port 22

$cmds = @(
    "ls -la /etc/letsencrypt/live/baimeixiaofan.xyz/ 2>&1",
    "ls -la /etc/letsencrypt/live/ 2>&1",
    "nginx -t 2>&1",
    "systemctl is-active nginx 2>&1",
    "cat -n /etc/nginx/sites-enabled/default 2>&1"
)

foreach ($cmd in $cmds) {
    Write-Output "=== $cmd ==="
    $r = Invoke-SSHCommand -SSHSession $session -Command $cmd
    if ($r.Output) { $r.Output | ForEach-Object { Write-Output $_ } }
    if ($r.Error -and $r.Error -ne "None") { Write-Output "ERR: $($r.Error)" }
}

Remove-SSHSession -SSHSession $session
