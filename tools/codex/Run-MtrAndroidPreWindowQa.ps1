[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$ProjectRoot,
    [Parameter(Mandatory=$true)][string]$OutputDir,
    [Parameter(Mandatory=$true)][string]$ExpectedApkSha256,
    [switch]$Inject,
    [string]$Serial='emulator-5554'
)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
if($Serial -notmatch '^emulator-\d+$'){throw 'Emulator-only laboratory'}
$out=[IO.Path]::GetFullPath($OutputDir)
if(Test-Path -LiteralPath $out){throw 'Evidence directory already exists'}
New-Item -ItemType Directory -Path $out | Out-Null
$utf8=[Text.UTF8Encoding]::new($false)
$adb=(Get-Command adb -ErrorAction Stop).Source
$package='com.martyskin.trudrunner'
$started=Get-Date
$status='fail'
$failure=$null
$appPid=''
$verified=$false
$facts=@{}
function Save([string]$Name,[string]$Text){[IO.File]::WriteAllText((Join-Path $out $Name),$Text,$utf8)}
function Adb([string[]]$Arguments,[int]$TimeoutSeconds=20){
    $info=[Diagnostics.ProcessStartInfo]::new()
    $info.FileName=$adb
    $info.UseShellExecute=$false
    $info.CreateNoWindow=$true
    $info.RedirectStandardOutput=$true
    $info.RedirectStandardError=$true
    foreach($a in @('-s',$Serial)+$Arguments){$info.ArgumentList.Add($a)}
    $p=[Diagnostics.Process]::new()
    $p.StartInfo=$info
    try{
        if(-not $p.Start()){throw 'ADB client did not start'}
        $stdout=$p.StandardOutput.ReadToEndAsync()
        $stderr=$p.StandardError.ReadToEndAsync()
        if(-not $p.WaitForExit($TimeoutSeconds*1000)){
            $p.Kill()
            $p.WaitForExit()
            throw ('Owned ADB client timed out: '+($Arguments -join ' '))
        }
        $text=$stdout.GetAwaiter().GetResult()+$stderr.GetAwaiter().GetResult()
        if($p.ExitCode -ne 0){throw ('ADB exit '+$p.ExitCode+': '+$text)}
        return $text
    }finally{$p.Dispose()}
}
try{
    . (Join-Path $ProjectRoot 'tools/codex/MtrAndroidQaAudioGuard.ps1')
    $audioPolicy=Assert-MtrAndroidQaAudioMuted -AdbPath $adb -Serial $Serial
    Save 'audio.receipt.json' ($audioPolicy | ConvertTo-Json -Depth 10)
    if((Adb @('shell','am','get-current-user')).Trim() -ne '0'){throw 'QA requires user0'}
    $installed=(Adb @('shell','pm','path','--user','0',$package)).Trim()
    if($installed -notmatch '^package:(/[^\r\n]+/base\.apk)$'){throw 'Installed APK identity ambiguous'}
    $hash=(Adb @('shell','sha256sum',$Matches[1])).Split()[0].ToUpperInvariant()
    if($hash -ne $ExpectedApkSha256.ToUpperInvariant()){throw 'Installed APK differs from expected SHA'}
    $verified=$true
    Save 'apk.identity.json' (@{sha256=$hash;serial=$Serial;user=0}|ConvertTo-Json)
    Adb @('logcat','-c') | Out-Null
    $launch=@('shell','am','start','--user','0','-S','-n',"$package/com.cocos.game.AppActivity",'--es','mtr_state','menu')
    if($Inject){$launch+=@('--ez','mtr_qa_native_pre_window_recreate','true')}
    Save 'launch.stdout.txt' (Adb $launch)
    $watch=[Diagnostics.Stopwatch]::StartNew()
    $ready=$false
    do{
        $log=Adb @('logcat','-d','-v','threadtime')
        $ready=$log -match 'MTR_QA_SCREEN_READY screen=menu' -and $log -match 'MTR_MENU_UI_GATE_READY[^\r\n]*screen=menu'
        if($ready){break}
        Start-Sleep -Milliseconds 350
    }while($watch.ElapsedMilliseconds -lt 35000)
    Save 'launch.logcat.txt' $log
    $appPid=(Adb @('shell','pidof',$package)).Trim()
    Save 'pid.txt' $appPid
    $activities=Adb @('shell','dumpsys','activity','activities')
    Save 'activities.txt' $activities
    Save 'window.txt' (Adb @('shell','dumpsys','window','windows'))
    $remote='/sdcard/mtr_pre_window_control.png'
    Adb @('shell','screencap','-p',$remote) | Out-Null
    Adb @('pull',$remote,(Join-Path $out 'screen.png')) | Out-Null
    Adb @('shell','rm',$remote) | Out-Null
    $destroy=$log.IndexOf('MTR_NATIVE_LIFECYCLE event=destroy_enter')
    $window=$log.IndexOf('AndroidPlatform: APP_CMD_INIT_WINDOW')
    $early=$destroy -ge 0 -and ($window -lt 0 -or $destroy -lt $window)
    $instances=[regex]::Matches($log,'MTR_NATIVE_LIFECYCLE event=create_ready instance=(\d+)')
    $newInstance=$instances.Count -ge 2 -and $instances[0].Groups[1].Value -ne $instances[$instances.Count-1].Groups[1].Value
    $requestCount=[regex]::Matches($log,'MTR_NATIVE_LIFECYCLE event=qa_pre_window_recreate_requested').Count
    $fatal=$log -match 'FATAL EXCEPTION|Fatal signal|ANR in com\.martyskin\.trudrunner|JS:\s*(Uncaught|TypeError|ReferenceError|SyntaxError)|MTR_[A-Z0-9_]*(?:_FAIL|_ERROR)\b'
    $focused=$activities -match 'topResumedActivity=ActivityRecord\{[^\r\n]*u0 com\.martyskin\.trudrunner/com\.cocos\.game\.AppActivity'
    $bytes=(Get-Item (Join-Path $out 'screen.png')).Length
    $facts=@{menu_ready=$ready;marker_wait_ms=$watch.ElapsedMilliseconds;pre_window_destroy=$early;window_seen=$window -ge 0;native_destroy_seen=$log -match 'AndroidPlatform: APP_CMD_DESTROY';destroy_after_cocos=$log -match 'MTR_NATIVE_LIFECYCLE event=destroy_after_cocos';guard_exit_request=$log -match 'MTR_NATIVE_PRE_WINDOW_CLOSE_EXIT_REQUESTED';fresh_create_count=$instances.Count;new_instance=$newInstance;request_count=$requestCount;fatal=$fatal;focused_user0=$focused;screenshot_bytes=$bytes;pid=$appPid}
    $injectedPass=$early -and $newInstance -and $requestCount -eq 1 -and $facts.destroy_after_cocos -and $facts.guard_exit_request -and $log -match 'MTR_NATIVE_LIFECYCLE event=create_enter_saved'
    if($ready -and -not $fatal -and $focused -and $bytes -gt 100000 -and ((-not $Inject -and $requestCount -eq 0) -or ($Inject -and $injectedPass))){$status='pass'}
    else{
        $failure='Runtime contract did not pass; preserve exact facts and logs'
        if($appPid -match '^\d+$'){
            try{Save 'sigquit.stdout.txt' (Adb @('shell','run-as',$package,'/system/bin/kill','-3',$appPid));Start-Sleep -Seconds 2;Save 'sigquit.logcat.txt' (Adb @('logcat','-d','-v','threadtime'))}catch{Save 'sigquit.error.txt' $_.Exception.Message}
            try{Save 'native-backtrace.txt' (Adb @('shell','run-as',$package,'/system/bin/debuggerd','-b',$appPid) 25)}catch{Save 'native-backtrace.error.txt' $_.Exception.Message}
        }
    }
}catch{$failure=$_.Exception.Message}
finally{
    if($verified){try{Save 'finally.force-stop.txt' (Adb @('shell','am','force-stop','--user','0',$package))}catch{$status='fail';$failure="$failure; cleanup: $($_.Exception.Message)"}}
    $report=@{schema='mtr.pre_window_recreate_diagnostic.v1';status=$status;failure=$failure;injected=[bool]$Inject;expected_apk_sha256=$ExpectedApkSha256;serial=$Serial;user=0;facts=$facts;timeout_seconds=35;retry_count=0;started_at=$started.ToString('o');finished_at=(Get-Date).ToString('o')}
    Save 'report.json' ($report|ConvertTo-Json -Depth 12)
}
$report|ConvertTo-Json -Depth 8
if($status -ne 'pass'){exit 1}
