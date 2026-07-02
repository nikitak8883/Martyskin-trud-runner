param(
    [string]$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
)

$ErrorActionPreference = 'Stop'
$srcPath = Join-Path $ProjectRoot 'assets\scripts\GameRoot.ts'
$src = Get-Content -Raw -Encoding UTF8 -Path $srcPath
$errors = New-Object System.Collections.Generic.List[string]

function Add-Error([string]$message) {
    $script:errors.Add($message) | Out-Null
}

$levelsBlock = [regex]::Match($src, 'const LEVELS:[\s\S]*?const SKINS').Value
$levelMatches = [regex]::Matches($levelsBlock, "\{ name: 'Уровень (?<num>\d+): (?<name>[^']+)'[\s\S]*?speed: (?<speed>\d+), length: (?<length>\d+), target: (?<target>\d+), theme: (?<theme>\d+) \}")
if ($levelMatches.Count -ne 15) {
    Add-Error "Ожидалось 15 уровней, найдено $($levelMatches.Count)."
}

$seenThemes = @{}
foreach ($m in $levelMatches) {
    $num = [int]$m.Groups['num'].Value
    $speed = [int]$m.Groups['speed'].Value
    $length = [int]$m.Groups['length'].Value
    $target = [int]$m.Groups['target'].Value
    $theme = [int]$m.Groups['theme'].Value
    if ($speed -le 0) { Add-Error "Уровень ${num}: speed <= 0." }
    if ($length -le 0) { Add-Error "Уровень ${num}: length <= 0." }
    if ($target -le 0) { Add-Error "Уровень ${num}: target <= 0." }
    $seenThemes[$theme] = $true
}
if ($seenThemes.Count -lt 15) {
    Add-Error "Уровни должны иметь 15 тематических фонов, найдено тем: $($seenThemes.Count)."
}

$storyBlock = [regex]::Match($src, 'const STORY:[\s\S]*?const BILLBOARDS').Value
$storyRows = [regex]::Matches($storyBlock, "\['[^']+', '[^']+', '[^']+', '[^']+'\]")
if ($storyRows.Count -ne 15) {
    Add-Error "Ожидалось 15 story-наборов по 4 баннера, найдено $($storyRows.Count)."
}

$obstacleBlock = [regex]::Match($src, 'const OBSTACLES:[\s\S]*?const OBSTACLE_LABELS').Value
$obstacleLabels = [regex]::Matches($obstacleBlock, "label: '[^']+'")
if ($obstacleLabels.Count -lt 15) {
    Add-Error "Ожидалось минимум 15 препятствий с русскими подписями, найдено $($obstacleLabels.Count)."
}

$required = @(
    'КИРПИЧ',
    'ОТЧЁТ',
    'ОКНО',
    'Я НА',
    '220V',
    'НЕ',
    'ДОРОГА',
    'КРАСКА',
    'БАЛКА',
    'КАСКА ЕСТЬ',
    'ОБЪЕКТ',
    'ПРИМАТ',
    'СМЕТА',
    'БРИГАДА'
)

foreach ($needle in $required) {
    if ($src.IndexOf($needle, [System.StringComparison]::Ordinal) -lt 0) {
        Add-Error "Нет обязательной русской строки: $needle"
    }
}

$backgroundDir = Join-Path $ProjectRoot 'assets\resources\backgrounds'
$sourceManifest = Join-Path $backgroundDir 'background_sources.json'
if (-not (Test-Path -LiteralPath $sourceManifest)) {
    Add-Error "Нет манифеста фоновых источников: $sourceManifest"
}

$configDir = Join-Path $ProjectRoot 'assets\resources\config'
$requiredConfigs = @(
    'levels.json',
    'skins.json',
    'bonus_visual_states.json',
    'achievements.json',
    'current_objective_runtime_usage.json',
    'level_visual_contracts.json',
    'objective_integration_requirements.json',
    'pause_touch_zone_contract.json',
    'performance_budget.json',
    'level_visual_integration_blueprint.json',
    'visual_layer_contract.json',
    'render_layer_contract.json',
    'equipment_layer_contract.json',
    'equipment_anchor_contract.json',
    'objective_category_mapping.json',
    'visual_readability_thresholds.json',
    'achievement_ui_contract.json',
    'objective_attachment_rules.json',
    'strings_ru.json',
    'audio_manifest.json'
)
foreach ($name in $requiredConfigs) {
    $path = Join-Path $configDir $name
    if (-not (Test-Path -LiteralPath $path)) {
        Add-Error "Нет unified config: $path"
    }
}

if (Test-Path -LiteralPath (Join-Path $configDir 'levels.json')) {
    $levelsConfig = Get-Content -Raw -Encoding UTF8 -LiteralPath (Join-Path $configDir 'levels.json') | ConvertFrom-Json
    if ($levelsConfig.levels.Count -ne 15) {
        Add-Error "В assets/resources/config/levels.json должно быть 15 уровней, найдено $($levelsConfig.levels.Count)."
    }
    foreach ($level in $levelsConfig.levels) {
        if (-not $level.title) { Add-Error "Config level $($level.id): пустой title." }
        if (-not $level.theme) { Add-Error "Config level $($level.id): пустой theme." }
        if (-not $level.storyBanners -or $level.storyBanners.Count -lt 3) { Add-Error "Config level $($level.id): мало storyBanners." }
        if (-not $level.obstaclePool -or $level.obstaclePool.Count -lt 1) { Add-Error "Config level $($level.id): пустой obstaclePool." }
        if ([int]$level.targetBananas -le 0) { Add-Error "Config level $($level.id): targetBananas <= 0." }
        if ([int]$level.length -le 0) { Add-Error "Config level $($level.id): length <= 0." }
        if ([int]$level.baseSpeed -le 0) { Add-Error "Config level $($level.id): baseSpeed <= 0." }
    }
}

if (Test-Path -LiteralPath (Join-Path $configDir 'skins.json')) {
    $skinsConfig = Get-Content -Raw -Encoding UTF8 -LiteralPath (Join-Path $configDir 'skins.json') | ConvertFrom-Json
    if ($skinsConfig.skins.Count -lt 4) {
        Add-Error "В skins.json должно быть минимум 4 скина, найдено $($skinsConfig.skins.Count)."
    }
}

if (Test-Path -LiteralPath (Join-Path $configDir 'audio_manifest.json')) {
    $audioConfig = Get-Content -Raw -Encoding UTF8 -LiteralPath (Join-Path $configDir 'audio_manifest.json') | ConvertFrom-Json
    foreach ($sfx in $audioConfig.sfx) {
        $assetName = Split-Path $sfx.file -Leaf
        $audioPath = Join-Path $ProjectRoot "assets\resources\audio\$assetName"
        if (-not (Test-Path -LiteralPath $audioPath)) {
            Add-Error "Audio manifest ссылается на отсутствующий SFX: $audioPath"
        }
    }
    $requiredVoiceEvents = @('jump', 'dash', 'hurt', 'death', 'banana')
    $voiceTotal = 0
    foreach ($eventName in $requiredVoiceEvents) {
        $entry = $audioConfig.monkeyVoice.$eventName
        if (-not $entry -or $entry.Count -lt 5) {
            Add-Error "Monkey voice bank '$eventName' должен содержать минимум 5 семплов."
            continue
        }
        $voiceTotal += $entry.Count
        foreach ($voiceFile in $entry) {
            $assetName = Split-Path $voiceFile -Leaf
            $voicePath = Join-Path $ProjectRoot "assets\resources\audio\$assetName"
            if (-not (Test-Path -LiteralPath $voicePath)) {
                Add-Error "Monkey voice manifest ссылается на отсутствующий файл: $voicePath"
            }
        }
    }
    if ($voiceTotal -lt 25) {
        Add-Error "Monkey voice bank должен иметь минимум 25 семплов, найдено $voiceTotal."
    }
}

if (Test-Path -LiteralPath (Join-Path $configDir 'achievements.json')) {
    $achievementConfig = Get-Content -Raw -Encoding UTF8 -LiteralPath (Join-Path $configDir 'achievements.json') | ConvertFrom-Json
    if ($achievementConfig.achievements.Count -lt 8) {
        Add-Error "В achievements.json должно быть минимум 8 достижений, найдено $($achievementConfig.achievements.Count)."
    }
    if ($src -notmatch 'mtr_achievements') {
        Add-Error "GameRoot.ts должен сохранять достижения в mtr_achievements."
    }
    if ($src -notmatch 'mtr_unlock_achievements') {
        Add-Error "Нужен dev QA query-флаг mtr_unlock_achievements=1."
    }
}

if (Test-Path -LiteralPath (Join-Path $configDir 'current_objective_runtime_usage.json')) {
    $objectiveRuntimeConfig = Get-Content -Raw -Encoding UTF8 -LiteralPath (Join-Path $configDir 'current_objective_runtime_usage.json') | ConvertFrom-Json
    $requiredCategories = @('bonuses', 'npc_decor', 'ui_achievements', 'labels_signage', 'foreground_decor', 'background_decor')
    foreach ($category in $requiredCategories) {
        if ($objectiveRuntimeConfig.requiredRuntimeCategories -notcontains $category) {
            Add-Error "current_objective_runtime_usage.json не содержит requiredRuntimeCategories.$category."
        }
    }
    foreach ($category in $requiredCategories) {
        $keys = $objectiveRuntimeConfig.requiredRuntimeKeys.$category
        if (-not $keys -or $keys.Count -lt 1) {
            Add-Error "current_objective_runtime_usage.json не содержит requiredRuntimeKeys.$category."
            continue
        }
        foreach ($runtimeKey in $keys) {
            if ($runtimeKey -like 'objectives/*') {
                $spritePath = Join-Path $ProjectRoot ("assets\resources\" + $runtimeKey.Replace('/', '\') + ".png")
                if (-not (Test-Path -LiteralPath $spritePath)) {
                    Add-Error "Runtime sprite отсутствует: $spritePath"
                }
            }
        }
    }
    if ($src -notmatch 'BONUS_ASSET_KEYS') {
        Add-Error "Current objective runtime должен оставаться подключенным для бонусов, NPC, UI и экипировки."
    }
    foreach ($category in $requiredCategories) {
        if ($src -notmatch [regex]::Escape("'$category'")) {
            Add-Error "GameRoot.ts не содержит runtime-категорию current objectives: $category."
        }
    }
    if ($src -notmatch 'MTR_ASSET_USAGE') {
        Add-Error "GameRoot.ts должен логировать MTR_ASSET_USAGE для аудита интеграции current objectives."
    }
}

if (Test-Path -LiteralPath (Join-Path $configDir 'objective_integration_requirements.json')) {
    $objectiveReq = Get-Content -Raw -Encoding UTF8 -LiteralPath (Join-Path $configDir 'objective_integration_requirements.json') | ConvertFrom-Json
    foreach ($category in @('platforms', 'hazards', 'bonuses', 'npc_decor', 'ui_achievements', 'labels_signage', 'foreground_decor', 'background_decor')) {
        if (-not $objectiveReq.requiredCategories.$category) {
            Add-Error "objective_integration_requirements.json не содержит категорию: $category."
        }
    }
}

if (Test-Path -LiteralPath (Join-Path $configDir 'last_iteration_asset_manifest.generated.json')) {
    $lastIterationManifest = Get-Content -Raw -Encoding UTF8 -LiteralPath (Join-Path $configDir 'last_iteration_asset_manifest.generated.json') | ConvertFrom-Json
    if (-not $lastIterationManifest.validation.passed) {
        Add-Error "last_iteration_asset_manifest.generated.json не прошел встроенную валидацию."
    }
    if ([int]$lastIterationManifest.entryCount -lt 450) {
        Add-Error "last_iteration_asset_manifest.generated.json содержит слишком мало runtime-ассетов: $($lastIterationManifest.entryCount)."
    }
    foreach ($level in 1..15) {
        $levelKey = ('lvl{0:D2}' -f $level)
        $levelTypes = $lastIterationManifest.summary.byLevelAssetType.$levelKey
        if (-not $levelTypes.PlatformMain -or -not $levelTypes.PlatformAlt) {
            Add-Error "Новый themed manifest не содержит PlatformMain/PlatformAlt для $levelKey."
        }
    }
    if ($src -notmatch 'themedPlatformKeysForLevel' -or $src -notmatch 'themedObstacleKeysForType') {
        Add-Error "GameRoot.ts должен выбирать платформы и препятствия через themed-каталог necessary/9."
    }
}

if (Test-Path -LiteralPath (Join-Path $configDir 'visual_layer_contract.json')) {
    $visualContract = Get-Content -Raw -Encoding UTF8 -LiteralPath (Join-Path $configDir 'visual_layer_contract.json') | ConvertFrom-Json
    foreach ($layerName in @('far_background', 'background_signage', 'platforms', 'collectibles', 'player_body', 'equipment_front', 'hands_items', 'hazards', 'active_labels', 'hud', 'modal_overlay')) {
        if (-not ($visualContract.z_layers | Where-Object { $_.name -eq $layerName })) {
            Add-Error "visual_layer_contract.json не содержит z-layer: $layerName."
        }
    }
    if ($src -notmatch 'VISUAL_Z_LAYERS') {
        Add-Error "GameRoot.ts должен иметь runtime-константу VISUAL_Z_LAYERS."
    }
}

if (Test-Path -LiteralPath (Join-Path $configDir 'render_layer_contract.json')) {
    $renderContract = Get-Content -Raw -Encoding UTF8 -LiteralPath (Join-Path $configDir 'render_layer_contract.json') | ConvertFrom-Json
    foreach ($layerName in @('BG_FAR', 'BG_MID', 'BG_NEAR_DECOR', 'PLATFORMS_SOLID', 'OBJECTIVES_ACTIVE', 'COLLECTIBLES', 'PLAYER_BODY', 'PLAYER_EQUIPMENT', 'PLAYER_EFFECTS', 'FOREGROUND_LIGHT_DECOR', 'HUD', 'DEV_OVERLAY')) {
        if (-not ($renderContract.layers | Where-Object { $_.name -eq $layerName })) {
            Add-Error "render_layer_contract.json не содержит runtime-layer: $layerName."
        }
        if ($src -notmatch [regex]::Escape("'$layerName'")) {
            Add-Error "GameRoot.ts не содержит runtime-layer: $layerName."
        }
    }
}

if (Test-Path -LiteralPath (Join-Path $configDir 'equipment_anchor_contract.json')) {
    $equipmentContract = Get-Content -Raw -Encoding UTF8 -LiteralPath (Join-Path $configDir 'equipment_anchor_contract.json') | ConvertFrom-Json
    $anchorList = @()
    if ($equipmentContract.anchors_required) {
        $anchorList = @($equipmentContract.anchors_required)
    } elseif ($equipmentContract.anchors) {
        $anchorList = @($equipmentContract.anchors)
    }
    foreach ($anchorName in @('head_anchor', 'neck_anchor', 'torso_anchor', 'back_anchor', 'hand_r_anchor', 'hand_l_anchor', 'feet_anchor', 'aura_anchor')) {
        if (-not ($anchorList -contains $anchorName)) {
            Add-Error "equipment_anchor_contract.json не содержит anchor: $anchorName."
        }
    }
    foreach ($needle in @('equipmentAnchorPoint', 'MTR_EQUIPMENT_ATTACH')) {
        if (-not $src.Contains($needle)) {
            Add-Error "GameRoot.ts не содержит runtime-привязку экипировки: $needle."
        }
    }
    $runtimeAnchorMarkers = @{
        head_anchor = @("case 'head_anchor'", 'player_equipment_head_anchor')
        neck_anchor = @("case 'neck_anchor'", 'player_equipment_neck_anchor')
        torso_anchor = @("case 'torso_anchor'", 'player_equipment_torso_anchor')
        back_anchor = @("case 'back_anchor'", 'player_equipment_back_anchor')
        hand_r_anchor = @("case 'hand_r_anchor'", 'player_equipment_hand_r_anchor')
        hand_l_anchor = @("case 'hand_l_anchor'", 'player_equipment_hand_l_anchor')
        feet_anchor = @("case 'feet_anchor'", 'player_equipment_feet_anchor')
        aura_anchor = @("case 'aura_anchor'", 'player_equipment_aura_anchor')
    }
    foreach ($anchorName in @('head_anchor', 'neck_anchor', 'torso_anchor', 'back_anchor', 'hand_r_anchor', 'hand_l_anchor', 'feet_anchor', 'aura_anchor')) {
        $found = $false
        foreach ($marker in $runtimeAnchorMarkers[$anchorName]) {
            if ($src.Contains($marker)) {
                $found = $true
                break
            }
        }
        if (-not $found) {
            Add-Error "GameRoot.ts не содержит runtime-привязку экипировки: $anchorName."
        }
    }
} elseif (Test-Path -LiteralPath (Join-Path $configDir 'equipment_layer_contract.json')) {
    $equipmentContract = Get-Content -Raw -Encoding UTF8 -LiteralPath (Join-Path $configDir 'equipment_layer_contract.json') | ConvertFrom-Json
    foreach ($anchorName in @('head', 'torso_front', 'torso_back', 'right_hand', 'left_hand', 'feet', 'aura', 'ground_fx')) {
        if (-not $equipmentContract.anchors.$anchorName) {
            Add-Error "equipment_layer_contract.json не содержит anchor: $anchorName."
        }
    }
    foreach ($needle in @('equipmentAnchorPoint', 'MTR_EQUIPMENT_ATTACH')) {
        if (-not $src.Contains($needle)) {
            Add-Error "GameRoot.ts не содержит runtime-привязку экипировки: $needle."
        }
    }
}

if (Test-Path -LiteralPath (Join-Path $configDir 'achievement_ui_contract.json')) {
    $achievementUi = Get-Content -Raw -Encoding UTF8 -LiteralPath (Join-Path $configDir 'achievement_ui_contract.json') | ConvertFrom-Json
    if ([int]$achievementUi.card.min_height_px -lt 86 -or [int]$achievementUi.card.icon_size_px -lt 64) {
        Add-Error "achievement_ui_contract.json должен требовать card >= 86 px и icon >= 64 px."
    }
}

if (Test-Path -LiteralPath (Join-Path $configDir 'objective_attachment_rules.json')) {
    $attachRules = Get-Content -Raw -Encoding UTF8 -LiteralPath (Join-Path $configDir 'objective_attachment_rules.json') | ConvertFrom-Json
    foreach ($category in @('platforms', 'hazards', 'bonuses', 'npc_decor', 'ui_achievements', 'labels_signage', 'foreground_decor', 'background_decor')) {
        if (-not $attachRules.categories.$category) {
            Add-Error "objective_attachment_rules.json не содержит категорию: $category."
        }
    }
}

if (Test-Path -LiteralPath (Join-Path $configDir 'pause_touch_zone_contract.json')) {
    $pauseContract = Get-Content -Raw -Encoding UTF8 -LiteralPath (Join-Path $configDir 'pause_touch_zone_contract.json') | ConvertFrom-Json
    if ([int]$pauseContract.hitbox.width -lt 128 -or [int]$pauseContract.hitbox.height -lt 80) {
        Add-Error "Pause hitbox должен быть не меньше 128x80 virtual px."
    }
    if ($src -notmatch 'pauseTouchRect' -or $src -notmatch 'MTR_INPUT_PAUSE_TAP') {
        Add-Error "GameRoot.ts должен иметь pauseTouchRect и MTR_INPUT_PAUSE_TAP лог."
    }
}

if ($src -notmatch 'private\s+debugColliders\s*=\s*false') {
    Add-Error "debugColliders должен быть false по умолчанию в production gameplay."
}
if ($src -notmatch 'params\.get\(''debugColliders''\)\s*===\s*''true''') {
    Add-Error "debugColliders должен включаться только явным query-флагом debugColliders=true."
}
if ($src -notmatch 'private\s+debugReadability\s*=\s*false' -or $src -notmatch 'mtr_debug_readability') {
    Add-Error "Нужен debugReadability=false по умолчанию и query/localStorage флаг mtr_debug_readability."
}

for ($i = 1; $i -le 15; $i++) {
    $fileName = 'level{0:D2}.jpg' -f $i
    $backgroundPath = Join-Path $backgroundDir $fileName
    if (-not (Test-Path -LiteralPath $backgroundPath)) {
        Add-Error "Нет bitmap-фона уровня ${i}: $backgroundPath"
        continue
    }

    $file = Get-Item -LiteralPath $backgroundPath
    if ($file.Length -lt 50000) {
        Add-Error "Фон уровня ${i} слишком мал и похож на заглушку: $($file.Length) байт."
    }
}

if ($errors.Count -gt 0) {
    foreach ($e in $errors) { Write-Error $e }
    exit 1
}

Write-Host "MTR config OK: 15 levels, 15 bitmap backgrounds, story themes, current objective sprites, achievements and Russian labels present."

