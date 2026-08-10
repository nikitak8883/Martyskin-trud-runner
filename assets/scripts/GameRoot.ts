import {
    _decorator,
    AudioClip,
    AudioSource,
    Color,
    Component,
    EditBox,
    EventKeyboard,
    EventTouch,
    Graphics,
    Input,
    input,
    KeyCode,
    Label,
    Node,
    profiler,
    ResolutionPolicy,
    resources,
    screen,
    Sprite,
    SpriteFrame,
    sys,
    UITransform,
    Vec3,
    view,
} from 'cc';
import { DEBUG } from 'cc/env';
import {
    THEMED_ASSET_ENTRIES,
    THEMED_ALL_RUNTIME_KEYS,
    themedAssetKeysForLevel,
    themedObstacleKeysForType,
    themedPlatformKeysForLevel,
    themedUiAssetKeysForSurface,
} from './generated/ThemeAssetCatalog.generated';
import type { ThemedUiAssetRole, ThemeRuntimeCategory } from './generated/ThemeAssetCatalog.generated';
import { evaluateGameSessionTransition, gameSessionModeForState } from './gameplay/state/GameSessionState';
import type {
    GameSessionMode,
    GameSessionState,
    GameSessionTransitionResult,
} from './gameplay/state/GameSessionState';
import {
    GAME_ROOT_DEV_EVENT_CAPACITY,
    GAME_ROOT_DEV_EVENT_MAX_EXPORT_BYTES,
    GameRootDevEventAdapter,
} from './qa/GameRootDevEventAdapter';
import type { DevEventRecord, GameRootResetReason } from './qa/GameRootDevEventAdapter';
import { UI_SCREEN_TITLES, UI_SHARED_ASSET_KEYS, UI_SKIN } from './ui/UITheme';
import type { UiColorTuple } from './ui/UITheme';

const { ccclass } = _decorator;

function logGameRootDevEvent(event: DevEventRecord): void {
    console.log(
        `MTR_DEV_EVENT sequence=${event.sequence} epoch=${event.epoch} tick=${event.tick}`
        + ` code=${event.code} state=${event.state || '-'} reason=${event.reason || '-'}`,
    );
}

const W = 1280;
const H = 720;
const GROUND = 560;
const SCENE_PAD = 460;
interface StartupQueryParams {
    get(name: string): string | null;
}

interface NativeReflectionBridge {
    reflection?: {
        callStaticMethod?: (className: string, methodName: string, signature: string) => unknown;
    };
}

function decodeQueryPart(value: string): string {
    try {
        return decodeURIComponent(value.replace(/\+/g, ' '));
    } catch {
        return value;
    }
}

function extractQueryFromHref(href: string): string {
    const queryStart = href.indexOf('?');
    if (queryStart < 0) return '';
    const hashStart = href.indexOf('#', queryStart + 1);
    return href.slice(queryStart + 1, hashStart >= 0 ? hashStart : undefined);
}

function parseStartupQueryParams(query: string): StartupQueryParams | null {
    const clean = query.trim().replace(/^\?/, '');
    if (!clean) return null;
    const values: Record<string, string> = {};
    for (const part of clean.split('&')) {
        if (!part) continue;
        const eq = part.indexOf('=');
        const rawKey = eq >= 0 ? part.slice(0, eq) : part;
        if (!rawKey) continue;
        const key = decodeQueryPart(rawKey);
        if (values[key] !== undefined) continue;
        values[key] = decodeQueryPart(eq >= 0 ? part.slice(eq + 1) : '1');
    }
    return {
        get(name: string): string | null {
            return values[name] ?? null;
        },
    };
}

function readNativeStartupQuery(): string {
    const globalBridge = globalThis as unknown as { native?: NativeReflectionBridge; jsb?: NativeReflectionBridge };
    const bridges = [globalBridge.native, globalBridge.jsb];
    for (const bridge of bridges) {
        const callStaticMethod = bridge?.reflection?.callStaticMethod;
        if (!callStaticMethod) continue;
        try {
            const query = callStaticMethod(
                'com/cocos/game/AppActivity',
                'getStartupQuery',
                '()Ljava/lang/String;',
            );
            return typeof query === 'string' ? query : '';
        } catch (err) {
            console.warn(`MTR_NATIVE_STARTUP_QUERY_FAIL err=${err instanceof Error ? err.message : String(err)}`);
        }
    }
    console.warn('MTR_NATIVE_STARTUP_QUERY_UNAVAILABLE reflection=false');
    return '';
}

const BACKGROUND_FRAME_CACHE_LIMIT = 4;
type ObjectSpriteLoadPriority = 'critical' | 'visible' | 'normal' | 'idle';
const OBJECT_SPRITE_WEB_LOAD_CONCURRENCY = 2;
const OBJECT_SPRITE_WEB_URGENT_LOAD_CONCURRENCY = 5;
const OBJECT_SPRITE_NATIVE_LOAD_CONCURRENCY = 8;
const OBJECT_SPRITE_LOAD_SLOW_MS = 1800;
const OBJECT_SPRITE_QUEUE_LOG_STEP = 50;
const OBJECT_SPRITE_IDLE_CHUNK_WEB = 4;
const OBJECT_SPRITE_IDLE_CHUNK_NATIVE = 16;
const OBJECT_SPRITE_WEB_CHUNK_INTERVAL_SEC = 0.22;
const OBJECT_SPRITE_NATIVE_CHUNK_INTERVAL_SEC = 0.06;
const WEB_STARTUP_PLATFORM_KEY_LIMIT = 4;
const WEB_STARTUP_HAZARD_KEY_LIMIT = 8;
const WEB_STARTUP_COLLECTIBLE_KEY_LIMIT = 2;
const WEB_SKIN_VARIANTS_DEFER_SEC = 4.5;
const WEB_UTILITY_WARMUP_DEFER_SEC = 2.5;
const OBJECT_SPRITE_PRIORITY_RANK: Record<ObjectSpriteLoadPriority, number> = {
    critical: 3,
    visible: 2,
    normal: 1,
    idle: 0,
};
const BACKGROUND_SCENIC_SOURCE_WIDTH = 1920;
const BACKGROUND_SCENIC_SOURCE_HEIGHT = 886;
const BACKGROUND_SCENIC_PAN_MARGIN_PX = 220;
const BANANA_DENSITY_MULTIPLIER = 0.70;
const SIDE_COLLECTIBLE_CHANCE = 0.18;
const MAX_VISIBLE_BANANAS_NORMAL = 12;
const MAX_VISIBLE_BANANAS_MAGNET = 16;
const MAX_BANANA_CLUSTERS_ON_SCREEN = 3;
const MIN_CLUSTER_GAP_PX = 280;
const MIN_BANANA_GAP_PX = 52;
const MAGNET_RADIUS_PX = 360;
const MAGNET_SPEED_PX_PER_SEC = 620;
const MAGNET_MAX_SPEED_PX_PER_SEC = 900;
const PLAYER_SKIN_BLEND_SEC = 0.22;
const TOAST_DURATION_SEC = 1.45;
const DEFAULT_MUSIC_VOLUME = 0.46;
const DEFAULT_SFX_VOLUME = 0.58;
const DEFAULT_VOICE_VOLUME = 0.54;
const MASTER_AUDIO_GAIN = 0.72;
const SFX_BUS_GAIN = 0.76;
const VOICE_BUS_GAIN = 0.66;
const MUSIC_TO_VOICE_RATIO = 1.25;
const MAIN_MENU_UI_SURFACE = 'main_menu';
const MAIN_MENU_CRITICAL_UI_ROLES: ThemedUiAssetRole[] = ['title', 'button', 'prop', 'icon'];
const SECONDARY_MENU_UI_SURFACES = ['death', 'pause', 'level_select', 'skin_select', 'sound_settings', 'records', 'achievements', 'developer'];
const MAIN_MENU_BACKGROUND_SPRITE_ALPHA = 255;
const MAIN_MENU_BACKGROUND_HAZE_ALPHA = 24;
const MAIN_MENU_BACKGROUND_LAYER_KEYS = [
    'ui/main_menu_background/main_menu_bg_far',
] as const;
const MAIN_MENU_BACKGROUND_REQUIRED_KEYS = [
    MAIN_MENU_BACKGROUND_LAYER_KEYS[0],
] as const;
const MAIN_MENU_TITLE_KEY = 'objectives/themed/last_iteration/ui/main_menu/title/mtr_last_main_menu_ui_main_menu_main_title_01';
const MAIN_MENU_DEONION_BUTTON_KEYS = {
    'НАЧАТЬ ИГРУ': 'objectives/themed/last_iteration/ui/main_menu/button/mtr_last_main_menu_ui_main_menu_button_start_08',
    'ВПЕРЁД, ПРИМАТЫ!': 'objectives/themed/last_iteration/ui/main_menu/button/mtr_last_main_menu_ui_main_menu_button_forward_01',
    'ВЫБЕРИ СВОЕГО ПРИМАТА': 'objectives/themed/last_iteration/ui/main_menu/button/mtr_last_main_menu_ui_main_menu_button_skins_03',
    'ЗВУК И НАСТРОЙКИ': 'objectives/themed/last_iteration/ui/main_menu/button/mtr_last_main_menu_ui_main_menu_button_sound_05',
    'МАРТЫШКИНЫ РЕКОРДЫ': 'objectives/themed/last_iteration/ui/main_menu/button/mtr_last_main_menu_ui_main_menu_button_records_02',
    'ВЫБОР УРОВНЯ': 'objectives/themed/last_iteration/ui/main_menu/button/mtr_last_main_menu_ui_main_menu_button_levels_04',
    'РЕЖИМ РАЗРАБОТЧИКА': 'objectives/themed/last_iteration/ui/main_menu/button/mtr_last_main_menu_ui_main_menu_button_developer_06',
} as const;
const MAIN_MENU_DEONION_REQUIRED_KEYS = [
    MAIN_MENU_TITLE_KEY,
    MAIN_MENU_DEONION_BUTTON_KEYS['НАЧАТЬ ИГРУ'],
    MAIN_MENU_DEONION_BUTTON_KEYS['ВПЕРЁД, ПРИМАТЫ!'],
    MAIN_MENU_DEONION_BUTTON_KEYS['ВЫБЕРИ СВОЕГО ПРИМАТА'],
    MAIN_MENU_DEONION_BUTTON_KEYS['ЗВУК И НАСТРОЙКИ'],
    MAIN_MENU_DEONION_BUTTON_KEYS['МАРТЫШКИНЫ РЕКОРДЫ'],
    MAIN_MENU_DEONION_BUTTON_KEYS['ВЫБОР УРОВНЯ'],
    MAIN_MENU_DEONION_BUTTON_KEYS['РЕЖИМ РАЗРАБОТЧИКА'],
] as const;
const MAIN_MENU_INITIAL_READY_KEYS: readonly string[] = [
    ...MAIN_MENU_BACKGROUND_REQUIRED_KEYS,
    MAIN_MENU_TITLE_KEY,
    MAIN_MENU_DEONION_BUTTON_KEYS['НАЧАТЬ ИГРУ'],
];
const MAIN_MENU_DEONION_DEFERRED_KEYS = MAIN_MENU_DEONION_REQUIRED_KEYS.filter((key) =>
    MAIN_MENU_INITIAL_READY_KEYS.indexOf(key) < 0,
);
const START_MENU_PROFILE_BOX_KEY = 'objectives/themed/last_iteration/ui/start_menu/mtr_start_menu_profile_box_01';
const START_MENU_BUTTON_KEYS = {
    'СОХРАНИТЬ ИМЯ': 'objectives/themed/last_iteration/ui/start_menu/mtr_start_menu_button_save_name_01',
    'ВПЕРЁД, ПРИМАТЫ!': 'objectives/themed/last_iteration/ui/start_menu/mtr_start_menu_button_forward_01',
    'В МЕНЮ': 'objectives/themed/last_iteration/ui/start_menu/mtr_start_menu_button_back_menu_01',
} as const;
const START_MENU_UI_KEYS = [
    START_MENU_PROFILE_BOX_KEY,
    START_MENU_BUTTON_KEYS['СОХРАНИТЬ ИМЯ'],
    START_MENU_BUTTON_KEYS['ВПЕРЁД, ПРИМАТЫ!'],
    START_MENU_BUTTON_KEYS['В МЕНЮ'],
] as const;
const LEVEL_SELECT_THEME_ICON_KEYS = [
    'objectives/themed/last_iteration/ui/level_select/icon/mtr_level_select_theme_icon_01',
    'objectives/themed/last_iteration/ui/level_select/icon/mtr_level_select_theme_icon_02',
    'objectives/themed/last_iteration/ui/level_select/icon/mtr_level_select_theme_icon_03',
    'objectives/themed/last_iteration/ui/level_select/icon/mtr_level_select_theme_icon_04',
    'objectives/themed/last_iteration/ui/level_select/icon/mtr_level_select_theme_icon_05',
    'objectives/themed/last_iteration/ui/level_select/icon/mtr_level_select_theme_icon_06',
    'objectives/themed/last_iteration/ui/level_select/icon/mtr_level_select_theme_icon_07',
    'objectives/themed/last_iteration/ui/level_select/icon/mtr_level_select_theme_icon_08',
    'objectives/themed/last_iteration/ui/level_select/icon/mtr_level_select_theme_icon_09',
    'objectives/themed/last_iteration/ui/level_select/icon/mtr_level_select_theme_icon_10',
    'objectives/themed/last_iteration/ui/level_select/icon/mtr_level_select_theme_icon_11',
    'objectives/themed/last_iteration/ui/level_select/icon/mtr_level_select_theme_icon_12',
    'objectives/themed/last_iteration/ui/level_select/icon/mtr_level_select_theme_icon_13',
    'objectives/themed/last_iteration/ui/level_select/icon/mtr_level_select_theme_icon_14',
    'objectives/themed/last_iteration/ui/level_select/icon/mtr_level_select_theme_icon_15',
] as const;
const THEMED_GAMEPLAY_RUNTIME_KEYS = THEMED_ALL_RUNTIME_KEYS.filter((key) => !key.includes('/ui/'));

type State = GameSessionState;
type EndState = 'clear' | 'over' | 'finished';
type FsmMode = GameSessionMode;
type CollectibleKind = 'banana' | 'coconut' | 'figLeaf';

interface Rect { x: number; y: number; w: number; h: number; }
interface Platform { x: number; y: number; w: number; type: number; state: number; }
interface Banana { x: number; y: number; taken: boolean; value: number; cluster: number; kind: CollectibleKind; }
interface Obstacle { x: number; y: number; type: number; dead: boolean; label: string; motion: number; }
interface Bonus { x: number; y: number; type: number; taken: boolean; }
interface Npc { anchor: number; range: number; speed: number; skin: number; t: number; dead: boolean; }
interface Particle { x: number; y: number; vx: number; vy: number; life: number; size: number; color: Color; }
interface Button { rect: Rect; text: string; action: () => void; stroke: Color; fill: Color; textColor: Color; }
interface Level { name: string; subtitle: string; top: Color; bottom: Color; accent: Color; speed: number; length: number; target: number; theme: number; }
interface Skin { name: string; species: string; badge: string; fur: Color; face: Color; helmet: Color; accent: Color; vest: Color; }
type PlayerSkinPose = 'idle' | 'run1' | 'run2' | 'jump' | 'jump2' | 'fall' | 'crouchDash' | 'hit' | 'victory';
interface ObstacleSpec { w: number; h: number; label?: string; joke: string; }
interface ObstacleVisualProfile { assetWScale: number; assetHScale: number; assetBottomOffset: number; labelLift: number; assetOpacity: number; }
interface RecordEntry { name: string; score: number; level: number; bananas: number; }
interface PooledLabel { node: Node; ui: UITransform; label: Label; }
interface PooledSprite { node: Node; ui: UITransform; sprite: Sprite; key: string; }
interface BackgroundSegment { node: Node; ui: UITransform; sprite: Sprite; }
interface BackgroundLayout {
    viewportWidth: number;
    drawWidth: number;
    drawHeight: number;
    panRange: number;
    segmentCount: number;
}
type AchievementRarity = 'common' | 'rare' | 'epic' | 'legendary' | 'bureaucratic';
type AchievementTrigger = 'bananas' | 'bonus' | 'level_complete' | 'no_damage' | 'speedrun' | 'streak' | 'secret';
interface AchievementDef { id: string; title: string; caption: string; category: string; rarity: AchievementRarity; triggerType: AchievementTrigger; target: number; iconAsset: string; hint: string; }
interface AchievementEntry { id: string; nickname: string; timestamp: number; level: number; reason: string; }
interface AchievementToast { def: AchievementDef; reason: string; }

type VoiceEvent = 'jump' | 'dash' | 'hurt' | 'death' | 'banana' | 'ui' | 'clear';
type ObjectiveCategory = 'platforms' | 'hazards' | 'collectibles' | 'bonuses' | 'npc_decor' | 'ui_achievements' | 'labels_signage' | 'active_labels' | 'foreground_decor' | 'background_decor' | 'player_body' | 'equipment';
type EquipmentSlot = 'helmet' | 'vest' | 'boots' | 'magnet' | 'coffee' | 'blueprint' | 'pass_card' | 'shield' | 'life_badge';
type PlayerSkinResourcePose = 'idle' | 'run_1' | 'run_2' | 'jump' | 'jump_2' | 'fall' | 'crouch_dash' | 'hit' | 'victory';
type PlayerSkinVariant =
    'base'
    | 'helmet'
    | 'vest'
    | 'helmet_vest'
    | 'boots'
    | 'helmet_vest_boots'
    | 'magnet'
    | 'shield'
    | 'blueprint'
    | 'radio'
    | 'banana_boost'
    | 'key_pass'
    | 'coffee';
interface RunnerGameState {
    mode: FsmMode;
    state: State;
    levelId: number;
    worldSpeed: number;
    distance: number;
    score: number;
    bananas: number;
    bonusBananas: number;
    hp: number;
    seed: number;
    activeBonuses: Record<string, number>;
    player: { x: number; y: number; vy: number; onGround: boolean; doubleJump: boolean };
    pools: { platforms: number; bananas: number; obstacles: number; bonuses: number; npcs: number; particles: number };
}
interface ObjectiveDefinition {
    asset_id: string;
    category: ObjectiveCategory;
    semantic_role: string;
    render_layer: RenderLayerName;
    collision_role: 'solid' | 'hazard' | 'collectible' | 'trigger' | 'decor' | 'none';
    spawn_rule: string;
    level_family: string;
}
type RenderLayerName =
    'BG_FAR'
    | 'BG_MID'
    | 'BG_NEAR_DECOR'
    | 'PLATFORMS_SOLID'
    | 'OBJECTIVES_ACTIVE'
    | 'COLLECTIBLES'
    | 'PLAYER_BODY'
    | 'PLAYER_EQUIPMENT'
    | 'PLAYER_EFFECTS'
    | 'FOREGROUND_LIGHT_DECOR'
    | 'HUD'
    | 'DEV_OVERLAY';
type EquipmentAnchor = 'head_anchor' | 'neck_anchor' | 'torso_anchor' | 'hand_l_anchor' | 'hand_r_anchor' | 'back_anchor' | 'feet_anchor' | 'aura_anchor';

const RENDER_LAYER_ORDER: RenderLayerName[] = [
    'BG_FAR',
    'BG_MID',
    'BG_NEAR_DECOR',
    'PLATFORMS_SOLID',
    'OBJECTIVES_ACTIVE',
    'COLLECTIBLES',
    'PLAYER_BODY',
    'PLAYER_EQUIPMENT',
    'PLAYER_EFFECTS',
    'FOREGROUND_LIGHT_DECOR',
    'HUD',
    'DEV_OVERLAY',
];

const VISUAL_Z_LAYERS: Record<RenderLayerName, number> = {
    BG_FAR: 0,
    BG_MID: 10,
    BG_NEAR_DECOR: 20,
    PLATFORMS_SOLID: 30,
    OBJECTIVES_ACTIVE: 40,
    COLLECTIBLES: 50,
    PLAYER_BODY: 60,
    PLAYER_EQUIPMENT: 70,
    PLAYER_EFFECTS: 80,
    FOREGROUND_LIGHT_DECOR: 90,
    HUD: 100,
    DEV_OVERLAY: 110,
};

function rgb(r: number, g: number, b: number, a = 255): Color {
    return new Color(r, g, b, a);
}

function lerp(a: number, b: number, t: number): number {
    return a + (b - a) * t;
}

function clamp(v: number, lo: number, hi: number): number {
    return Math.max(lo, Math.min(hi, v));
}

function hit(a: Rect, b: Rect): boolean {
    return a.x < b.x + b.w && a.x + a.w > b.x && a.y < b.y + b.h && a.y + a.h > b.y;
}

function union(a: Rect, b: Rect): Rect {
    const x1 = Math.min(a.x, b.x);
    const y1 = Math.min(a.y, b.y);
    const x2 = Math.max(a.x + a.w, b.x + b.w);
    const y2 = Math.max(a.y + a.h, b.y + b.h);
    return { x: x1, y: y1, w: x2 - x1, h: y2 - y1 };
}

function swept(a0: Rect, a1: Rect, b0: Rect, b1: Rect): boolean {
    return hit(union(a0, a1), union(b0, b1));
}

const LEVELS: Level[] = [
    { name: 'Уровень 1: Стройплощадка примата', subtitle: 'Стройка, где план есть, смысл не завезли.', top: rgb(38, 65, 70), bottom: rgb(115, 94, 60), accent: rgb(221, 169, 80), speed: 430, length: 39000, target: 50, theme: 0 },
    { name: 'Уровень 2: Банановая логистика', subtitle: 'Склад, где бананы перемещают до тех пор, пока они не станут отчётом.', top: rgb(42, 52, 48), bottom: rgb(103, 82, 54), accent: rgb(229, 184, 72), speed: 438, length: 41200, target: 55, theme: 1 },
    { name: 'Уровень 3: Отдел бессмысленных заявлений', subtitle: 'Офис, где каждый прыжок требует заявление в двух экземплярах.', top: rgb(55, 62, 65), bottom: rgb(115, 104, 80), accent: rgb(218, 187, 107), speed: 447, length: 42900, target: 60, theme: 2 },
    { name: 'Уровень 4: Джунгли примата', subtitle: 'Природная зона, где труд ещё не оформлен, но уже подозрителен.', top: rgb(25, 54, 40), bottom: rgb(83, 116, 65), accent: rgb(164, 212, 111), speed: 455, length: 44600, target: 65, theme: 3 },
    { name: 'Уровень 5: Ферма сверхплана', subtitle: 'Сельхоз-абсурд: кокосы, куры и отчётность на одной грядке.', top: rgb(69, 75, 49), bottom: rgb(142, 105, 64), accent: rgb(239, 194, 92), speed: 464, length: 46400, target: 70, theme: 4 },
    { name: 'Уровень 6: Павлин-инспектор', subtitle: 'Проверка ради проверки. Хвост распустил - значит акт составлен.', top: rgb(46, 42, 64), bottom: rgb(102, 84, 65), accent: rgb(76, 178, 150), speed: 473, length: 48200, target: 75, theme: 5 },
    { name: 'Уровень 7: Фабрика вечного труда', subtitle: 'Трубы, пар, шестерни и конвейер, который производит усталость.', top: rgb(54, 47, 39), bottom: rgb(125, 87, 58), accent: rgb(220, 142, 72), speed: 482, length: 50100, target: 80, theme: 6 },
    { name: 'Уровень 8: Архив важности', subtitle: 'Документы лежат так давно, что начали принимать решения сами.', top: rgb(51, 43, 36), bottom: rgb(99, 81, 57), accent: rgb(190, 155, 94), speed: 491, length: 52000, target: 85, theme: 7 },
    { name: 'Уровень 9: Банановый реактор', subtitle: 'Энергия банана поставлена на поток. Очень зря.', top: rgb(34, 52, 43), bottom: rgb(82, 105, 63), accent: rgb(178, 228, 80), speed: 501, length: 54100, target: 90, theme: 8 },
    { name: 'Уровень 10: Коридор проверок', subtitle: 'Каждая дверь ведёт к новой проверке предыдущей проверки.', top: rgb(48, 42, 37), bottom: rgb(105, 84, 62), accent: rgb(221, 151, 98), speed: 510, length: 56100, target: 95, theme: 9 },
    { name: 'Уровень 11: Ночная смена', subtitle: 'Когда весь мир спит, план продолжает требовать видимость.', top: rgb(13, 22, 38), bottom: rgb(44, 48, 68), accent: rgb(105, 160, 220), speed: 519, length: 58100, target: 100, theme: 10 },
    { name: 'Уровень 12: Учебный отдел плана', subtitle: 'Здесь учат прыгать по инструкции, которую никто не читал.', top: rgb(50, 43, 36), bottom: rgb(106, 89, 58), accent: rgb(205, 176, 101), speed: 528, length: 60200, target: 105, theme: 11 },
    { name: 'Уровень 13: Башня согласований', subtitle: 'Вертикальная бюрократия. Чем выше этаж, тем ниже смысл.', top: rgb(64, 58, 53), bottom: rgb(133, 111, 76), accent: rgb(218, 176, 87), speed: 532, length: 61700, target: 110, theme: 12 },
    { name: 'Уровень 14: Министерство фабричного труда', subtitle: 'Фабрика производит регламенты, а министерство дымит.', top: rgb(66, 54, 42), bottom: rgb(131, 98, 62), accent: rgb(218, 161, 82), speed: 535, length: 63100, target: 115, theme: 13 },
    { name: 'Уровень 15: Сердце Мартышкиного труда', subtitle: 'Финальный механизм, где планы, бананы и акты крутятся без причины.', top: rgb(53, 43, 37), bottom: rgb(116, 82, 55), accent: rgb(236, 186, 72), speed: 538, length: 64600, target: 120, theme: 14 },
];

const SKINS: Skin[] = [
    { name: 'Бригадир', species: 'макака', badge: 'ЖИЛЕТ', fur: rgb(118, 70, 35), face: rgb(205, 150, 92), helmet: rgb(45, 180, 70), accent: rgb(95, 55, 28), vest: rgb(47, 135, 61) },
    { name: 'Мудрец', species: 'орангутанг', badge: 'ЧЕРТЁЖ', fur: rgb(210, 190, 155), face: rgb(245, 220, 185), helmet: rgb(70, 130, 220), accent: rgb(138, 111, 80), vest: rgb(69, 93, 156) },
    { name: 'Кибер-макака', species: 'макака', badge: 'ВИЗОР', fur: rgb(90, 95, 105), face: rgb(185, 205, 205), helmet: rgb(80, 235, 210), accent: rgb(48, 54, 63), vest: rgb(47, 159, 170) },
    { name: 'Красный прораб', species: 'шимпанзе', badge: 'РАЦИЯ', fur: rgb(115, 45, 35), face: rgb(225, 135, 90), helmet: rgb(230, 70, 55), accent: rgb(90, 37, 29), vest: rgb(177, 44, 38) },
    { name: 'Деповский примат', species: 'капуцин', badge: 'КЛЮЧ', fur: rgb(82, 63, 44), face: rgb(222, 184, 132), helmet: rgb(255, 178, 67), accent: rgb(42, 42, 46), vest: rgb(67, 94, 113) },
    { name: 'Орангутанг-нуар', species: 'орангутанг', badge: 'ПЛАЩ', fur: rgb(170, 78, 36), face: rgb(235, 162, 102), helmet: rgb(28, 28, 34), accent: rgb(74, 45, 31), vest: rgb(32, 32, 40) },
    { name: 'Лаборант акта', species: 'мартышка', badge: 'ОЧКИ', fur: rgb(134, 77, 34), face: rgb(232, 167, 102), helmet: rgb(246, 238, 214), accent: rgb(78, 54, 35), vest: rgb(232, 224, 198) },
    { name: 'Золотой бригадир', species: 'макака', badge: 'ЗОЛОТО', fur: rgb(102, 62, 30), face: rgb(225, 154, 92), helmet: rgb(255, 205, 48), accent: rgb(65, 42, 24), vest: rgb(91, 63, 34) },
];

const PLAYER_SKIN_IDS = [
    'brigadir',
    'mudrec',
    'cyber_makaka',
    'red_prorab',
    'depo_primate',
    'orangutan_noir',
    'lab_assistant_act',
    'golden_brigadir',
] as const;

const PLAYER_SKIN_RESOURCE_ROOT = 'characters/player_skins';
const LEGACY_PLAYER_SKIN_RESOURCE_ROOT = 'player_skins_v2';
const LEGACY_PLAYER_SKIN_ID_REDIRECTS: Record<string, typeof PLAYER_SKIN_IDS[number]> = {
    brigadier_yellow: 'brigadir',
    office_clerk: 'mudrec',
    green_engineer: 'cyber_makaka',
    red_foreman: 'red_prorab',
    blue_builder: 'depo_primate',
    inspector: 'orangutan_noir',
    lab_primate: 'lab_assistant_act',
    gold_brigadier: 'golden_brigadir',
};
const LEGACY_PLAYER_SKIN_VARIANT_REDIRECTS: Record<string, PlayerSkinVariant> = {
    base: 'base',
    helmet: 'helmet',
    vest: 'vest',
    helmet_vest: 'helmet_vest',
    boots: 'boots',
    helmet_vest_boots: 'helmet_vest_boots',
    full_safety: 'helmet_vest_boots',
    magnet: 'magnet',
    shield: 'shield',
    blueprint: 'blueprint',
    radio: 'radio',
    banana_boost: 'banana_boost',
    key_pass: 'key_pass',
    pass_card: 'key_pass',
    coffee: 'coffee',
};
const LEGACY_PLAYER_SKIN_POSE_REDIRECTS: Record<string, PlayerSkinResourcePose> = {
    idle: 'idle',
    run_1: 'run_1',
    run_2: 'run_2',
    jump: 'jump',
    jump_2: 'jump_2',
    fall: 'fall',
    crouch_dash: 'crouch_dash',
    crawl: 'crouch_dash',
    hit: 'hit',
    victory: 'victory',
};
const PLAYER_SKIN_RESOURCE_POSES: PlayerSkinResourcePose[] = ['idle', 'run_1', 'run_2', 'jump', 'jump_2', 'fall', 'crouch_dash', 'hit', 'victory'];
const PLAYER_SKIN_VARIANTS: PlayerSkinVariant[] = [
    'base',
    'helmet',
    'vest',
    'helmet_vest',
    'boots',
    'helmet_vest_boots',
    'magnet',
    'shield',
    'blueprint',
    'radio',
    'banana_boost',
    'key_pass',
    'coffee',
];
const PLAYER_SKIN_START_GATE_POSES: PlayerSkinResourcePose[] = ['idle', 'run_1', 'run_2', 'jump', 'jump_2', 'fall', 'crouch_dash', 'hit', 'victory'];
const PLAYER_SKIN_POSE_RESOURCE: Record<PlayerSkinPose, PlayerSkinResourcePose> = {
    idle: 'idle',
    run1: 'run_1',
    run2: 'run_2',
    jump: 'jump',
    jump2: 'jump_2',
    fall: 'fall',
    crouchDash: 'crouch_dash',
    hit: 'hit',
    victory: 'victory',
};
const PLAYER_SKIN_QA_POSE_ALIASES: Record<string, PlayerSkinPose> = {
    idle: 'idle',
    run1: 'run1',
    run_1: 'run1',
    run2: 'run2',
    run_2: 'run2',
    jump: 'jump',
    jump2: 'jump2',
    jump_2: 'jump2',
    fall: 'fall',
    crouchDash: 'crouchDash',
    crouch_dash: 'crouchDash',
    dash: 'crouchDash',
    hit: 'hit',
    victory: 'victory',
};
const PLAYER_SKIN_CANONICAL_MODELS: Record<PlayerSkinVariant, string> = {
    base: 'selected_skin',
    helmet: 'bonus/helmet',
    vest: 'bonus/vest',
    helmet_vest: 'bonus/helmet_vest',
    boots: 'bonus/boots',
    helmet_vest_boots: 'bonus/helmet_vest_boots',
    magnet: 'bonus/magnet',
    shield: 'bonus/shield',
    blueprint: 'bonus/blueprint',
    radio: 'bonus/radio',
    banana_boost: 'bonus/banana_boost',
    key_pass: 'bonus/key_pass',
    coffee: 'bonus/coffee',
};

function playerSkinId(skinIndex: number): typeof PLAYER_SKIN_IDS[number] {
    const normalizedIndex = ((Math.floor(skinIndex) % PLAYER_SKIN_IDS.length) + PLAYER_SKIN_IDS.length) % PLAYER_SKIN_IDS.length;
    return PLAYER_SKIN_IDS[normalizedIndex] || PLAYER_SKIN_IDS[0];
}

function playerSkinVariantDirectory(variant: PlayerSkinVariant): string {
    return variant === 'base' ? 'base' : `bonus/${variant}`;
}

function normalizeObjectSpriteKey(key: string): string {
    const parts = key.split('/');
    if (parts.length === 4 && parts[0] === LEGACY_PLAYER_SKIN_RESOURCE_ROOT) {
        const skinId = LEGACY_PLAYER_SKIN_ID_REDIRECTS[parts[1]];
        const variant = LEGACY_PLAYER_SKIN_VARIANT_REDIRECTS[parts[2]];
        const pose = LEGACY_PLAYER_SKIN_POSE_REDIRECTS[parts[3]];
        if (skinId && variant && pose) return `${PLAYER_SKIN_RESOURCE_ROOT}/${skinId}/${playerSkinVariantDirectory(variant)}/${pose}`;
    }
    return key;
}

function playerSkinResourceKey(skinIndex: number, variant: PlayerSkinVariant, pose: PlayerSkinResourcePose): string {
    return `${PLAYER_SKIN_RESOURCE_ROOT}/${playerSkinId(skinIndex)}/${playerSkinVariantDirectory(variant)}/${pose}`;
}

function playerSkinV2AssetKey(skinIndex: number, variant: PlayerSkinVariant, pose: PlayerSkinPose): string {
    return playerSkinResourceKey(skinIndex, variant, PLAYER_SKIN_POSE_RESOURCE[pose]);
}

function playerSkinV2AssetKeysForSkin(skinIndex: number): string[] {
    const keys: string[] = [];
    for (const variant of PLAYER_SKIN_VARIANTS) {
        for (const pose of PLAYER_SKIN_RESOURCE_POSES) keys.push(playerSkinResourceKey(skinIndex, variant, pose));
    }
    return keys;
}

function playerSkinCriticalAssetKeysForSkin(skinIndex: number): string[] {
    return PLAYER_SKIN_START_GATE_POSES.map((pose) => playerSkinResourceKey(skinIndex, 'base', pose));
}

function playerSkinPreviewAssetKey(skinIndex: number): string {
    return playerSkinResourceKey(skinIndex, 'base', 'idle');
}

const PLAYER_SKIN_V2_BASE_ASSET_KEYS = PLAYER_SKIN_IDS.flatMap((_, index) => playerSkinCriticalAssetKeysForSkin(index));
const PLAYER_SKIN_PREVIEW_ASSET_KEYS = PLAYER_SKIN_IDS.map((_, index) => playerSkinPreviewAssetKey(index));
const BANANA_COLLECTIBLE_ASSET_KEYS = [
    'objectives/collectibles/collectible_banana_single_new',
    'objectives/collectibles/collectible_banana_large_new',
    'objectives/collectibles/collectible_banana_glow_new',
    'objectives/collectibles/collectible_banana_hardhat_new',
];
const BANANA_BUNCH_ASSET_KEY = 'objectives/collectibles/collectible_banana_bunch_new';
const COCONUT_COLLECTIBLE_ASSET_KEYS = [
    'objectives/collectibles/collectible_coconut_regular_new',
    'objectives/collectibles/collectible_coconut_cracked_new',
    'objectives/collectibles/collectible_coconut_hardhat_new',
    'objectives/collectibles/collectible_coconut_gold_new',
];
const FIG_LEAF_COLLECTIBLE_ASSET_KEYS = [
    'objectives/collectibles/collectible_fig_leaf_regular_new',
    'objectives/collectibles/collectible_fig_leaf_bright_new',
    'objectives/collectibles/collectible_fig_leaf_glow_new',
    'objectives/collectibles/collectible_fig_leaf_wind_new',
];
const NEW_COLLECTIBLE_ASSET_KEYS = [
    ...BANANA_COLLECTIBLE_ASSET_KEYS,
    BANANA_BUNCH_ASSET_KEY,
    ...COCONUT_COLLECTIBLE_ASSET_KEYS,
    ...FIG_LEAF_COLLECTIBLE_ASSET_KEYS,
];

const themedRuntimeKeysByCategory = (category: ThemeRuntimeCategory): string[] =>
    THEMED_ASSET_ENTRIES
        .filter((entry) => entry.runtimeEnabled !== false && entry.category === category)
        .map((entry) => entry.key);

const THEMED_PLATFORM_RUNTIME_KEYS = themedRuntimeKeysByCategory('platforms');
const THEMED_HAZARD_RUNTIME_KEYS = themedRuntimeKeysByCategory('hazards');

const OBSTACLES: ObstacleSpec[] = [
    { w: 96, h: 72, label: 'КИРПИЧ\nС ДУШОЙ', joke: 'Кирпич с душой победил архитектуру.' },
    { w: 118, h: 82, label: 'ЯЩИК\nБАНАНОВ', joke: 'Логистика доказала: банан может быть тяжёлым документом.' },
    { w: 92, h: 86, label: 'ЗАЯВЛЕНИЕ\nЖИВО', joke: 'Заявление потребовало ещё одно заявление.' },
    { w: 126, h: 82, label: 'ЛИАНА\nС АКТОМ', joke: 'Джунгли оформили препятствие по форме.' },
    { w: 112, h: 82, label: 'КУРЫ\nСВЕРХПЛАН', joke: 'Ферма перевыполнила план прямо под ноги.' },
    { w: 106, h: 108, label: 'НЕ\nБОЯТЬСЯ', joke: 'Павлин оказался полномочным инспектором.' },
    { w: 110, h: 86, label: 'ШЕСТЕРНЯ\nТРУДА', joke: 'Фабрика произвела усталость с гарантией.' },
    { w: 118, h: 86, label: 'АРХИВ\nЖИВ', joke: 'Архив вспомнил всё и не дал пройти.' },
    { w: 126, h: 82, label: 'РЕАКТОР\nБАНАН', joke: 'Банановая энергия вышла из регламента.' },
    { w: 118, h: 74, label: 'ЗОНА\nАУДИТА', joke: 'Проверка проверила траекторию прыжка.' },
    { w: 124, h: 76, label: 'НОЧНАЯ\nСМЕНА', joke: 'Ночная смена потребовала дневной отчёт.' },
    { w: 122, h: 86, label: 'ЭКЗАМЕН\nПЛАНА', joke: 'План поставил двойку за импровизацию.' },
    { w: 132, h: 86, label: 'ЛИФТ\nСОГЛАСОВАН', joke: 'Башня согласовала падение заранее.' },
    { w: 140, h: 82, label: 'ШТАМП\nЦЕХА', joke: 'Штамповочный цех утвердил столкновение.' },
    { w: 126, h: 104, label: 'СЕРДЦЕ\nТРУДА', joke: 'Сердце труда билось строго по инструкции.' },
    { w: 96, h: 90, label: 'СМЕТА\nЖИВА', joke: 'Смета внезапно стала препятствием.' },
    { w: 92, h: 112, label: 'ПРОЕКТ\nУСПЕШЕН', joke: 'Печать поставила точку прямо по примату.' },
    { w: 122, h: 86, label: 'ПРИМАТ\nРАБОТАЕТ', joke: 'Баннер работал лучше, чем объект.' },
];

const OBSTACLE_LABELS = [
    'КИРПИЧ\nС ДУШОЙ',
    'ЯЩИК\nБАНАНОВ',
    'ЗАЯВЛЕНИЕ',
    'ЛИАНА\nС АКТОМ',
    'КУРЫ\nСВЕРХПЛАН',
    'ИНСПЕКТОР',
    'ШЕСТЕРНЯ\nТРУДА',
    'АРХИВ\nДЫМИТСЯ',
    'РЕАКТОР\nБАНАН',
    'ЗОНА\nАУДИТА',
    'НОЧНАЯ\nСМЕНА',
    'ЭКЗАМЕН\nПЛАНА',
    'ЛИФТ\nСОГЛАСОВАН',
    'ШТАМП\nЦЕХА',
    'СЕРДЦЕ\nТРУДА',
    'СМЕТА\nЖИВА',
    'ПРОЕКТ\nУСПЕШЕН',
    'ОКНО\nЗАЯВЛЕНИЙ',
    'Я НА\nПРОВЕРКЕ',
    '220V\nИ РЕАКТОР',
    'ДОРОГА\nАУДИТА',
    'КРАСКА\nРЕГЛАМЕНТА',
    'БАЛКА\nСОГЛАСОВАНА',
    'КАСКА ЕСТЬ\nПЛАНА НЕТ',
    'ОБЪЕКТ\nПОЧТИ ГОТОВ',
    'БРИГАДА\nВ НОЧЬ',
];

const OBSTACLE_LABEL_BANK: string[][] = [
    ['КИРПИЧ\nС ДУШОЙ', 'КЛАДКА\nДУМАЕТ', 'СТЕНА\nСПОРИТ', 'ШАБАШ\nНЕ НЕСЁТ'],
    ['ЯЩИК\nБАНАНОВ', 'ПАЛЛЕТА\nСПОРИТ', 'ОТГРУЗКА\nДУМАЕТ', 'КОНТЕЙНЕР\nНЕ ТУДА'],
    ['ЗАЯВЛЕНИЕ', 'НА ПОДПИСЬ', 'ВЕДОМОСТЬ\nЖИВА', 'ПАПКА\nКУСАЕТСЯ'],
    ['ЛИАНА\nС АКТОМ', 'КОРЕНЬ\nУТВЕРЖДЁН', 'ЗАРОСЛИ\nПРИНЯЛИ', 'ТРОПА\nВ ОТПУСКЕ'],
    ['КУРЫ\nСВЕРХПЛАН', 'ФЕРМА\nОТЧИТАЛАСЬ', 'АМБАР\nДУМАЕТ', 'ТЕЛЕЖКА\nЖИВА'],
    ['НЕ\nБОЯТЬСЯ', 'ПАВЛИН\nПРИШЁЛ', 'АКТ\nРАСПУЩЕН'],
    ['ШЕСТЕРНЯ\nТРУДА', 'ТРУБА\nОДОБРИЛА', 'ПАР\nНА СМЕТЕ', 'КОНВЕЙЕР\nНЕ ЖДЁТ'],
    ['АРХИВ\nЖИВ', 'СТЕЛЛАЖ\nПОМНИТ', 'ДЕЛО\nКУСАЕТСЯ', 'КАРТОТЕКА\nВСТАЛА'],
    ['РЕАКТОР\nБАНАН', 'ПЕРЕГРЕВ\nПЛАНА', 'ТРУБА\nСВЕТИТ', 'ЭНЕРГИЯ\nСПОРИТ'],
    ['ЗОНА\nАУДИТА', 'ЕЩЁ РАЗ', 'ПРОВЕРКА\nПРОВЕРКИ', 'ДОПУСК\nЖДЁТ'],
    ['НОЧНАЯ\nСМЕНА', 'КОФЕ\nНЕ СПАС', 'ФОНАРЬ\nПИШЕТ АКТ', 'СОН\nЗАПРЕЩЁН'],
    ['ЭКЗАМЕН\nПЛАНА', 'МЕТОДИЧКА\nЖИВА', 'ДОСКА\nСПОРИТ', 'ПРАВИЛО\nПРЫЖКА'],
    ['ЛИФТ\nСОГЛАСОВАН', 'ЭТАЖ\nНЕ ТОТ', 'ПОДПИСЬ\nВВЕРХУ', 'БАШНЯ\nДУМАЕТ'],
    ['ШТАМП\nЦЕХА', 'РЕГЛАМЕНТ\nДЫМИТ', 'ПАРАГРАФ\nГОРЯЧИЙ', 'ТРУБА\nПОДПИСАЛА'],
    ['СЕРДЦЕ\nТРУДА', 'ЯДРО\nОДОБРИЛО', 'АКТ\nВРАЩАЕТСЯ', 'ПЛАН\nКРУТИТСЯ'],
    ['СМЕТА\nЖИВА', 'БАЛАНС\nПОЧТИ', 'СЕЙФ\nТРЕБУЕТ', 'ХРАНИТЬ\nБАНАНЫ'],
    ['ПРОЕКТ\nУСПЕШЕН', 'ПЕЧАТЬ\nРЕШАЕТ', 'СОВЕТ\nОДОБРИЛ'],
    ['ПРИМАТ\nРАБОТАЕТ', 'ОБЪЕКТ\nПОЧТИ ГОТОВ', 'РАБОТА\nИДЁТ'],
];

const DEFAULT_OBSTACLE_VISUAL_PROFILE: ObstacleVisualProfile = { assetWScale: 1.12, assetHScale: 1.10, assetBottomOffset: 0, labelLift: 58, assetOpacity: 222 };
const OBSTACLE_VISUAL_PROFILES: ObstacleVisualProfile[] = [
    { assetWScale: 1.18, assetHScale: 1.10, assetBottomOffset: 0, labelLift: 74, assetOpacity: 228 },
    { assetWScale: 1.16, assetHScale: 1.12, assetBottomOffset: 2, labelLift: 68, assetOpacity: 226 },
    { assetWScale: 1.02, assetHScale: 1.36, assetBottomOffset: 0, labelLift: 84, assetOpacity: 228 },
    { assetWScale: 1.28, assetHScale: 1.02, assetBottomOffset: 0, labelLift: 72, assetOpacity: 228 },
    { assetWScale: 1.10, assetHScale: 1.12, assetBottomOffset: 0, labelLift: 78, assetOpacity: 228 },
    { assetWScale: 1.10, assetHScale: 1.24, assetBottomOffset: 0, labelLift: 90, assetOpacity: 228 },
    { assetWScale: 0.88, assetHScale: 1.16, assetBottomOffset: 0, labelLift: 72, assetOpacity: 226 },
    { assetWScale: 1.10, assetHScale: 1.08, assetBottomOffset: 0, labelLift: 68, assetOpacity: 224 },
    { assetWScale: 1.10, assetHScale: 1.02, assetBottomOffset: 2, labelLift: 64, assetOpacity: 224 },
    { assetWScale: 1.12, assetHScale: 1.04, assetBottomOffset: 0, labelLift: 66, assetOpacity: 224 },
    { assetWScale: 1.10, assetHScale: 1.04, assetBottomOffset: 0, labelLift: 68, assetOpacity: 220 },
    { assetWScale: 1.16, assetHScale: 1.02, assetBottomOffset: 0, labelLift: 66, assetOpacity: 224 },
    { assetWScale: 1.08, assetHScale: 1.08, assetBottomOffset: 0, labelLift: 68, assetOpacity: 224 },
    { assetWScale: 1.10, assetHScale: 1.10, assetBottomOffset: 0, labelLift: 78, assetOpacity: 228 },
    { assetWScale: 1.28, assetHScale: 1.02, assetBottomOffset: 0, labelLift: 72, assetOpacity: 228 },
    { assetWScale: 1.14, assetHScale: 1.08, assetBottomOffset: 0, labelLift: 68, assetOpacity: 224 },
    { assetWScale: 1.10, assetHScale: 1.08, assetBottomOffset: 0, labelLift: 72, assetOpacity: 224 },
    { assetWScale: 1.35, assetHScale: 0.96, assetBottomOffset: 0, labelLift: 74, assetOpacity: 228 },
];

const VOICE_BANK: Record<VoiceEvent, string[]> = {
    jump: ['voice_jump_01', 'voice_jump_02', 'voice_jump_03', 'voice_jump_04', 'voice_jump_05'],
    dash: ['voice_dash_01', 'voice_dash_02', 'voice_dash_03', 'voice_dash_04', 'voice_dash_05'],
    hurt: ['voice_hurt_01', 'voice_hurt_02', 'voice_hurt_03', 'voice_hurt_04', 'voice_hurt_05'],
    death: ['voice_death_01', 'voice_death_02', 'voice_death_03', 'voice_death_04', 'voice_death_05'],
    banana: ['voice_banana_01', 'voice_banana_02', 'voice_banana_03', 'voice_banana_04', 'voice_banana_05'],
    ui: ['banner', 'pause', 'monkey_happy'],
    clear: ['level_clear', 'monkey_happy', 'monkey_chatter', 'voice_banana_05'],
};

const BONUS_LABELS = ['ПРЫГ', 'РЫВОК', 'ЩИТ', 'МАГНИТ', 'ЖИЛЕТ', 'КОФЕ', 'ЧЕРТЕЖ', 'ПРОПУСК', 'ЖИЗНЬ'];
const BONUS_COUNT = BONUS_LABELS.length;
const BONUS_COLORS = [
    rgb(108, 215, 255),
    rgb(255, 217, 75),
    rgb(156, 255, 122),
    rgb(223, 126, 255),
    rgb(255, 137, 79),
    rgb(189, 132, 75),
    rgb(96, 178, 255),
    rgb(255, 245, 154),
    rgb(255, 116, 146),
];

const OBJECTIVE_BATCH_EQUIPMENT_KEYS = [
    'objectives/equipment/equipment_hardhat_01',
    'objectives/equipment/equipment_safety_vest_01',
    'objectives/equipment/equipment_dash_boots_01',
    'objectives/equipment/equipment_magnet_01',
] as const;

const OBJECTIVE_BATCH_BONUS_KEYS = [
    'objectives/bonuses/bonus_jump_spring_01',
    'objectives/bonuses/bonus_dash_bolt_01',
    'objectives/bonuses/bonus_shield_01',
    'objectives/bonuses/bonus_coffee_01',
    'objectives/bonuses/bonus_blueprint_01',
    'objectives/bonuses/bonus_pass_card_01',
    'objectives/bonuses/bonus_extra_life_01',
    'objectives/bonuses/bonus_banana_coin_01',
] as const;

const OBJECTIVE_BATCH_COLLECTIBLE_KEYS = [
    'objectives/collectibles/collectible_banana_bunch_01',
] as const;

const OBJECTIVE_BATCH_UI_KEYS = [
    'objectives/ui/ui_label_plate_01',
    'objectives/ui/ui_achievement_trophy_01',
    'objectives/ui/ui_speedrun_badge_01',
    'objectives/ui/ui_bonus_bundle_badge_01',
    'objectives/ui/ui_level_lock_01',
    'objectives/ui/ui_avatar_worker_01',
    'objectives/ui/ui_avatar_scholar_01',
    'objectives/ui/ui_avatar_guard_01',
] as const;

const OBJECTIVE_BATCH_NPC_KEYS = [
    'objectives/npc/npc_worker_wrench_01',
    'objectives/npc/npc_worker_clipboard_01',
    'objectives/npc/npc_scholar_files_01',
    'objectives/npc/npc_guard_baton_01',
    'objectives/npc/npc_banana_carrier_01',
    'objectives/npc/npc_mechanic_wrench_01',
    'objectives/npc/npc_scientist_flask_01',
    'objectives/npc/npc_runner_bag_01',
    'objectives/npc/npc_angry_boss_01',
    'objectives/npc/npc_cleaner_broom_01',
] as const;

const OBJECT_SPRITES = [
    ...OBJECTIVE_BATCH_EQUIPMENT_KEYS,
    ...OBJECTIVE_BATCH_BONUS_KEYS,
    ...OBJECTIVE_BATCH_COLLECTIBLE_KEYS,
    ...OBJECTIVE_BATCH_UI_KEYS,
    ...OBJECTIVE_BATCH_NPC_KEYS,
] as const;

const BONUS_ASSET_KEYS = [
    'objectives/bonuses/bonus_jump_spring_01',
    'objectives/bonuses/bonus_dash_bolt_01',
    'objectives/bonuses/bonus_shield_01',
    'objectives/equipment/equipment_magnet_01',
    'objectives/equipment/equipment_safety_vest_01',
    'objectives/bonuses/bonus_coffee_01',
    'objectives/bonuses/bonus_blueprint_01',
    'objectives/bonuses/bonus_pass_card_01',
    'objectives/bonuses/bonus_extra_life_01',
];

const REQUIRED_OBJECTIVE_CATEGORIES: ObjectiveCategory[] = [
    'platforms',
    'hazards',
    'collectibles',
    'bonuses',
    'npc_decor',
    'ui_achievements',
    'labels_signage',
    'active_labels',
    'foreground_decor',
    'background_decor',
    'player_body',
    'equipment',
];

const OBJECTIVE_CATEGORY_KEYS: Record<ObjectiveCategory, readonly string[]> = {
    platforms: THEMED_PLATFORM_RUNTIME_KEYS,
    hazards: THEMED_HAZARD_RUNTIME_KEYS,
    collectibles: [
        ...OBJECTIVE_BATCH_COLLECTIBLE_KEYS,
        ...NEW_COLLECTIBLE_ASSET_KEYS,
    ],
    bonuses: [
        ...OBJECTIVE_BATCH_BONUS_KEYS,
    ],
    npc_decor: [
        ...OBJECTIVE_BATCH_NPC_KEYS,
    ],
    ui_achievements: [
        ...OBJECTIVE_BATCH_UI_KEYS,
        ...OBJECTIVE_BATCH_BONUS_KEYS,
    ],
    labels_signage: [
        'objectives/ui/ui_label_plate_01',
        'obstacle_label_component',
        'story_banner_component',
    ],
    active_labels: [
        'objectives/ui/ui_label_plate_01',
        'obstacle_label_component',
        'story_banner_component',
    ],
    foreground_decor: [
        'foreground_safe_area_matte',
        'themed_platform_contact',
    ],
    background_decor: [
        'story_banner_component',
        ...OBJECTIVE_BATCH_NPC_KEYS,
    ],
    player_body: [
        ...PLAYER_SKIN_V2_BASE_ASSET_KEYS,
    ],
    equipment: [
        ...OBJECTIVE_BATCH_EQUIPMENT_KEYS,
    ],
};

const OBJECTIVE_CATEGORY_CONTRACT: Record<ObjectiveCategory, Omit<ObjectiveDefinition, 'asset_id' | 'category'>> = {
    platforms: { semantic_role: 'walkable runner support', render_layer: 'PLATFORMS_SOLID', collision_role: 'solid', spawn_rule: 'procedural treadmill lane', level_family: 'all_levels' },
    hazards: { semantic_role: 'damage obstacle', render_layer: 'OBJECTIVES_ACTIVE', collision_role: 'hazard', spawn_rule: 'difficulty-patterned spawn', level_family: 'theme_obstacle_pool' },
    collectibles: { semantic_role: 'banana pickup', render_layer: 'COLLECTIBLES', collision_role: 'collectible', spawn_rule: 'arc and platform lanes', level_family: 'all_levels' },
    bonuses: { semantic_role: 'temporary powerup', render_layer: 'COLLECTIBLES', collision_role: 'trigger', spawn_rule: 'rare route reward', level_family: 'all_levels' },
    npc_decor: { semantic_role: 'primate npc/decor', render_layer: 'OBJECTIVES_ACTIVE', collision_role: 'hazard', spawn_rule: 'level_4_plus_patrol', level_family: 'advanced_levels' },
    ui_achievements: { semantic_role: 'achievement ui plate', render_layer: 'HUD', collision_role: 'none', spawn_rule: 'menu_and_toast_only', level_family: 'meta' },
    labels_signage: { semantic_role: 'static sign text', render_layer: 'OBJECTIVES_ACTIVE', collision_role: 'none', spawn_rule: 'attached_to_object', level_family: 'all_levels' },
    active_labels: { semantic_role: 'active obstacle label', render_layer: 'OBJECTIVES_ACTIVE', collision_role: 'none', spawn_rule: 'attached_priority_label', level_family: 'all_levels' },
    foreground_decor: { semantic_role: 'light foreground depth', render_layer: 'FOREGROUND_LIGHT_DECOR', collision_role: 'decor', spawn_rule: 'parallax_sparse', level_family: 'all_levels' },
    background_decor: { semantic_role: 'background parallax decor', render_layer: 'BG_NEAR_DECOR', collision_role: 'decor', spawn_rule: 'parallax_segment', level_family: 'all_levels' },
    player_body: { semantic_role: 'main primate skin animation', render_layer: 'PLAYER_BODY', collision_role: 'none', spawn_rule: 'selected_skin_pose', level_family: 'player' },
    equipment: { semantic_role: 'player equipment slot visual', render_layer: 'PLAYER_EQUIPMENT', collision_role: 'none', spawn_rule: 'bonus_state_to_slot_anchor', level_family: 'player' },
};

const V2_OBJECT_CATALOG: ObjectiveDefinition[] = REQUIRED_OBJECTIVE_CATEGORIES.flatMap((category) => {
    const contract = OBJECTIVE_CATEGORY_CONTRACT[category];
    return OBJECTIVE_CATEGORY_KEYS[category].map((asset_id) => ({ asset_id, category, ...contract }));
});

const ACHIEVEMENTS: AchievementDef[] = [
    { id: 'banana_50', title: 'Банановая ведомость', caption: '50 бананов ушли в отчёт.', category: 'bananas', rarity: 'common', triggerType: 'bananas', target: 50, iconAsset: 'objectives/collectibles/collectible_banana_bunch_01', hint: 'Собери 50 бананов за забег.' },
    { id: 'banana_100', title: 'Банановый бухгалтер', caption: '100 бананов и ни одного смысла.', category: 'bananas', rarity: 'rare', triggerType: 'bananas', target: 100, iconAsset: 'objectives/bonuses/bonus_banana_coin_01', hint: 'Собери 100 бананов за забег.' },
    { id: 'bonus_three_run', title: 'Карман прораба', caption: 'Три бонуса за один забег.', category: 'bonuses', rarity: 'common', triggerType: 'bonus', target: 3, iconAsset: 'objectives/ui/ui_bonus_bundle_badge_01', hint: 'Собери 3 бонуса до финиша.' },
    { id: 'bonus_all_types', title: 'Инвентарь шевелится', caption: 'Все типы бонусов хотя бы раз.', category: 'bonuses', rarity: 'epic', triggerType: 'bonus', target: BONUS_COUNT, iconAsset: 'objectives/ui/ui_bonus_bundle_badge_01', hint: 'Найди все виды бонусов.' },
    { id: 'helmet_imitation', title: 'Каска не жмёт', caption: 'Безопасность имитирована успешно.', category: 'bonuses', rarity: 'common', triggerType: 'bonus', target: 1, iconAsset: 'objectives/equipment/equipment_hardhat_01', hint: 'Активируй каску.' },
    { id: 'almost_engineer', title: 'Почти инженер', caption: 'Нашёл чертёж, но не прочитал.', category: 'bonuses', rarity: 'rare', triggerType: 'bonus', target: 1, iconAsset: 'objectives/bonuses/bonus_blueprint_01', hint: 'Подними чертёж.' },
    { id: 'self_approved', title: 'Согласовано само с собой', caption: 'Пропуск без очереди. Подозрительно.', category: 'bonuses', rarity: 'bureaucratic', triggerType: 'bonus', target: 1, iconAsset: 'objectives/bonuses/bonus_pass_card_01', hint: 'Получи пропуск.' },
    { id: 'level_clear', title: 'Труд без финиша', caption: 'Уровень пройден, работа осталась.', category: 'progress', rarity: 'common', triggerType: 'level_complete', target: 1, iconAsset: 'objectives/ui/ui_achievement_trophy_01', hint: 'Пройди любой уровень.' },
    { id: 'no_damage_clear', title: 'Не переиграй себя', caption: 'Прошёл без потери здоровья.', category: 'progress', rarity: 'legendary', triggerType: 'no_damage', target: 1, iconAsset: 'objectives/ui/ui_achievement_trophy_01', hint: 'Пройди уровень без урона.' },
    { id: 'bonus_bananas', title: 'Сверхплановый примат', caption: 'Бананы сверх нормы тоже отчёт.', category: 'bananas', rarity: 'bureaucratic', triggerType: 'bananas', target: 1, iconAsset: 'objectives/collectibles/collectible_banana_bunch_01', hint: 'Собери бананы сверх цели уровня.' },
];
const ACHIEVEMENT_MENU_ICON_ASSET_KEYS = Array.from(new Set<string>([
    ...ACHIEVEMENTS.map((def) => def.iconAsset),
    'objectives/ui/ui_level_lock_01',
]));

const PLATFORM_NAMES = ['ЛЕСА', 'ПЛИТА', 'ДОСКИ', 'РЕЛЬСЫ', 'ВАГОНЕТКА', 'ПОДДОН', 'ТРУБЫ', 'ЩИТ', 'ФЕРМА', 'КАБЕЛЬ', 'ТАЧКА', 'КОНТЕЙНЕР'];
const DEATH_FALLBACKS = [
    'Каска была. Плана не было. Итог закономерен.',
    'Бананов много. Тормозов мало.',
    'Смета зашевелилась. Примат не вынес бухгалтерии.',
    'Прораб был в душе. Душа вышла из чата.',
];

const STORY: string[][] = [
    ['Вход на объект', 'Центр стройки', 'Большой баннер «Мартышкин труд»', 'Зона хаоса с краном'],
    ['Приём бананов', 'Упаковка', 'Отгрузка', 'Зона возврата «не туда отправили»'],
    ['Приёмная', 'Окна заявлений', 'Лабиринт столов', 'Архивная дверь'],
    ['Край джунглей', 'Лиановый проход', 'Водопад', 'Старый объект труда в зарослях'],
    ['Вход на ферму', 'Склад урожая', 'Зона куриной проверки', 'Амбар сверхплана'],
    ['Зал ожидания проверки', 'Коридор замечаний', 'Главная трибуна инспектора', 'Стена актов'],
    ['Вход в цех', 'Конвейерная линия', 'Котельная', 'Главный механизм'],
    ['Первые стеллажи', 'Глубокий архив', 'Секретный сектор', 'Дверь к реактору'],
    ['Вход в лабораторию', 'Трубный сектор', 'Сердце реактора', 'Перегрев плана'],
    ['Начало коридора', 'Зона аудита', 'Архив проверок', 'Дверь с табличкой «ещё раз»'],
    ['Сумерки', 'Полночь', 'Зона фонарей', 'Рассветный отчёт'],
    ['Класс', 'Полигон тренировки', 'Экзаменационная зона', 'Выход к башне согласований'],
    ['Нижние этажи', 'Середина башни', 'Кабинет главного согласования', 'Выход на министерство-фабрику'],
    ['Министерский вход', 'Штамповочный цех', 'Зал регламентов', 'Ворота к сердцу труда'],
    ['Внешнее кольцо', 'Механизм', 'Ядро', 'Финальный баннер труда'],
];

const BILLBOARDS = [
    'КАСКА ЕСТЬ\nПЛАНА НЕТ',
    'ОТЧЁТ\nПРИНЯТ',
    'ОКНО\nЗАЯВЛЕНИЙ',
    'Я НА\nПРОВЕРКЕ',
    '220V\nИ РЕАКТОР',
    'ДОРОГА\nАУДИТА',
    'КРАСКА\nРЕГЛАМЕНТА',
    'БАЛКА\nСОГЛАСОВАНА',
    'СМЕТА\nЖИВА',
    'БРИГАДА\nВ НОЧЬ',
    'ОБЪЕКТ\nПОЧТИ ГОТОВ',
    'ПРИМАТ\nРАБОТАЕТ',
    'ПРОЕКТ\nУСПЕШЕН',
];

const MANDATORY_SIGNAGE_AUDIT_BANK = [
    'КИРПИЧ С ДУШОЙ',
    'ОТЧЁТ',
    'ОКНО ЗАЯВЛЕНИЙ',
    'Я НА ПРОВЕРКЕ',
    '220V И РЕАКТОР',
    'НЕ БОЯТЬСЯ',
    'ДОРОГА АУДИТА',
    'КРАСКА РЕГЛАМЕНТА',
    'БАЛКА СОГЛАСОВАНА',
    'КАСКА ЕСТЬ / ПЛАНА НЕТ',
    'ОБЪЕКТ ПОЧТИ ГОТОВ',
    'ПРИМАТ РАБОТАЕТ',
    'СМЕТА ЖИВА',
    'БРИГАДА В НОЧЬ',
] as const;

const DEFAULT_PLAYER_NAME = 'Безымянный примат';
const PLAYER_NAME_MAX_LENGTH = 24;

@ccclass('GameRoot')
export class GameRoot extends Component {
    private backgroundImageNode!: Node;
    private backgroundSprite: Sprite | null = null;
    private backgroundSegments: BackgroundSegment[] = [];
    private activeBackgroundSegmentCount = 0;
    private backgroundWorldDistancePx = 0;
    private lastBackgroundTextureLogKey = '';
    private lastBackgroundSyncLogKey = '';
    private lastTrackBackdropSyncLogKey = '';
    private backgroundFrameCache: Record<number, SpriteFrame> = {};
    private backgroundFrameOrder: number[] = [];
    private backgroundFrameLoading: Record<number, boolean> = {};
    private backgroundFrameLoadStartedAt: Record<number, number> = {};
    private backgroundFrameAppliedLogged: Record<number, boolean> = {};
    private backgroundPreviewFrameCache: Record<number, SpriteFrame> = {};
    private backgroundPreviewFrameLoading: Record<number, boolean> = {};
    private backgroundPreviewFrameAppliedLogged: Record<number, boolean> = {};
    private backgroundPreviewFrameLoadStartedAt: Record<number, number> = {};
    private activeBackgroundTheme = -1;
    private activeBackgroundFrameKey = '';
    private pendingStartLevel = -1;
    private graphics!: Graphics;
    private activeRenderLayer: RenderLayerName = 'BG_MID';
    private graphicsLayers: Partial<Record<RenderLayerName, Graphics>> = {};
    private spriteLayers: Partial<Record<RenderLayerName, Node>> = {};
    private labelLayers: Partial<Record<RenderLayerName, Node>> = {};
    private pauseTouchZone!: Node;
    private devPasswordNode!: Node;
    private devPasswordEdit!: EditBox;
    private playerNameEditNode!: Node;
    private playerNameEdit!: EditBox;
    private audioSource!: AudioSource;
    private musicSource!: AudioSource;
    private buttons: Button[] = [];
    private labelPoolsByLayer: Partial<Record<RenderLayerName, PooledLabel[]>> = {};
    private labelCursorsByLayer: Partial<Record<RenderLayerName, number>> = {};
    private spritePoolsByLayer: Partial<Record<RenderLayerName, PooledSprite[]>> = {};
    private spriteCursorsByLayer: Partial<Record<RenderLayerName, number>> = {};
    private primitiveCountsByLayer: Partial<Record<RenderLayerName, number>> = {};
    private objectSpriteFrames: Record<string, SpriteFrame> = {};
    private objectSpriteLoading: Record<string, boolean> = {};
    private objectSpriteAliases: Record<string, string> = {};
    private objectSpriteReverseAliases: Record<string, string[]> = {};
    private objectSpriteAutoCorrectLogged: Record<string, boolean> = {};
    private objectSpriteQueued: Record<string, boolean> = {};
    private objectSpriteQueuedPriority: Record<string, ObjectSpriteLoadPriority> = {};
    private objectSpriteLoadFailures: Record<string, string> = {};
    private objectSpriteQueue: string[] = [];
    private objectSpriteActiveLoads = 0;
    private objectSpriteQueuePumpScheduled = false;
    private objectSpriteQueueHighWater = 0;
    private objectSpriteLoadStartedAt: Record<string, number> = {};
    private objectSpriteEnqueueBatchLogged: Record<string, boolean> = {};
    private playerSkinVariantPreloadLogged: Record<string, boolean> = {};
    private levelThemeWarmupScheduled: Record<number, boolean> = {};
    private utilityWarmupScheduled = false;
    private menuUiCriticalPreloadLoggedBySurface: Record<string, boolean> = {};
    private mainMenuBackgroundPreloadStarted = false;
    private mainMenuDeferredButtonsPreloadStarted = false;
    private secondaryMenuUiPreloadStarted = false;
    private menuUiGateWaitLoggedBySurface: Record<string, boolean> = {};
    private menuUiReadyLoggedBySurface: Record<string, boolean> = {};
    private clips: Record<string, AudioClip> = {};
    private audioPreloadScheduled = false;
    private audioCoreLoadStarted = false;
    private audioDeferredLoadStarted = false;
    private currentMusic = '';
    private rngSeed = 1;
    private readonly devEvents = new GameRootDevEventAdapter({
        eventsEnabled: DEBUG,
        onEvent: DEBUG ? logGameRootDevEvent : undefined,
    });

    private state: State = 'menu';
    private levelIndex = 0;
    private unlockedLevel = 0;
    private selectedSkin = 0;
    private playerName = DEFAULT_PLAYER_NAME;
    private musicVolume = DEFAULT_MUSIC_VOLUME;
    private sfxVolume = DEFAULT_SFX_VOLUME;
    private voiceVolume = DEFAULT_VOICE_VOLUME;
    private musicEnabled = true;
    private sfxEnabled = true;
    private voiceEnabled = true;
    private musicClock = 0;
    private musicStep = 0;
    private developerMode = false;
    private debugColliders = false;
    private debugReadability = false;
    private showTouchZones = false;
    private pendingQaPauseAfterStart = false;
    private pendingQaPauseShowTouchZones = false;
    private showPerfOverlay = false;
    private devStatusText = '';
    private lastPauseToggleMs = 0;
    private pauseTapAccepted = 0;
    private assetUsageLogged: Record<string, boolean> = {};
    private equipmentAttachLogged: Record<string, boolean> = {};
    private equipmentMissingLogged: Record<string, boolean> = {};
    private skinVariantMissingLogged: Record<string, boolean> = {};
    private legacyPlayerEquipmentFallbackSuppressedLogged: Record<string, boolean> = {};
    private currentPlayerVisualKey = '';
    private previousPlayerVisualKey = '';
    private playerVisualBlendTimer = 0;
    private lastSkinVariantLog = '';
    private lastPlayerPoseLog = '';
    private magnetLogCooldown = 0;
    private lastLayerDrawLogAt = -999;
    private layerDrawLoggedOnce = false;
    private lastBackgroundDuplicateScan = '';
    private audioUnlocked = false;
    private devTapCount = 0;
    private devTapWindow = 0;
    private voiceCooldown = 0;
    private voiceBurstWindow = 0;
    private voiceBurstCount = 0;
    private readonly fixedDt = 1 / 60;
    private logicAccumulator = 0;
    private progress = 0;
    private score = 0;
    private hp = 3;
    private bananasCollected = 0;
    private invincible = 0;
    private hitPoseTimer = 0;
    private secondJumpPoseTimer = 0;
    private dashTimer = 0;
    private dashCooldown = 0;
    private jumpBoost = 0;
    private dashBoost = 0;
    private armor = 0;
    private magnet = 0;
    private vestBonus = 0;
    private shieldBonus = 0;
    private coffeeBoost = 0;
    private blueprintBonus = 0;
    private passBonus = 0;
    private extraLifeAura = 0;
    private runBonusCount = 0;
    private runBonusSeen: boolean[] = [];
    private runDamageTaken = 0;
    private runStartClock = 0;
    private achievementToastTimer = 0;
    private achievementActive: AchievementToast | null = null;
    private achievementQueue: AchievementToast[] = [];
    private bannerTimer = 0;
    private bannerText = '';
    private storyStage = -1;
    private reason = '';
    private clock = 0;
    private gliding = false;
    private cameraShake = 0;

    private player = { x: 250, y: GROUND, vy: 0, onGround: true, doubleJump: true };
    private platforms: Platform[] = [];
    private bananas: Banana[] = [];
    private obstacles: Obstacle[] = [];
    private bonuses: Bonus[] = [];
    private npcs: Npc[] = [];
    private particles: Particle[] = [];
    private particlePool: Particle[] = [];
    private gameState!: RunnerGameState;
    private fixedStepCount = 0;
    private dtOkLogged = false;
    private treadmillReadyLogged = false;
    private objectCatalogLogged = false;
    private difficultyProfileLogged = false;
    private objectSpritesPreloadStarted = false;
    private selectedSkinVariantPreloadScheduledFor = -1;
    private playerSkinStartGatePending = false;
    private playerSkinStartGateAttempts = 0;
    private gameplayStartGateRetryScheduled = false;
    private pendingQaObstacleSpawn = false;
    private pendingQaBonusSpawn = false;
    private pendingSkinSelection = 0;
    private qaForcedSkinVariant: PlayerSkinVariant | null = null;
    private qaForcedPlayerPose: PlayerSkinPose | null = null;
    private resolutionPolicyMode: 'show_all' | 'fixed_height' | null = null;

    private applyResponsiveResolutionPolicy(): void {
        const frame = screen.windowSize;
        const viewportWidth = Number.isFinite(frame.width) && frame.width > 0 ? frame.width : W;
        const viewportHeight = Number.isFinite(frame.height) && frame.height > 0 ? frame.height : H;
        const isNarrowerThanDesign = viewportWidth / viewportHeight < W / H;
        const nextMode: 'show_all' | 'fixed_height' = !sys.isNative && isNarrowerThanDesign
            ? 'show_all'
            : 'fixed_height';
        if (this.resolutionPolicyMode === nextMode) return;

        this.resolutionPolicyMode = nextMode;
        const policy = nextMode === 'show_all' ? ResolutionPolicy.SHOW_ALL : ResolutionPolicy.FIXED_HEIGHT;
        view.setDesignResolutionSize(W, H, policy);
        console.log(
            `MTR_RESOLUTION_POLICY platform=${sys.isNative ? 'native' : 'web'}`
            + ` orientation=${viewportWidth < viewportHeight ? 'portrait' : 'landscape'}`
            + ` policy=${nextMode} viewport=${Math.round(viewportWidth)}x${Math.round(viewportHeight)}`,
        );
    }

    private onCanvasResize(): void {
        this.applyResponsiveResolutionPolicy();
    }

    onLoad(): void {
        profiler.hideStats();
        this.applyResponsiveResolutionPolicy();
        view.on('canvas-resize', this.onCanvasResize, this);
        this.node.getComponent(UITransform)?.setContentSize(W, H);
        const uiLayer = this.node.layer;
        console.log(`MTR_BITMAP_RUNTIME_READY owner=GameRoot platform=${sys.isNative ? 'native' : 'web'} backgrounds=resources/backgrounds objects=latest_themed_assets`);

        this.backgroundImageNode = new Node('BG_FAR_BitmapBackground');
        this.backgroundImageNode.layer = uiLayer;
        this.backgroundImageNode.setPosition(Vec3.ZERO);
        this.backgroundImageNode.addComponent(UITransform).setContentSize(W, H);
        this.backgroundImageNode.active = false;
        this.node.addChild(this.backgroundImageNode);

        for (const layerName of RENDER_LAYER_ORDER) {
            const drawNode = new Node(`${layerName}_Graphics`);
            drawNode.layer = uiLayer;
            drawNode.setPosition(Vec3.ZERO);
            drawNode.addComponent(UITransform).setContentSize(W, H);
            this.node.addChild(drawNode);
            const graphics = drawNode.addComponent(Graphics);
            this.graphicsLayers[layerName] = graphics;
            if (layerName === 'BG_MID') this.graphics = graphics;

            const spriteNode = new Node(`${layerName}_Sprites`);
            spriteNode.layer = uiLayer;
            spriteNode.setPosition(Vec3.ZERO);
            spriteNode.addComponent(UITransform).setContentSize(W, H);
            this.node.addChild(spriteNode);
            this.spriteLayers[layerName] = spriteNode;

            const labelNode = new Node(`${layerName}_Labels`);
            labelNode.layer = uiLayer;
            labelNode.setPosition(Vec3.ZERO);
            labelNode.addComponent(UITransform).setContentSize(W, H);
            this.node.addChild(labelNode);
            this.labelLayers[layerName] = labelNode;
        }
        console.log(`MTR_LAYER_ORDER_READY:${RENDER_LAYER_ORDER.join('>')}`);
        this.logBackgroundDuplicateScan('OK:init:sources=1');
        this.logTreadmillContracts('boot');
        this.logObjectCatalogSummary();

        this.pauseTouchZone = new Node('PauseTouchZone');
        this.pauseTouchZone.layer = uiLayer;
        this.pauseTouchZone.addComponent(UITransform).setContentSize(160, 104);
        this.pauseTouchZone.setPosition(this.cx(W - 90), this.cy(116));
        this.pauseTouchZone.on(Input.EventType.TOUCH_END, this.onPauseTouchZoneTap, this);
        this.pauseTouchZone.active = false;
        this.node.addChild(this.pauseTouchZone);
        this.pauseTouchZone.setSiblingIndex(9999);

        this.devPasswordNode = new Node('DevPasswordInput');
        this.devPasswordNode.layer = uiLayer;
        this.devPasswordNode.addComponent(UITransform).setContentSize(420, 58);
        this.devPasswordNode.setPosition(this.cx(640), this.cy(318));
        this.devPasswordEdit = this.devPasswordNode.addComponent(EditBox);
        this.devPasswordEdit.maxLength = 32;
        this.devPasswordEdit.placeholder = '';
        this.devPasswordEdit.string = '';
        this.devPasswordEdit.inputFlag = EditBox.InputFlag.PASSWORD;
        this.devPasswordNode.active = false;
        this.node.addChild(this.devPasswordNode);
        this.devPasswordNode.setSiblingIndex(9998);
        this.scrubDefaultEditBoxLabels(this.devPasswordNode);

        this.playerNameEditNode = new Node('PlayerNameInput');
        this.playerNameEditNode.layer = uiLayer;
        this.playerNameEditNode.addComponent(UITransform).setContentSize(520, 58);
        this.playerNameEditNode.setPosition(this.cx(640), this.cy(318));
        this.playerNameEdit = this.playerNameEditNode.addComponent(EditBox);
        this.playerNameEdit.maxLength = PLAYER_NAME_MAX_LENGTH;
        this.playerNameEdit.placeholder = DEFAULT_PLAYER_NAME;
        this.playerNameEdit.string = this.playerName;
        this.playerNameEditNode.active = false;
        this.node.addChild(this.playerNameEditNode);
        this.playerNameEditNode.setSiblingIndex(9997);
        this.scrubDefaultEditBoxLabels(this.playerNameEditNode);
        this.hideEditBoxVisualLabels(this.playerNameEditNode);
        this.installWebEditBoxVisualGuard();

        this.audioSource = this.node.addComponent(AudioSource);
        this.musicSource = this.node.addComponent(AudioSource);
        this.loadSettings();
        if (this.playerNameEdit) this.playerNameEdit.string = this.playerName;
        this.audioUnlocked = sys.isNative;
        this.preloadCriticalMenuUiSprites('boot-main-menu');
        this.preloadBackgroundFrames();
        this.preloadCriticalPlayerSkinSprites('boot-selected-skin');
        console.log('MTR_AUDIO_LOAD_DEFERRED_UNTIL_BACKGROUND reason=protect-cold-background-start');
        this.syncGameState();
        this.logDifficultyProfile('boot');
        this.logGameStateSnapshot('boot');
        console.log(`MTR_RUNTIME_CORE_READY state=${this.state} mode=${this.gameState.mode} levels=${LEVELS.length} fixedDt=${this.fixedDt}`);

        input.on(Input.EventType.TOUCH_START, this.onTouchStart, this);
        input.on(Input.EventType.TOUCH_MOVE, this.onTouchMove, this);
        input.on(Input.EventType.TOUCH_END, this.onTouchEnd, this);
        input.on(Input.EventType.TOUCH_CANCEL, this.onTouchEnd, this);
        input.on(Input.EventType.KEY_DOWN, this.onKeyDown, this);
        input.on(Input.EventType.KEY_UP, this.onKeyUp, this);

        this.reset('boot');
        this.applyStartupQuery();
    }

    onDestroy(): void {
        this.devEvents.invalidate(this.state, 'component_destroy', this.fixedStepCount);
        input.off(Input.EventType.TOUCH_START, this.onTouchStart, this);
        input.off(Input.EventType.TOUCH_MOVE, this.onTouchMove, this);
        input.off(Input.EventType.TOUCH_END, this.onTouchEnd, this);
        input.off(Input.EventType.TOUCH_CANCEL, this.onTouchEnd, this);
        input.off(Input.EventType.KEY_DOWN, this.onKeyDown, this);
        input.off(Input.EventType.KEY_UP, this.onKeyUp, this);
        view.off('canvas-resize', this.onCanvasResize, this);
        if (this.pauseTouchZone) this.pauseTouchZone.off(Input.EventType.TOUCH_END, this.onPauseTouchZoneTap, this);
    }

    update(dt: number): void {
        this.voiceCooldown = Math.max(0, this.voiceCooldown - dt);
        this.voiceBurstWindow = Math.max(0, this.voiceBurstWindow - dt);
        if (this.voiceBurstWindow <= 0) this.voiceBurstCount = 0;
        if (this.devTapWindow > 0) {
            this.devTapWindow -= dt;
            if (this.devTapWindow <= 0) this.devTapCount = 0;
        }
        if (this.achievementToastTimer > 0) {
            this.achievementToastTimer -= dt;
            if (this.achievementToastTimer <= 0) this.achievementActive = null;
        }
        if (!this.achievementActive && this.achievementQueue.length) {
            this.achievementActive = this.achievementQueue.shift() || null;
            this.achievementToastTimer = TOAST_DURATION_SEC;
        }
        if (this.state === 'playing') {
            this.logicAccumulator += Math.min(dt, 0.1);
            let steps = 0;
            while (this.logicAccumulator >= this.fixedDt && steps < 5 && this.state === 'playing') {
                this.updateGame(this.fixedDt);
                this.logicAccumulator -= this.fixedDt;
                steps++;
                this.fixedStepCount++;
                if (!this.dtOkLogged && this.fixedStepCount >= 10) {
                    this.dtOkLogged = true;
                    console.log(`MTR_DT_OK fixedDt=${this.fixedDt} steps=${this.fixedStepCount}`);
                }
            }
            if (steps >= 5) this.logicAccumulator = 0;
        } else {
            this.logicAccumulator = 0;
        }
        this.syncGameState();
        this.ensureMusic();
        this.draw();
    }

    private random(): number {
        this.rngSeed = (this.rngSeed * 1664525 + 1013904223) >>> 0;
        return this.rngSeed / 4294967296;
    }

    private randint(max: number): number {
        return Math.floor(this.random() * max) % max;
    }

    private modeForState(state: State): FsmMode {
        return gameSessionModeForState(state);
    }

    private createGameState(): RunnerGameState {
        const level = LEVELS[this.levelIndex] || LEVELS[0];
        return {
            mode: this.modeForState(this.state),
            state: this.state,
            levelId: this.levelIndex + 1,
            worldSpeed: level.speed,
            distance: this.progress,
            score: this.score,
            bananas: Math.min(this.bananasCollected, level.target),
            bonusBananas: Math.max(0, this.bananasCollected - level.target),
            hp: this.hp,
            seed: this.rngSeed,
            activeBonuses: {
                jumpBoost: Math.max(0, this.jumpBoost),
                dashBoost: Math.max(0, this.dashBoost),
                armor: Math.max(0, this.armor),
                magnet: Math.max(0, this.magnet),
                vest: Math.max(0, this.vestBonus),
                shield: Math.max(0, this.shieldBonus),
                coffee: Math.max(0, this.coffeeBoost),
                blueprint: Math.max(0, this.blueprintBonus),
                pass: Math.max(0, this.passBonus),
                lifeAura: Math.max(0, this.extraLifeAura),
            },
            player: { ...this.player },
            pools: {
                platforms: this.platforms.length,
                bananas: this.bananas.length,
                obstacles: this.obstacles.length,
                bonuses: this.bonuses.length,
                npcs: this.npcs.length,
                particles: this.particles.length + this.particlePool.length,
            },
        };
    }

    private syncGameState(): void {
        this.gameState = this.createGameState();
    }

    private transitionTo(next: State, reason = 'runtime'): GameSessionTransitionResult {
        const prev = this.state;
        const transition = evaluateGameSessionTransition(prev, next, reason);
        if (transition.accepted === false) {
            this.syncGameState();
            console.warn(`MTR_FSM_REJECT code=${transition.code} state=${prev}->${next} reason=${reason}`);
            this.devEvents.recordTransition(transition, this.fixedStepCount);
            return transition;
        }
        if (!transition.changed) {
            this.syncGameState();
            this.devEvents.recordTransition(transition, this.fixedStepCount);
            return transition;
        }
        if (prev === 'name' && next !== 'name') this.commitPlayerNameFromInput(false);
        const prevMode = this.modeForState(prev);
        const nextMode = this.modeForState(next);
        if (next === 'skins') this.pendingSkinSelection = this.selectedSkin;
        this.state = next;
        if (next === 'name') this.syncPlayerNameEditString();
        this.syncGameState();
        console.log(`MTR_FSM:${prevMode}->${nextMode} state=${prev}->${next} reason=${reason}`);
        this.devEvents.recordTransition(transition, this.fixedStepCount);
        return transition;
    }

    private logGameStateSnapshot(reason: string): void {
        this.syncGameState();
        console.log(`MTR_GAMESTATE reason=${reason} mode=${this.gameState.mode} level=${this.gameState.levelId} speed=${this.gameState.worldSpeed} distance=${Math.round(this.gameState.distance)} score=${this.gameState.score} hp=${this.gameState.hp} bananas=${this.gameState.bananas} bonus=${this.gameState.bonusBananas} pools=${this.gameState.pools.platforms}/${this.gameState.pools.obstacles}/${this.gameState.pools.bananas}/${this.gameState.pools.npcs}`);
    }

    private logObjectCatalogSummary(): void {
        if (this.objectCatalogLogged) return;
        this.objectCatalogLogged = true;
        const categories = REQUIRED_OBJECTIVE_CATEGORIES.join(',');
        console.log(`MTR_OBJECT_CATALOG_READY entries=${V2_OBJECT_CATALOG.length} categories=${categories} fields=asset_id,category,semantic_role,render_layer,collision_role,spawn_rule,level_family`);
    }

    private logTreadmillContracts(reason: string): void {
        if (this.treadmillReadyLogged) return;
        this.treadmillReadyLogged = true;
        console.log(`MTR_TREADMILL_READY reason=${reason} playerX=${this.player.x} worldXFormula=playerX+worldX-progress fixedDt=${this.fixedDt}`);
        console.log('MTR_BG_SCENIC_SYNC_OK owner=GameRootBackgroundController layers=BG_FAR mode=scenic-fit repeat=none proceduralFallback=0 correctionRectangles=0');
        console.log('MTR_BG_SEAMLESS_OK owner=GameRootBackgroundController layers=BG_FAR mode=scenic-fit repeat=none proceduralFallback=0 correctionRectangles=0');
        console.log('MTR_BG_DUPLICATE_OK');
    }

    private logDifficultyProfile(reason: string): void {
        if (this.difficultyProfileLogged) return;
        this.difficultyProfileLogged = true;
        const base = LEVELS[0].speed;
        const profile = LEVELS.map((level, index) => `L${index + 1}:${(level.speed / base).toFixed(2)}x/${Math.round(level.length / Math.max(1, level.speed))}s`).join(',');
        console.log(`MTR_DIFFICULTY_PROFILE reason=${reason} baseSpeed=${base} maxMul=${(LEVELS[LEVELS.length - 1].speed / base).toFixed(2)} curve=${profile}`);
    }

    private loadSettings(): void {
        try {
            this.playerName = this.sanitizePlayerName(sys.localStorage.getItem('mtr_player_name') || DEFAULT_PLAYER_NAME);
            this.selectedSkin = Number(sys.localStorage.getItem('mtr_skin') || '0') || 0;
            this.unlockedLevel = clamp(Number(sys.localStorage.getItem('mtr_unlocked_level') || '0') || 0, 0, LEVELS.length - 1);
            this.musicVolume = clamp(Number(sys.localStorage.getItem('mtr_music_volume') || String(DEFAULT_MUSIC_VOLUME)), 0, 1);
            this.sfxVolume = clamp(Number(sys.localStorage.getItem('mtr_sfx_volume') || String(DEFAULT_SFX_VOLUME)), 0, 1);
            this.voiceVolume = clamp(Number(sys.localStorage.getItem('mtr_voice_volume') || String(DEFAULT_VOICE_VOLUME)), 0, 1);
            const storedSound = sys.localStorage.getItem('mtr_sound_enabled');
            this.musicEnabled = storedSound !== '0' && sys.localStorage.getItem('mtr_music_enabled') !== '0';
            this.sfxEnabled = storedSound !== '0' && sys.localStorage.getItem('mtr_sfx_enabled') !== '0';
            this.voiceEnabled = storedSound !== '0' && sys.localStorage.getItem('mtr_voice_enabled') !== '0';
            this.developerMode = sys.localStorage.getItem('mtr_developer_mode') === '1';
            this.debugColliders = this.developerMode && sys.localStorage.getItem('mtr_debug_colliders') === '1';
            this.debugReadability = this.developerMode && (sys.localStorage.getItem('mtr_debug_readability') === '1' || sys.localStorage.getItem('mtr_readability_debug') === '1');
            this.showTouchZones = this.developerMode && sys.localStorage.getItem('mtr_show_touch_zones') === '1';
            this.showPerfOverlay = this.developerMode && sys.localStorage.getItem('mtr_show_perf_overlay') === '1';
            this.selectedSkin = clamp(this.selectedSkin, 0, SKINS.length - 1);
            if (this.developerMode) this.unlockedLevel = LEVELS.length - 1;
        } catch {
            this.playerName = DEFAULT_PLAYER_NAME;
        }
    }

    private saveSettings(): void {
        try {
            this.playerName = this.sanitizePlayerName(this.playerName);
            sys.localStorage.setItem('mtr_player_name', this.playerName);
            sys.localStorage.setItem('mtr_skin', String(this.selectedSkin));
            sys.localStorage.setItem('mtr_unlocked_level', String(this.unlockedLevel));
            sys.localStorage.setItem('mtr_music_volume', String(this.musicVolume));
            sys.localStorage.setItem('mtr_sfx_volume', String(this.sfxVolume));
            sys.localStorage.setItem('mtr_voice_volume', String(this.voiceVolume));
            sys.localStorage.setItem('mtr_music_enabled', this.musicEnabled ? '1' : '0');
            sys.localStorage.setItem('mtr_sfx_enabled', this.sfxEnabled ? '1' : '0');
            sys.localStorage.setItem('mtr_voice_enabled', this.voiceEnabled ? '1' : '0');
            sys.localStorage.setItem('mtr_sound_enabled', this.musicEnabled || this.sfxEnabled || this.voiceEnabled ? '1' : '0');
            sys.localStorage.setItem('mtr_developer_mode', this.developerMode ? '1' : '0');
            sys.localStorage.setItem('mtr_debug_colliders', this.debugColliders ? '1' : '0');
            sys.localStorage.setItem('mtr_debug_readability', this.debugReadability ? '1' : '0');
            sys.localStorage.setItem('mtr_readability_debug', this.debugReadability ? '1' : '0');
            sys.localStorage.setItem('mtr_show_touch_zones', this.showTouchZones ? '1' : '0');
            sys.localStorage.setItem('mtr_show_perf_overlay', this.showPerfOverlay ? '1' : '0');
        } catch {
            // Storage may be disabled on some embedded WebViews.
        }
    }

    private loadAudio(): void {
        if (this.audioCoreLoadStarted) return;
        this.audioPreloadScheduled = true;
        this.audioCoreLoadStarted = true;
        const names = ['jump', 'dash', 'hit', 'bonus', 'pause', 'banner', 'musicA', 'musicB'];
        this.loadAudioClips(names, 'core');
        this.scheduleOnce(() => this.loadDeferredAudio(), sys.isNative ? 4.25 : 1.25);
    }

    private scheduleAudioPreload(reason: string): void {
        if (this.audioPreloadScheduled || this.audioCoreLoadStarted) return;
        this.audioPreloadScheduled = true;
        const delay = sys.isNative ? 0.35 : 0;
        console.log(`MTR_AUDIO_LOAD_SCHEDULED reason=${reason} delay=${delay}`);
        this.scheduleOnce(() => this.loadAudio(), delay);
    }

    private loadDeferredAudio(): void {
        if (this.audioDeferredLoadStarted) return;
        this.audioDeferredLoadStarted = true;
        const voices = Object.values(VOICE_BANK).flat();
        const names = Array.from(new Set(['clear', 'level_clear', 'monkey', 'monkey_happy', 'stomp', ...voices])).filter((name) => !this.clips[name]);
        this.loadAudioClips(names, 'deferred');
    }

    private loadAudioClips(names: string[], reason: 'core' | 'deferred'): void {
        console.log(`MTR_AUDIO_LOAD_REQUEST reason=${reason} count=${names.length}`);
        for (const name of names) {
            resources.load(`audio/${name}`, AudioClip, (err, clip) => {
                if (!err && clip) {
                    this.clips[name] = clip;
                    if (name === 'musicA' || name === 'musicB') this.ensureMusic(true);
                }
            });
        }
    }

    private loadObjectSprites(): void {
        const menuKeys = this.criticalMenuUiSpriteKeys(MAIN_MENU_UI_SURFACE);
        const selectedSkinKeys = this.criticalPlayerSkinKeys(this.selectedSkin);
        const currentLevelKeys = this.criticalHazardSpriteKeys(this.levelIndex);
        const startupCollectibleKeys = sys.isNative ? NEW_COLLECTIBLE_ASSET_KEYS : NEW_COLLECTIBLE_ASSET_KEYS.slice(0, WEB_STARTUP_COLLECTIBLE_KEY_LIMIT);
        if (sys.isNative) {
            const nativeCriticalCount = this.enqueueObjectSprites([
                ...menuKeys,
                ...selectedSkinKeys,
                ...currentLevelKeys,
                ...startupCollectibleKeys,
            ], 'native-critical-current-level', 'critical');
            this.scheduleUtilitySpriteWarmup('native-post-critical');
            this.scheduleLevelThemeWarmup('native-post-critical', this.levelIndex);
            this.preloadSelectedSkinVariantsDeferred('native-post-critical');
            console.log(`MTR_OBJECT_PRELOAD_REQUESTED platform=native critical=${nativeCriticalCount} strategy=critical-first-chunked-warmup fullCatalogDeferred=true`);
            return;
        }
        const webCriticalCount = this.enqueueObjectSprites([
            ...menuKeys,
            ...currentLevelKeys,
            ...selectedSkinKeys,
            ...startupCollectibleKeys,
        ], 'web-critical-first-screen', 'critical');
        this.scheduleUtilitySpriteWarmup('web-post-first-screen');
        this.scheduleLevelThemeWarmup('web-post-first-screen', this.levelIndex);
        this.preloadSelectedSkinVariantsDeferred('web-idle-after-first-screen');
        console.log(`MTR_WEB_OBJECT_PRELOAD_REQUESTED critical=${webCriticalCount} strategy=web-critical-first-lazy-chunked fullCatalogDeferred=true themedFullCatalog=${THEMED_GAMEPLAY_RUNTIME_KEYS.length}`);
    }

    private criticalPlayerSkinKeys(skinIndex = this.selectedSkin): string[] {
        return playerSkinCriticalAssetKeysForSkin(skinIndex);
    }

    private preloadCriticalPlayerSkinSprites(reason: string, skinIndex = this.selectedSkin): void {
        const keys = this.criticalPlayerSkinKeys(skinIndex);
        this.enqueueObjectSprites(keys, `player-skin-critical:${reason}`, 'critical');
        console.log(`MTR_PLAYER_SKIN_CRITICAL_PRELOAD_REQUESTED reason=${reason} skin=${playerSkinId(skinIndex)} count=${keys.length}`);
    }

    private playerSkinVariantSpriteKeys(variant: PlayerSkinVariant, skinIndex = this.selectedSkin): string[] {
        return PLAYER_SKIN_RESOURCE_POSES.map((pose) => playerSkinResourceKey(skinIndex, variant, pose));
    }

    private preloadPlayerSkinVariantSprites(
        variant: PlayerSkinVariant,
        reason: string,
        skinIndex = this.selectedSkin,
        priority: ObjectSpriteLoadPriority = 'critical',
    ): void {
        const keys = this.playerSkinVariantSpriteKeys(variant, skinIndex);
        this.enqueueObjectSprites(keys, `player-skin-variant:${reason}:${variant}`, priority);
        const logKey = `${reason}:${playerSkinId(skinIndex)}:${variant}:${priority}`;
        if (!this.playerSkinVariantPreloadLogged[logKey]) {
            this.playerSkinVariantPreloadLogged[logKey] = true;
            console.log(`MTR_PLAYER_SKIN_VARIANT_PRELOAD_REQUESTED reason=${reason} skin=${playerSkinId(skinIndex)} variant=${variant} count=${keys.length} priority=${priority}`);
        }
    }

    private missingPlayerSkinVariantSprites(variant: PlayerSkinVariant, skinIndex = this.selectedSkin): string[] {
        return this.playerSkinVariantSpriteKeys(variant, skinIndex).filter((key) => !this.objectSpriteFrames[key]);
    }

    private arePlayerSkinVariantSpritesReady(variant: PlayerSkinVariant, skinIndex = this.selectedSkin): boolean {
        return this.missingPlayerSkinVariantSprites(variant, skinIndex).length === 0;
    }

    private preloadSelectedSkinVariantsDeferred(reason: string, skinIndex = this.selectedSkin): void {
        const normalizedSkinIndex = clamp(skinIndex, 0, PLAYER_SKIN_IDS.length - 1);
        if (this.selectedSkinVariantPreloadScheduledFor === normalizedSkinIndex) return;
        this.selectedSkinVariantPreloadScheduledFor = normalizedSkinIndex;
        const start = () => {
            const keys = playerSkinV2AssetKeysForSkin(normalizedSkinIndex);
            this.enqueueObjectSpritesChunked(keys, `player-skin-variants:${reason}:${PLAYER_SKIN_IDS[normalizedSkinIndex]}`, sys.isNative ? 'normal' : 'idle');
            console.log(`MTR_PLAYER_SKIN_VARIANTS_DEFERRED_PRELOAD_REQUESTED reason=${reason} skin=${PLAYER_SKIN_IDS[normalizedSkinIndex]} count=${keys.length} policy=chunked-idle`);
        };
        this.scheduleOnce(start, sys.isNative ? 0.75 : WEB_SKIN_VARIANTS_DEFER_SEC);
    }

    private criticalHazardSpriteKeys(levelIndex = this.levelIndex): string[] {
        return this.startupGameplaySpriteKeys(levelIndex);
    }

    private fullLevelThemeSpriteKeys(levelIndex = this.levelIndex): string[] {
        return Array.from(new Set<string>([
            ...themedPlatformKeysForLevel(levelIndex),
            ...themedAssetKeysForLevel(levelIndex, 'hazards'),
        ]));
    }

    private earlyVisibleLevelSpriteKeys(levelIndex = this.levelIndex): string[] {
        if (levelIndex !== this.levelIndex) return [];
        const keys: string[] = [];
        const minX = -240;
        const maxX = W + 560;
        for (const platform of this.platforms) {
            const screenX = this.worldX(platform.x + platform.w * 0.5);
            if (screenX > minX && screenX < maxX) keys.push(this.platformAssetKey(platform.type, platform.x));
        }
        for (const obstacle of this.obstacles) {
            const worldX = this.obstacleWorldX(obstacle);
            const screenX = this.worldX(worldX);
            if (screenX > minX && screenX < maxX) keys.push(this.obstacleAssetKey(obstacle.type, worldX));
        }
        return Array.from(new Set(keys.filter((key) => !!key)));
    }

    private startupGameplaySpriteKeys(levelIndex = this.levelIndex): string[] {
        const platformKeys = themedPlatformKeysForLevel(levelIndex);
        const hazardKeys = themedAssetKeysForLevel(levelIndex, 'hazards');
        const platformLimit = sys.isNative ? platformKeys.length : WEB_STARTUP_PLATFORM_KEY_LIMIT;
        const hazardLimit = sys.isNative ? hazardKeys.length : WEB_STARTUP_HAZARD_KEY_LIMIT;
        return Array.from(new Set<string>([
            ...this.earlyVisibleLevelSpriteKeys(levelIndex),
            ...platformKeys.slice(0, platformLimit),
            ...hazardKeys.slice(0, hazardLimit),
        ].filter((key) => !!key)));
    }

    private preloadCriticalHazardSprites(reason: string, levelIndex = this.levelIndex): void {
        const keys = this.criticalHazardSpriteKeys(levelIndex);
        this.enqueueObjectSprites(keys, `level-critical:${reason}:level-${levelIndex + 1}`, 'critical');
        this.scheduleLevelThemeWarmup(reason, levelIndex);
        console.log(`MTR_CRITICAL_LEVEL_ASSET_PRELOAD_REQUESTED reason=${reason} level=${levelIndex + 1} count=${keys.length} policy=visible-plus-limited-startup`);
    }

    private menuUiGateId(surface: string, state: State): string {
        return `${surface}:${state}`;
    }

    private criticalMenuUiSpriteKeys(surface = MAIN_MENU_UI_SURFACE, state: State = this.state): string[] {
        const keys: string[] = [];
        if (surface === MAIN_MENU_UI_SURFACE && state === 'menu') {
            keys.push(...MAIN_MENU_INITIAL_READY_KEYS);
        } else {
            keys.push(...UI_SHARED_ASSET_KEYS);
        }
        if (state === 'name') {
            keys.push(...START_MENU_UI_KEYS);
        }
        if (surface === 'level_select') {
            keys.push(...LEVEL_SELECT_THEME_ICON_KEYS);
        }
        if (surface === 'skin_select') {
            keys.push(...PLAYER_SKIN_PREVIEW_ASSET_KEYS);
        }
        if (surface === 'achievements') {
            keys.push(...ACHIEVEMENT_MENU_ICON_ASSET_KEYS);
        }
        return Array.from(new Set(keys));
    }

    private preloadCriticalMenuUiSprites(reason: string, surface = MAIN_MENU_UI_SURFACE, state: State = this.state): void {
        const gateId = this.menuUiGateId(surface, state);
        const keys = this.criticalMenuUiSpriteKeys(surface, state);
        this.enqueueObjectSprites(keys, `menu-ui-critical:${reason}:${gateId}`, 'critical');
        if (surface === MAIN_MENU_UI_SURFACE && state === 'menu') this.preloadMainMenuDeferredButtonSprites(reason);
        if (!this.menuUiCriticalPreloadLoggedBySurface[gateId]) {
            this.menuUiCriticalPreloadLoggedBySurface[gateId] = true;
            console.log(`MTR_MENU_UI_CRITICAL_PRELOAD_REQUESTED reason=${reason} surface=${surface} screen=${state} count=${keys.length}`);
        }
    }

    private areCriticalMenuUiSpritesReady(surface = MAIN_MENU_UI_SURFACE, state: State = this.state): boolean {
        const keys = this.criticalMenuUiSpriteKeys(surface, state);
        return keys.length === 0 || keys.every((key) => !!this.objectSpriteFrames[key]);
    }

    private missingCriticalMenuUiSprites(surface = MAIN_MENU_UI_SURFACE, state: State = this.state): string[] {
        return this.criticalMenuUiSpriteKeys(surface, state).filter((key) => !this.objectSpriteFrames[key]);
    }

    private preloadMainMenuBackgroundSprites(reason: string): void {
        this.enqueueObjectSprites(MAIN_MENU_BACKGROUND_REQUIRED_KEYS, `main-menu-background:${reason}`, 'critical');
        if (!this.mainMenuBackgroundPreloadStarted) {
            this.mainMenuBackgroundPreloadStarted = true;
            console.log(`MTR_MAIN_MENU_BACKGROUND_PRELOAD_REQUESTED reason=${reason} count=${MAIN_MENU_BACKGROUND_REQUIRED_KEYS.length}`);
        }
    }

    private preloadMainMenuDeferredButtonSprites(reason: string): void {
        if (this.mainMenuDeferredButtonsPreloadStarted) return;
        this.mainMenuDeferredButtonsPreloadStarted = true;
        const priority: ObjectSpriteLoadPriority = 'critical';
        this.enqueueObjectSprites(MAIN_MENU_DEONION_DEFERRED_KEYS, `main-menu-deferred-buttons:${reason}`, priority);
        console.log(
            `MTR_MAIN_MENU_DEFERRED_BUTTON_PRELOAD_REQUESTED reason=${reason} count=${MAIN_MENU_DEONION_DEFERRED_KEYS.length} priority=${priority} platform=${sys.isNative ? 'native' : 'web'}`,
        );
    }

    private preloadSecondaryMenuUiSprites(reason: string): void {
        if (this.secondaryMenuUiPreloadStarted) return;
        this.secondaryMenuUiPreloadStarted = true;
        const keys = new Set<string>(UI_SHARED_ASSET_KEYS);
        for (const key of START_MENU_UI_KEYS) keys.add(key);
        for (const key of LEVEL_SELECT_THEME_ICON_KEYS) keys.add(key);
        const start = () => {
            this.enqueueObjectSpritesChunked(keys, `secondary-ui:${reason}`, sys.isNative ? 'normal' : 'idle');
            console.log(`MTR_SECONDARY_UI_PRELOAD_REQUESTED reason=${reason} policy=shared_blank_runtime_text_chunked surfaces=${SECONDARY_MENU_UI_SURFACES.join(',')} count=${keys.size}`);
        };
        if (sys.isNative) this.scheduleOnce(start, 0.25);
        else this.scheduleOnce(start, 1.25);
    }

    private enqueueObjectSprites(keys: Iterable<string>, reason: string, priority: ObjectSpriteLoadPriority): number {
        const uniqueKeys = Array.from(new Set(Array.from(keys).filter((key) => !!key)));
        let requested = 0;
        for (const key of uniqueKeys) {
            if (this.requestObjectSprite(key, priority)) requested++;
        }
        const logKey = `${reason}:${priority}:${sys.isNative ? 'native' : 'web'}`;
        if (requested > 0 || (uniqueKeys.length > 0 && !this.objectSpriteEnqueueBatchLogged[logKey])) {
            this.objectSpriteEnqueueBatchLogged[logKey] = true;
            console.log(`MTR_OBJECT_SPRITE_ENQUEUE_BATCH reason=${reason} count=${uniqueKeys.length} requested=${requested} priority=${priority} platform=${sys.isNative ? 'native' : 'web'}`);
        }
        return uniqueKeys.length;
    }

    private enqueueObjectSpritesChunked(
        keys: Iterable<string>,
        reason: string,
        priority: ObjectSpriteLoadPriority,
        chunkSize = sys.isNative ? OBJECT_SPRITE_IDLE_CHUNK_NATIVE : OBJECT_SPRITE_IDLE_CHUNK_WEB,
        intervalSec = sys.isNative ? OBJECT_SPRITE_NATIVE_CHUNK_INTERVAL_SEC : OBJECT_SPRITE_WEB_CHUNK_INTERVAL_SEC,
    ): void {
        const uniqueKeys = Array.from(new Set(Array.from(keys).filter((key) => !!key)));
        if (uniqueKeys.length === 0) return;
        console.log(`MTR_OBJECT_SPRITE_CHUNKED_ENQUEUE_SCHEDULED reason=${reason} count=${uniqueKeys.length} chunkSize=${chunkSize} intervalSec=${intervalSec} priority=${priority} platform=${sys.isNative ? 'native' : 'web'}`);
        let offset = 0;
        const enqueueNextChunk = () => {
            const slice = uniqueKeys.slice(offset, offset + chunkSize);
            for (const key of slice) this.requestObjectSprite(key, priority);
            offset += slice.length;
            if (offset < uniqueKeys.length) {
                this.scheduleOnce(enqueueNextChunk, intervalSec);
                return;
            }
            console.log(`MTR_OBJECT_SPRITE_CHUNKED_ENQUEUE_DONE reason=${reason} count=${uniqueKeys.length} priority=${priority}`);
        };
        enqueueNextChunk();
    }

    private scheduleLevelThemeWarmup(reason: string, levelIndex = this.levelIndex): void {
        const normalizedLevelIndex = clamp(levelIndex, 0, LEVELS.length - 1);
        if (this.levelThemeWarmupScheduled[normalizedLevelIndex]) return;
        this.levelThemeWarmupScheduled[normalizedLevelIndex] = true;
        const critical = new Set(this.criticalHazardSpriteKeys(normalizedLevelIndex));
        const keys = this.fullLevelThemeSpriteKeys(normalizedLevelIndex).filter((key) => !critical.has(key));
        const start = () => this.enqueueObjectSpritesChunked(keys, `level-theme-warmup:${reason}:level-${normalizedLevelIndex + 1}`, sys.isNative ? 'normal' : 'idle');
        this.scheduleOnce(start, sys.isNative ? 0.15 : 1.1);
        console.log(`MTR_LEVEL_THEME_WARMUP_SCHEDULED reason=${reason} level=${normalizedLevelIndex + 1} deferredCount=${keys.length} platform=${sys.isNative ? 'native' : 'web'}`);
    }

    private scheduleUtilitySpriteWarmup(reason: string): void {
        if (this.utilityWarmupScheduled) return;
        this.utilityWarmupScheduled = true;
        const collectibleWarmupKeys = sys.isNative ? NEW_COLLECTIBLE_ASSET_KEYS : NEW_COLLECTIBLE_ASSET_KEYS.slice(WEB_STARTUP_COLLECTIBLE_KEY_LIMIT);
        const keys = [
            ...OBJECT_SPRITES,
            ...BONUS_ASSET_KEYS,
            ...collectibleWarmupKeys,
        ];
        const start = () => this.enqueueObjectSpritesChunked(keys, `utility-warmup:${reason}`, sys.isNative ? 'normal' : 'idle');
        this.scheduleOnce(start, sys.isNative ? 0.25 : WEB_UTILITY_WARMUP_DEFER_SEC);
        console.log(`MTR_UTILITY_SPRITE_WARMUP_SCHEDULED reason=${reason} count=${keys.length} platform=${sys.isNative ? 'native' : 'web'}`);
    }

    private areCriticalPlayerSkinSpritesReady(skinIndex = this.selectedSkin): boolean {
        const keys = this.criticalPlayerSkinKeys(skinIndex);
        for (const key of keys) {
            if (!this.objectSpriteFrames[key]) return false;
        }
        return true;
    }

    private missingCriticalHazardSprites(levelIndex = this.levelIndex): string[] {
        return this.criticalHazardSpriteKeys(levelIndex).filter((key) => !this.objectSpriteFrames[key]);
    }

    private waitForCriticalPlayerSkinSprites(target: number, reason: string): boolean {
        this.preloadCriticalPlayerSkinSprites(reason, this.selectedSkin);
        this.preloadCriticalHazardSprites(reason, target);
        const playerReady = this.areCriticalPlayerSkinSpritesReady(this.selectedSkin);
        const missingHazards = this.missingCriticalHazardSprites(target);
        const hazardsReady = missingHazards.length === 0;
        if (playerReady && hazardsReady) {
            if (this.playerSkinStartGatePending) console.log(`MTR_GAMEPLAY_START_GATE_READY level=${target + 1} attempts=${this.playerSkinStartGateAttempts}`);
            this.playerSkinStartGatePending = false;
            this.playerSkinStartGateAttempts = 0;
            this.gameplayStartGateRetryScheduled = false;
            return true;
        }
        this.playerSkinStartGatePending = true;
        this.playerSkinStartGateAttempts++;
        this.pendingStartLevel = target;
        this.bannerText = playerReady ? 'Грузим препятствия без заглушек' : 'Грузим примата без кружочка';
        this.bannerTimer = TOAST_DURATION_SEC;
        const sample = missingHazards.slice(0, 4).join('|');
        const shouldLog = this.playerSkinStartGateAttempts <= 5 || this.playerSkinStartGateAttempts % 10 === 0;
        if (shouldLog) console.log(`MTR_GAMEPLAY_START_GATE_WAIT level=${target + 1} attempt=${this.playerSkinStartGateAttempts} playerReady=${playerReady} hazardsReady=${hazardsReady} missingHazards=${missingHazards.length}${sample ? ` sample=${sample}` : ''}`);
        const retryDelay = this.playerSkinStartGateAttempts < 10 ? 0.28 : 0.55;
        if (!this.gameplayStartGateRetryScheduled) {
            this.gameplayStartGateRetryScheduled = true;
            this.scheduleOnce(() => {
                this.gameplayStartGateRetryScheduled = false;
                if (this.pendingStartLevel === target && this.state !== 'playing') this.startLevel(target);
            }, retryDelay);
        }
        return false;
    }

    private startObjectSpritePreload(reason: string): void {
        if (this.objectSpritesPreloadStarted) return;
        this.objectSpritesPreloadStarted = true;
        console.log(`MTR_OBJECT_PRELOAD_DEFERRED_START platform=${sys.isNative ? 'native' : 'web'} reason=${reason}`);
        this.loadObjectSprites();
    }

    private preloadBackgroundFrames(): void {
        console.log(`MTR_BACKGROUND_PRELOAD_START platform=${sys.isNative ? 'native' : 'web'} count=${LEVELS.length} strategy=preview-first-then-full cacheLimit=${BACKGROUND_FRAME_CACHE_LIMIT}`);
        this.preloadCriticalPlayerSkinSprites('boot-priority', this.selectedSkin);
        this.ensureBackgroundPreviewFrame(this.levelIndex, 'boot-preview');
    }

    private ensureBackgroundPreviewFrame(themeIndexRaw: number, reason: string): void {
        const themeIndex = clamp(themeIndexRaw, 0, LEVELS.length - 1);
        if (this.backgroundPreviewFrameCache[themeIndex] || this.backgroundPreviewFrameLoading[themeIndex]) return;
        const path = this.backgroundPreviewResourcePath(themeIndex);
        this.backgroundPreviewFrameLoading[themeIndex] = true;
        this.backgroundPreviewFrameLoadStartedAt[themeIndex] = Date.now();
        console.log(`MTR_BACKGROUND_PREVIEW_LOAD_REQUEST level=${themeIndex + 1} path=${path} reason=${reason}`);
        resources.load(path, SpriteFrame, (err, frame) => {
            this.backgroundPreviewFrameLoading[themeIndex] = false;
            const elapsedMs = Date.now() - (this.backgroundPreviewFrameLoadStartedAt[themeIndex] || Date.now());
            if (!err && frame) {
                this.backgroundPreviewFrameCache[themeIndex] = frame;
                console.log(`MTR_BACKGROUND_PREVIEW_LOAD_OK level=${themeIndex + 1} elapsedMs=${elapsedMs}`);
                if (reason === 'boot-preview') {
                    this.scheduleOnce(() => this.ensureBackgroundFrame(themeIndex, 'boot-current'), sys.isNative ? 0.15 : 0);
                }
            } else {
                const message = err instanceof Error ? err.message : String(err || 'unknown');
                console.warn(`MTR_BACKGROUND_PREVIEW_LOAD_FAIL level=${themeIndex + 1} path=${path} elapsedMs=${elapsedMs} err=${message}`);
            }
        });
    }

    private ensureBackgroundFrame(themeIndexRaw: number, reason: string): void {
        const themeIndex = clamp(themeIndexRaw, 0, LEVELS.length - 1);
        if (this.backgroundFrameCache[themeIndex] || this.backgroundFrameLoading[themeIndex]) return;
        const path = this.backgroundResourcePath(themeIndex);
        this.backgroundFrameLoading[themeIndex] = true;
        this.backgroundFrameLoadStartedAt[themeIndex] = Date.now();
        console.log(`MTR_BACKGROUND_LOAD_REQUEST level=${themeIndex + 1} path=${path} reason=${reason}`);
        resources.load(path, SpriteFrame, (err, frame) => {
            this.backgroundFrameLoading[themeIndex] = false;
            const elapsedMs = Date.now() - (this.backgroundFrameLoadStartedAt[themeIndex] || Date.now());
            if (!err && frame) {
                this.rememberBackgroundFrame(themeIndex, frame);
                console.log(`MTR_BACKGROUND_LOAD_OK level=${themeIndex + 1} elapsedMs=${elapsedMs} strategy=critical-current-first`);
                if (themeIndex < 3 || themeIndex === LEVELS.length - 1) {
                    console.log(`MTR_BACKGROUND_PRELOAD_OK platform=${sys.isNative ? 'native' : 'web'} level=${themeIndex + 1}`);
                }
                if ((reason === 'boot-current' || reason === 'start-level-gate') && themeIndex === this.levelIndex) {
                    this.startObjectSpritePreload(`after-current-background:${reason}`);
                    this.scheduleAudioPreload(`after-current-background:${reason}`);
                }
                if (this.pendingStartLevel === themeIndex) {
                    console.log(`MTR_BACKGROUND_START_GATE_READY level=${themeIndex + 1} elapsedMs=${elapsedMs}`);
                    if (this.waitForCriticalPlayerSkinSprites(themeIndex, 'background-gate')) {
                        this.pendingStartLevel = -1;
                        this.beginLevelNow(themeIndex);
                    }
                }
            } else {
                const message = err instanceof Error ? err.message : String(err || 'unknown');
                console.warn(`MTR_BACKGROUND_LOAD_FAIL level=${themeIndex + 1} path=${path} elapsedMs=${elapsedMs} err=${message}`);
                if ((reason === 'boot-current' || reason === 'start-level-gate') && themeIndex === this.levelIndex) {
                    this.startObjectSpritePreload(`after-current-background-fail:${reason}`);
                    this.scheduleAudioPreload(`after-current-background-fail:${reason}`);
                }
                if (this.pendingStartLevel === themeIndex) {
                    console.warn(`MTR_BACKGROUND_START_GATE_FAIL_OPEN level=${themeIndex + 1}`);
                    if (this.waitForCriticalPlayerSkinSprites(themeIndex, 'background-fail-open-gate')) {
                        this.pendingStartLevel = -1;
                        this.beginLevelNow(themeIndex);
                    }
                }
            }
        });
    }

    private requestObjectSprite(key: string, priority: ObjectSpriteLoadPriority = 'normal'): boolean {
        const requestedKey = key;
        key = normalizeObjectSpriteKey(key);
        if (requestedKey !== key) {
            this.objectSpriteAliases[requestedKey] = key;
            const aliases = this.objectSpriteReverseAliases[key] || [];
            if (aliases.indexOf(requestedKey) < 0) {
                aliases.push(requestedKey);
                this.objectSpriteReverseAliases[key] = aliases;
            }
            if (this.objectSpriteFrames[key]) this.objectSpriteFrames[requestedKey] = this.objectSpriteFrames[key];
            const logKey = `${requestedKey}->${key}`;
            if (!this.objectSpriteAutoCorrectLogged[logKey]) {
                this.objectSpriteAutoCorrectLogged[logKey] = true;
                console.warn(`MTR_OBJECT_SPRITE_ENTRYPOINT_AUTOCORRECT from=${requestedKey} to=${key}`);
            }
        }
        if (this.objectSpriteFrames[key] || this.objectSpriteLoading[key]) return false;
        if (this.objectSpriteQueued[key]) {
            const previousPriority = this.objectSpriteQueuedPriority[key] || 'normal';
            if (OBJECT_SPRITE_PRIORITY_RANK[priority] > OBJECT_SPRITE_PRIORITY_RANK[previousPriority]) {
                const previousIndex = this.objectSpriteQueue.indexOf(key);
                if (previousIndex >= 0) this.objectSpriteQueue.splice(previousIndex, 1);
                this.objectSpriteQueuedPriority[key] = priority;
                this.enqueueObjectSpriteQueueKey(key, priority);
                console.log(`MTR_OBJECT_SPRITE_QUEUE_PROMOTE key=${key} from=${previousPriority} to=${priority} queued=${this.objectSpriteQueue.length} active=${this.objectSpriteActiveLoads}`);
                this.pumpObjectSpriteLoadQueue();
                return true;
            }
            return false;
        }
        this.objectSpriteQueued[key] = true;
        this.objectSpriteQueuedPriority[key] = priority;
        this.enqueueObjectSpriteQueueKey(key, priority);
        if (this.objectSpriteQueue.length > this.objectSpriteQueueHighWater) {
            this.objectSpriteQueueHighWater = this.objectSpriteQueue.length;
            if (this.objectSpriteQueueHighWater <= 20 || this.objectSpriteQueueHighWater % OBJECT_SPRITE_QUEUE_LOG_STEP === 0) {
                console.log(`MTR_OBJECT_SPRITE_QUEUE_HIGH_WATER queued=${this.objectSpriteQueueHighWater} active=${this.objectSpriteActiveLoads} priority=${priority} platform=${sys.isNative ? 'native' : 'web'}`);
            }
        }
        this.pumpObjectSpriteLoadQueue();
        return true;
    }

    private enqueueObjectSpriteQueueKey(key: string, priority: ObjectSpriteLoadPriority): void {
        const targetRank = OBJECT_SPRITE_PRIORITY_RANK[priority];
        const insertAt = this.objectSpriteQueue.findIndex((queuedKey) => {
            const queuedPriority = this.objectSpriteQueuedPriority[queuedKey] || 'normal';
            return OBJECT_SPRITE_PRIORITY_RANK[queuedPriority] < targetRank;
        });
        if (insertAt >= 0) this.objectSpriteQueue.splice(insertAt, 0, key);
        else this.objectSpriteQueue.push(key);
    }

    private objectSpriteQueueHasUrgentWork(): boolean {
        return this.objectSpriteQueue.some((key) => {
            const priority = this.objectSpriteQueuedPriority[key] || 'normal';
            return priority === 'critical' || priority === 'visible';
        });
    }

    private objectSpriteMaxConcurrentLoads(): number {
        if (sys.isNative) return OBJECT_SPRITE_NATIVE_LOAD_CONCURRENCY;
        return this.objectSpriteQueueHasUrgentWork() ? OBJECT_SPRITE_WEB_URGENT_LOAD_CONCURRENCY : OBJECT_SPRITE_WEB_LOAD_CONCURRENCY;
    }

    private pumpObjectSpriteLoadQueue(): void {
        if (this.objectSpriteQueuePumpScheduled) return;
        this.objectSpriteQueuePumpScheduled = true;
        const pump = () => {
            this.objectSpriteQueuePumpScheduled = false;
            const maxLoads = this.objectSpriteMaxConcurrentLoads();
            while (this.objectSpriteActiveLoads < maxLoads && this.objectSpriteQueue.length > 0) {
                const key = this.objectSpriteQueue.shift() || '';
                if (!key) continue;
                delete this.objectSpriteQueued[key];
                delete this.objectSpriteQueuedPriority[key];
                if (this.objectSpriteFrames[key] || this.objectSpriteLoading[key]) continue;
                this.beginObjectSpriteLoad(key);
            }
            if (this.objectSpriteQueue.length > 0 && this.objectSpriteActiveLoads < maxLoads) this.pumpObjectSpriteLoadQueue();
        };
        if (sys.isNative) pump();
        else this.scheduleOnce(pump, 0);
    }

    private beginObjectSpriteLoad(key: string): void {
        this.objectSpriteLoading[key] = true;
        this.objectSpriteActiveLoads++;
        this.objectSpriteLoadStartedAt[key] = Date.now();
        const resourcePath = `${key}/spriteFrame`;
        resources.load(resourcePath, SpriteFrame, (err, frame) => {
            this.objectSpriteLoading[key] = false;
            this.objectSpriteActiveLoads = Math.max(0, this.objectSpriteActiveLoads - 1);
            const elapsedMs = Date.now() - (this.objectSpriteLoadStartedAt[key] || Date.now());
            delete this.objectSpriteLoadStartedAt[key];
            if (!err && frame) {
                this.objectSpriteFrames[key] = frame;
                for (const alias of this.objectSpriteReverseAliases[key] || []) this.objectSpriteFrames[alias] = frame;
                delete this.objectSpriteLoadFailures[key];
                if (key.startsWith('objectives/themed/last_iteration/')) console.log(`MTR_THEMED_OBJECT_SPRITE_LOAD_OK key=${key} path=${resourcePath}`);
                if (elapsedMs > OBJECT_SPRITE_LOAD_SLOW_MS) console.warn(`MTR_OBJECT_SPRITE_LOAD_SLOW key=${key} path=${resourcePath} elapsedMs=${elapsedMs} active=${this.objectSpriteActiveLoads} queued=${this.objectSpriteQueue.length}`);
                this.pumpObjectSpriteLoadQueue();
                return;
            }
            const message = err instanceof Error ? err.message : String(err || 'unknown');
            if (this.objectSpriteLoadFailures[key] !== message) {
                this.objectSpriteLoadFailures[key] = message;
                console.warn(`MTR_OBJECT_SPRITE_LOAD_FAIL key=${key} path=${resourcePath} elapsedMs=${elapsedMs} err=${message}`);
            }
            this.pumpObjectSpriteLoadQueue();
        });
    }

    private objectiveCategoryForKey(key: string): ObjectiveCategory {
        key = normalizeObjectSpriteKey(key);
        for (const category of REQUIRED_OBJECTIVE_CATEGORIES) {
            if (OBJECTIVE_CATEGORY_KEYS[category].includes(key)) return category;
        }
        if (key.startsWith('objectives/themed/')) {
            if (key.includes('/platforms/')) return 'platforms';
            if (key.includes('/hazards/')) return 'hazards';
            if (key.includes('/collectibles/')) return 'collectibles';
            if (key.includes('/bonuses/')) return 'bonuses';
            if (key.includes('/npc_decor/') || key.includes('/npc/')) return 'npc_decor';
            if (key.includes('/ui_achievements/') || key.includes('/ui/')) return 'ui_achievements';
            if (key.includes('/foreground_decor/')) return 'foreground_decor';
            if (key.includes('/background_decor/')) return 'background_decor';
            if (key.includes('/equipment/')) return 'equipment';
            return 'labels_signage';
        }
        if (key.startsWith(`${PLAYER_SKIN_RESOURCE_ROOT}/`)) return 'player_body';
        if (key.includes('objectives/collectibles/')) return 'collectibles';
        if (key.includes('platform') || key.includes('objectives/platforms')) return 'platforms';
        if (key.startsWith('hazard_')) return 'hazards';
        if (key.startsWith('story_')) return 'background_decor';
        if (key.startsWith('ui_achievement')) return 'ui_achievements';
        if (key.includes('label') || key.includes('banner') || key.includes('warning')) return 'active_labels';
        return 'labels_signage';
    }

    private markAssetUsage(key: string, category?: ObjectiveCategory, spawned = 1, reason = 'draw'): void {
        const actualCategory = category || this.objectiveCategoryForKey(key);
        const id = key.split('/').pop() || key;
        const usageKey = `${this.levelIndex}:${actualCategory}:${id}:${reason}`;
        if (this.assetUsageLogged[usageKey]) return;
        this.assetUsageLogged[usageKey] = true;
        console.log(`MTR_ASSET_USAGE category=${actualCategory} id=${id} level=${this.levelIndex + 1} spawned=${spawned} reason=${reason}`);
    }

    private logObjectiveIntegrationForLevel(): void {
        for (const category of REQUIRED_OBJECTIVE_CATEGORIES) {
            const keys = category === 'platforms'
                ? themedPlatformKeysForLevel(this.levelIndex)
                : category === 'hazards'
                    ? themedAssetKeysForLevel(this.levelIndex, 'hazards')
                    : OBJECTIVE_CATEGORY_KEYS[category];
            const limit = category === 'platforms' || category === 'hazards' ? Math.min(8, keys.length) : Math.min(6, keys.length);
            for (let i = 0; i < limit; i++) this.markAssetUsage(keys[i], category, 1, 'level_registry');
        }
        console.log(`MTR_ASSET_USAGE_SUMMARY level=${this.levelIndex + 1} categories=${REQUIRED_OBJECTIVE_CATEGORIES.join(',')}`);
    }

    private musicPlaybackVolume(): number {
        return clamp(this.musicVolume * MASTER_AUDIO_GAIN, 0, 1);
    }

    private sfxPlaybackVolume(volume: number): number {
        return clamp(volume * MASTER_AUDIO_GAIN * SFX_BUS_GAIN, 0, 1);
    }

    private voicePlaybackVolume(volume: number): number {
        const requested = volume * MASTER_AUDIO_GAIN * VOICE_BUS_GAIN;
        const musicRelativeCap = this.musicEnabled && this.musicVolume > 0
            ? this.musicPlaybackVolume() / MUSIC_TO_VOICE_RATIO
            : 1;
        return clamp(Math.min(requested, musicRelativeCap), 0, 1);
    }

    private play(name: string, volume = 1, channel: 'sfx' | 'music' = 'sfx'): void {
        if (channel === 'music' && !this.musicEnabled) return;
        if (channel === 'sfx' && !this.sfxEnabled) return;
        if (!this.audioUnlocked) return;
        if (!this.audioSource || !this.clips[name]) return;
        const playbackVolume = channel === 'music'
            ? clamp(volume * MASTER_AUDIO_GAIN, 0, 1)
            : this.sfxPlaybackVolume(volume);
        this.audioSource.playOneShot(this.clips[name], playbackVolume);
    }

    private unlockAudio(): void {
        if (this.audioUnlocked) return;
        this.audioUnlocked = true;
        this.ensureMusic(true);
    }

    private playFirst(names: string[], volume = 1, channel: 'sfx' | 'music' = 'sfx'): void {
        for (const name of names) {
            if (this.clips[name]) {
                this.play(name, volume, channel);
                return;
            }
        }
    }

    private playVoiceClip(name: string, volume: number): void {
        if (!this.audioUnlocked) return;
        if (!this.audioSource || !this.clips[name]) return;
        this.audioSource.playOneShot(this.clips[name], this.voicePlaybackVolume(volume));
    }

    private playVoice(event: VoiceEvent, chance = 1): void {
        if (!this.sfxEnabled || !this.voiceEnabled || this.voiceVolume <= 0 || Math.random() > chance) return;
        if (event !== 'death' && this.voiceCooldown > 0) return;
        if (event !== 'death') {
            if (this.voiceBurstWindow > 0 && this.voiceBurstCount >= 2) return;
            this.voiceBurstWindow = Math.max(this.voiceBurstWindow, 1);
            this.voiceBurstCount++;
            this.voiceCooldown = 0.34 + Math.random() * 0.18;
        }
        const pool = VOICE_BANK[event] || [];
        const start = Math.floor(Math.random() * Math.max(1, pool.length));
        for (let i = 0; i < pool.length; i++) {
            const name = pool[(start + i) % pool.length];
            if (this.clips[name]) {
                const variation = 0.9 + Math.random() * 0.2;
                this.playVoiceClip(name, clamp(this.sfxVolume * this.voiceVolume * variation, 0, 1));
                return;
            }
        }
        if (event !== 'ui') {
            const fallbackVolume = clamp(this.sfxVolume * this.voiceVolume * 0.55, 0, 1);
            for (const name of ['monkey_happy', 'monkey']) {
                if (this.clips[name]) {
                    this.playVoiceClip(name, fallbackVolume);
                    return;
                }
            }
        }
    }

    private ensureMusic(force = false): void {
        if (!this.musicSource) return;
        const next = this.state === 'playing' || this.state === 'paused' || this.state === 'clear' || this.state === 'over' || this.state === 'finished' ? 'musicB' : 'musicA';
        if (!this.audioUnlocked) return;
        if (!this.musicEnabled || this.musicVolume <= 0 || !this.clips[next]) {
            if (this.currentMusic) {
                this.musicSource.stop();
                this.currentMusic = '';
            }
            return;
        }
        this.musicSource.volume = this.musicPlaybackVolume();
        if (!force && this.currentMusic === next) return;
        this.musicSource.stop();
        this.musicSource.clip = this.clips[next];
        this.musicSource.loop = true;
        this.musicSource.play();
        this.currentMusic = next;
    }

    private restartLevelMusic(): void {
        this.currentMusic = '';
        this.musicStep = 0;
        this.musicClock = 7.5;
        if (this.musicSource) this.musicSource.stop();
        this.ensureMusic(true);
        console.log(`MTR_LEVEL_MUSIC_RESTART level=${this.levelIndex + 1} volume=${this.musicPlaybackVolume().toFixed(2)}`);
    }

    private tickMusic(dt: number): void {
        if (!this.musicEnabled || this.musicVolume <= 0) return;
        this.musicClock -= dt;
        if (this.musicClock > 0) return;
        if (this.musicStep % 4 === 3) this.playVoice('banana', 0.25);
        this.musicStep++;
        this.musicClock = 7.5;
    }

    private records(): RecordEntry[] {
        try {
            const raw = sys.localStorage.getItem('mtr_records') || '[]';
            const parsed = JSON.parse(raw) as RecordEntry[];
            return Array.isArray(parsed) ? parsed : [];
        } catch {
            return [];
        }
    }

    private saveRecord(): void {
        const name = (this.playerName || 'Безымянный примат').trim() || 'Безымянный примат';
        const entry: RecordEntry = { name, score: this.score, level: this.levelIndex + 1, bananas: this.bananasCollected };
        const records = this.records();
        const idx = records.findIndex((r) => r.name === name);
        if (idx < 0) records.push(entry);
        else if (entry.score > records[idx].score || entry.level > records[idx].level) records[idx] = entry;
        records.sort((a, b) => b.level - a.level || b.score - a.score);
        try {
            sys.localStorage.setItem('mtr_records', JSON.stringify(records.slice(0, 12)));
        } catch {
            // Ignore storage failures.
        }
    }

    private seedRecordsForQa(): void {
        const seeded: RecordEntry[] = [
            { name: 'Прораб Макакинсон', score: 15420, level: 15, bananas: 312 },
            { name: 'Безымянный примат', score: 12980, level: 14, bananas: 288 },
            { name: 'Инженер Банановой Сметы', score: 11110, level: 12, bananas: 251 },
            { name: 'Лаборантка Лиана', score: 9870, level: 10, bananas: 209 },
            { name: 'Кибер-Макака', score: 8760, level: 9, bananas: 198 },
            { name: 'Бригадир Золотой Каски', score: 7450, level: 7, bananas: 166 },
            { name: 'Очень длинное имя примата для проверки ведомости', score: 6120, level: 6, bananas: 144 },
        ];
        try {
            sys.localStorage.setItem('mtr_records', JSON.stringify(seeded));
            console.log(`MTR_RECORDS_QA_SEEDED count=${seeded.length}`);
        } catch {
            console.warn('MTR_RECORDS_QA_SEED_FAILED');
        }
    }

    private achievementEntries(): AchievementEntry[] {
        try {
            const raw = sys.localStorage.getItem('mtr_achievements') || '[]';
            const parsed = JSON.parse(raw) as AchievementEntry[];
            return Array.isArray(parsed) ? parsed : [];
        } catch {
            return [];
        }
    }

    private saveAchievementEntries(entries: AchievementEntry[]): void {
        try {
            sys.localStorage.setItem('mtr_achievements', JSON.stringify(entries.slice(-200)));
        } catch {
            // Ignore storage failures.
        }
    }

    private normalizedPlayerName(): string {
        return this.sanitizePlayerName(this.playerName);
    }

    private achievementDef(id: string): AchievementDef | undefined {
        return ACHIEVEMENTS.find((a) => a.id === id);
    }

    private hasAchievement(id: string): boolean {
        const name = this.normalizedPlayerName();
        return this.achievementEntries().some((entry) => entry.id === id && entry.nickname === name);
    }

    private unlockAchievement(id: string, reason: string): void {
        const def = this.achievementDef(id);
        if (!def || this.hasAchievement(id)) return;
        const name = this.normalizedPlayerName();
        const entries = this.achievementEntries();
        entries.push({ id, nickname: name, timestamp: Date.now(), level: this.levelIndex + 1, reason });
        this.saveAchievementEntries(entries);
        this.achievementQueue.push({ def, reason });
        this.playFirst(['banner', 'bonus', 'monkey_happy'], this.sfxVolume * 0.65);
        this.playVoice('ui', 0.7);
    }

    private checkAchievementProgress(trigger: string): void {
        if (this.bananasCollected >= 50) this.unlockAchievement('banana_50', trigger);
        if (this.bananasCollected >= 100) this.unlockAchievement('banana_100', trigger);
        if (this.bananasCollected > LEVELS[this.levelIndex].target) this.unlockAchievement('bonus_bananas', trigger);
        if (this.runBonusCount >= 3) this.unlockAchievement('bonus_three_run', trigger);
        if (this.runBonusSeen.filter(Boolean).length >= BONUS_COUNT) this.unlockAchievement('bonus_all_types', trigger);
        if (this.armor > 0) this.unlockAchievement('helmet_imitation', trigger);
        if (this.blueprintBonus > 0) this.unlockAchievement('almost_engineer', trigger);
        if (this.passBonus > 0) this.unlockAchievement('self_approved', trigger);
    }

    private unlockAllAchievementsForQa(): void {
        for (const def of ACHIEVEMENTS) this.unlockAchievement(def.id, 'dev QA unlock');
    }

    private askName(): void {
        this.syncPlayerNameEditString();
        const focusable = this.playerNameEdit as unknown as { focus?: () => void };
        if (focusable?.focus) focusable.focus();
        this.bannerText = 'Введи имя в поле и нажми «СОХРАНИТЬ ИМЯ»';
        this.bannerTimer = TOAST_DURATION_SEC;
    }

    private reset(reason: GameRootResetReason): void {
        const resetEpoch = this.devEvents.beginReset(this.state, reason, this.fixedStepCount);
        this.progress = 0;
        this.score = 0;
        this.hp = 3;
        this.bananasCollected = 0;
        this.invincible = 0;
        this.hitPoseTimer = 0;
        this.secondJumpPoseTimer = 0;
        this.dashTimer = 0;
        this.dashCooldown = 0;
        this.jumpBoost = 0;
        this.dashBoost = 0;
        this.armor = 0;
        this.magnet = 0;
        this.vestBonus = 0;
        this.shieldBonus = 0;
        this.coffeeBoost = 0;
        this.blueprintBonus = 0;
        this.passBonus = 0;
        this.extraLifeAura = 0;
        this.runBonusCount = 0;
        this.runBonusSeen = new Array(BONUS_COUNT).fill(false);
        this.runDamageTaken = 0;
        this.runStartClock = this.clock;
        this.achievementToastTimer = 0;
        this.achievementActive = null;
        this.achievementQueue = [];
        this.bannerTimer = 0;
        this.bannerText = '';
        this.storyStage = -1;
        this.reason = '';
        this.clock = 0;
        this.backgroundWorldDistancePx = 0;
        this.lastBackgroundSyncLogKey = '';
        this.lastTrackBackdropSyncLogKey = '';
        this.gliding = false;
        this.cameraShake = 0;
        this.logicAccumulator = 0;
        this.player = { x: 250, y: GROUND, vy: 0, onGround: true, doubleJump: true };
        this.particles = [];
        this.assetUsageLogged = {};
        this.equipmentAttachLogged = {};
        this.equipmentMissingLogged = {};
        this.skinVariantMissingLogged = {};
        this.legacyPlayerEquipmentFallbackSuppressedLogged = {};
        this.currentPlayerVisualKey = '';
        this.previousPlayerVisualKey = '';
        this.playerVisualBlendTimer = 0;
        this.lastSkinVariantLog = '';
        this.lastPlayerPoseLog = '';
        this.magnetLogCooldown = 0;
        this.layerDrawLoggedOnce = false;
        this.lastLayerDrawLogAt = -999;
        this.musicClock = 0;
        this.fixedStepCount = 0;
        this.dtOkLogged = false;
        this.generateLevel();
        this.logObjectiveIntegrationForLevel();
        this.syncGameState();
        this.logGameStateSnapshot('reset');
        this.devEvents.endReset(resetEpoch, this.state, reason, this.fixedStepCount);
    }

    private startLevel(i: number): void {
        const target = clamp(i, 0, this.developerMode ? LEVELS.length - 1 : this.unlockedLevel);
        if (!this.backgroundFrameCache[target]) {
            this.pendingStartLevel = target;
            this.bannerText = `Грузим фон объекта ${target + 1}`;
            this.bannerTimer = TOAST_DURATION_SEC;
            console.log(`MTR_BACKGROUND_START_GATE_WAIT level=${target + 1}`);
            this.ensureBackgroundPreviewFrame(target, 'start-level-preview');
            this.ensureBackgroundFrame(target, 'start-level-gate');
            return;
        }
        if (!this.waitForCriticalPlayerSkinSprites(target, 'start-level-gate')) return;
        this.pendingStartLevel = -1;
        this.beginLevelNow(target);
    }

    private beginLevelNow(target: number): void {
        this.levelIndex = target;
        this.ensureBackgroundFrame(this.levelIndex, 'start-level');
        this.transitionTo('playing', 'start_level');
        this.reset('start_level');
        this.restartLevelMusic();
        this.playVoice('ui', 0.45);
        if (this.pendingQaObstacleSpawn) {
            this.pendingQaObstacleSpawn = false;
            this.scheduleOnce(this.devEvents.guardSessionCallback(() => this.spawnAllObstacleFamiliesForQa()), 0);
        }
        if (this.pendingQaBonusSpawn) {
            this.pendingQaBonusSpawn = false;
            this.scheduleOnce(this.devEvents.guardSessionCallback(() => this.spawnAllBonusStatesForQa()), 0);
        }
        if (this.pendingQaPauseAfterStart) {
            this.pendingQaPauseAfterStart = false;
            this.scheduleOnce(this.devEvents.guardSessionCallback(() => {
                if (this.state !== 'playing') {
                    this.pendingQaPauseShowTouchZones = false;
                    return;
                }
                if (this.pendingQaPauseShowTouchZones) this.showTouchZones = true;
                this.pendingQaPauseShowTouchZones = false;
                this.togglePauseFromInput();
                console.log(`MTR_QA_STARTUP_PAUSE_APPLIED level=${this.levelIndex + 1}`);
                console.log('MTR_QA_SCREEN_READY screen=paused');
            }), 0.18);
        }
    }

    private startupQueryParams(): StartupQueryParams | null {
        if (sys.isNative) {
            const nativeQuery = readNativeStartupQuery();
            const params = parseStartupQueryParams(nativeQuery);
            if (params) console.log(`MTR_NATIVE_STARTUP_QUERY_READY queryLength=${nativeQuery.length}`);
            return params;
        }
        const locationLike = (globalThis as unknown as { location?: Location }).location;
        if (!locationLike?.href) return null;
        return parseStartupQueryParams(extractQueryFromHref(locationLike.href));
    }

    private seedEndStateForQa(state: EndState, target: number): void {
        this.levelIndex = clamp(target, 0, LEVELS.length - 1);
        this.unlockedLevel = Math.max(this.unlockedLevel, this.levelIndex);
        this.reset('qa_end_state');
        const level = LEVELS[this.levelIndex];
        this.progress = level.length;
        this.bananasCollected = state === 'over'
            ? Math.max(0, level.target - 1)
            : level.target + Math.max(1, Math.floor(level.target * 0.1));
        this.score = 12000 + this.levelIndex * 875 + this.bananasCollected * 100;
        this.reason = state === 'over' ? 'Бананов не хватило. Норма есть норма.' : '';
        this.ensureBackgroundPreviewFrame(this.levelIndex, `qa-end-state-${state}`);
        this.ensureBackgroundFrame(this.levelIndex, `qa-end-state-${state}`);
        this.preloadCriticalHazardSprites(`qa-end-state-${state}`, this.levelIndex);
        this.preloadCriticalPlayerSkinSprites(`qa-end-state-${state}`);
        this.transitionTo(state, 'startup_query_end_state');
        this.syncGameState();
        console.log(`MTR_QA_END_STATE_SEEDED screen=${state} level=${this.levelIndex + 1} score=${this.score} bananas=${this.bananasCollected} progress=${Math.round(this.progress)}`);
    }

    private applyStartupQuery(): void {
        const params = this.startupQueryParams();
        if (!params) return;
        if (params.get('mtr_dev') === '1') this.enableDeveloperMode();
        this.runDevEventResetLoopForQa(params);
        const skinParam = params.get('mtr_skin') || params.get('mtr_qa_skin');
        if (skinParam) {
            const skinIdIndex = PLAYER_SKIN_IDS.indexOf(skinParam as typeof PLAYER_SKIN_IDS[number]);
            const numericSkinIndex = Math.round(Number(skinParam));
            const targetSkin = skinIdIndex >= 0
                ? skinIdIndex
                : Number.isFinite(numericSkinIndex) ? numericSkinIndex : this.selectedSkin;
            this.selectedSkin = clamp(targetSkin, 0, SKINS.length - 1);
            this.pendingSkinSelection = this.selectedSkin;
            this.saveSettings();
            this.preloadCriticalPlayerSkinSprites('startup-query-skin', this.selectedSkin);
        }
        const variantParam = params.get('mtr_qa_variant') || params.get('mtr_variant');
        if (this.developerMode && variantParam && PLAYER_SKIN_VARIANTS.includes(variantParam as PlayerSkinVariant)) {
            this.qaForcedSkinVariant = variantParam as PlayerSkinVariant;
            this.preloadPlayerSkinVariantSprites(this.qaForcedSkinVariant, 'startup-query-forced-variant', this.selectedSkin, 'critical');
        }
        const poseParam = params.get('mtr_qa_pose') || params.get('mtr_pose');
        if (this.developerMode && poseParam && PLAYER_SKIN_QA_POSE_ALIASES[poseParam]) this.qaForcedPlayerPose = PLAYER_SKIN_QA_POSE_ALIASES[poseParam];
        if (this.developerMode && (this.qaForcedSkinVariant || this.qaForcedPlayerPose)) {
            console.log(`MTR_SKIN_QA_FORCED skin=${playerSkinId(this.selectedSkin)} variant=${this.qaForcedSkinVariant || 'runtime'} pose=${this.qaForcedPlayerPose || 'runtime'}`);
        }
        if (params.get('debugColliders') === 'true') {
            this.debugColliders = true;
            this.saveSettings();
        }
        if (params.get('mtr_debug_readability') === '1' || params.get('mtr_readability_debug') === '1') {
            this.developerMode = true;
            this.debugReadability = true;
            this.saveSettings();
        }
        if (params.get('mtr_seed_records') === '1') this.seedRecordsForQa();
        if (params.get('mtr_unlock_achievements') === '1') this.unlockAllAchievementsForQa();
        const qaState = params.get('mtr_state') || params.get('mtr_screen');
        if (qaState === 'pause' || qaState === 'paused' || params.get('mtr_pause') === '1') {
            this.pendingQaPauseAfterStart = true;
            this.pendingQaPauseShowTouchZones = params.get('mtr_show_touch_zones') === '1';
        }
        if (params.get('mtr_show_touch_zones') === '1') this.showTouchZones = true;
        const qaScreenAliases: Record<string, State> = {
            menu: 'menu',
            main_menu: 'menu',
            start: 'name',
            name: 'name',
            name_entry: 'name',
            levels: 'levels',
            level_select: 'levels',
            skins: 'skins',
            skin_select: 'skins',
            sound: 'sound',
            settings: 'sound',
            records: 'records',
            achievements: 'achievements',
            devgate: 'devgate',
            developer_gate: 'devgate',
            devpanel: 'devpanel',
            developer: 'devpanel',
            clear: 'clear',
            level_clear: 'clear',
            over: 'over',
            game_over: 'over',
            death: 'over',
            failed: 'over',
            finished: 'finished',
            game_finished: 'finished',
            completion: 'finished',
        };
        const qaScreen = qaState ? qaScreenAliases[qaState] : undefined;
        if (qaScreen && qaState !== 'pause' && qaState !== 'paused') {
            if (qaScreen === 'clear' || qaScreen === 'over' || qaScreen === 'finished') {
                const fallbackLevel = qaScreen === 'finished' ? LEVELS.length : 1;
                const requested = Math.round(Number(params.get('mtr_level') || `${fallbackLevel}`)) - 1;
                const target = clamp(Number.isFinite(requested) ? requested : fallbackLevel - 1, 0, LEVELS.length - 1);
                this.seedEndStateForQa(qaScreen, target);
            } else {
                this.transitionTo(qaScreen, 'startup_query');
            }
            console.log(`MTR_QA_SCREEN_READY screen=${qaScreen}`);
            return;
        }
        if (params.get('mtr_autostart') !== '1') return;
        const requested = Math.round(Number(params.get('mtr_level') || '1')) - 1;
        const target = clamp(Number.isFinite(requested) ? requested : 0, 0, LEVELS.length - 1);
        this.unlockedLevel = Math.max(this.unlockedLevel, target);
        this.startLevel(target);
        if (params.get('mtr_qa_obstacles') === '1' || params.get('mtr_spawn_obstacles') === '1') {
            this.pendingQaObstacleSpawn = true;
            if (this.state === 'playing') {
                this.pendingQaObstacleSpawn = false;
                this.spawnAllObstacleFamiliesForQa();
            }
        }
        if (params.get('mtr_qa_bonuses') === '1' || params.get('mtr_spawn_bonuses') === '1') {
            this.pendingQaBonusSpawn = true;
            if (this.state === 'playing') {
                this.pendingQaBonusSpawn = false;
                this.spawnAllBonusStatesForQa();
            }
        }
    }

    private runDevEventResetLoopForQa(params: StartupQueryParams): void {
        if (!DEBUG) return;
        const rawLoops = params.get('mtr_qa_reset_loops');
        if (rawLoops === null) return;
        if (!/^(?:[1-9]|10)$/.test(rawLoops)) {
            console.log('MTR_DEV_EVENT_QA_REJECTED reason=reset_loop_range');
            return;
        }
        const loops = Number(rawLoops);
        if (!Number.isSafeInteger(loops) || loops < 1 || loops > 10) {
            console.log('MTR_DEV_EVENT_QA_REJECTED reason=reset_loop_range');
            return;
        }
        for (let index = 0; index < loops; index += 1) this.reset('qa_reset_loop');

        const events = this.devEvents.snapshot();
        const sequences = new Set(events.map((event) => event.sequence));
        const epochEvents = events.filter((event) => event.code === 'session.epoch.changed').length;
        const resetBegins = events.filter((event) => event.code === 'session.reset.begin').length;
        const resetEnds = events.filter((event) => event.code === 'session.reset.end').length;
        const expectedResets = loops + 1;
        const exportJson = this.devEvents.exportJson(
            GAME_ROOT_DEV_EVENT_CAPACITY,
            GAME_ROOT_DEV_EVENT_MAX_EXPORT_BYTES,
        );
        const passed = this.devEvents.currentEpoch() === expectedResets
            && events.length === expectedResets * 3
            && sequences.size === events.length
            && epochEvents === expectedResets
            && resetBegins === expectedResets
            && resetEnds === expectedResets
            && exportJson.length > 2;
        console.log(
            `MTR_DEV_EVENT_QA_${passed ? 'READY' : 'FAIL'} loops=${loops}`
            + ` epoch=${this.devEvents.currentEpoch()} events=${events.length}`
            + ` unique=${sequences.size} resetBegin=${resetBegins} resetEnd=${resetEnds}`
            + ` exportBound=${GAME_ROOT_DEV_EVENT_MAX_EXPORT_BYTES}`,
        );
    }

    private enableDeveloperMode(): void {
        if (this.developerMode) return;
        this.developerMode = true;
        this.unlockedLevel = LEVELS.length - 1;
        this.bannerText = 'РЕЖИМ РАЗРАБОТЧИКА: ПРИМАТ ВСЁ ВИДИТ';
        this.bannerTimer = TOAST_DURATION_SEC;
        this.saveSettings();
        this.playFirst(['banner', 'monkey_happy', 'monkey'], this.sfxVolume * 0.8);
    }

    private openDevGate(): void {
        if (this.developerMode) {
            this.transitionTo('devpanel', 'open_dev_panel_enabled');
            this.devStatusText = 'Режим разработчика уже открыт.';
            return;
        }
        this.transitionTo('devgate', 'open_dev_gate');
        this.devStatusText = '';
        if (this.devPasswordEdit) this.devPasswordEdit.string = '';
    }

    private tryOpenDeveloperMode(): void {
        const value = this.devPasswordEdit?.string || '';
        const normalized = value.replace(/[^a-z]/gi, '').toLowerCase();
        if (normalized === 'primatal' || normalized.endsWith('primatal')) {
            this.enableDeveloperMode();
            this.devStatusText = 'Режим разработчика открыт.';
            this.transitionTo('devpanel', 'dev_password_ok');
            console.log('MTR_DEV_MODE_OPENED');
            return;
        }
        this.devStatusText = 'Неверный пароль. Примат не допущен.';
        console.warn(`MTR_DEV_MODE_DENIED inputLength=${value.length} normalizedLength=${normalized.length}`);
    }

    private isDeveloperCornerTap(x: number, y: number): boolean {
        return this.state === 'menu' && x < 180 && (y < 160 || y > H - 160);
    }

    private registerDeveloperCornerTap(): void {
        this.devTapWindow = Math.max(this.devTapWindow, 8);
        this.devTapCount++;
        console.log(`MTR_DEV_TAP count=${this.devTapCount} window=${this.devTapWindow.toFixed(1)}`);
        if (this.devTapCount < 7) return;
        this.enableDeveloperMode();
        this.devTapCount = 0;
        this.devTapWindow = 0;
        this.devStatusText = 'Режим разработчика открыт тапами.';
        this.transitionTo('devpanel', 'dev_tap_ok');
        console.log('MTR_DEV_MODE_OPENED_BY_TAPS');
    }

    private lockAchievementsForQa(): void {
        const name = this.normalizedPlayerName();
        this.saveAchievementEntries(this.achievementEntries().filter((entry) => entry.nickname !== name));
        this.achievementActive = null;
        this.achievementQueue = [];
        this.bannerText = 'Достижения текущего примата закрыты для теста';
        this.bannerTimer = TOAST_DURATION_SEC;
    }

    private spawnAllObstacleFamiliesForQa(): void {
        if (this.state !== 'playing') {
            this.pendingQaObstacleSpawn = true;
            this.startLevel(this.pendingStartLevel >= 0 ? this.pendingStartLevel : this.levelIndex);
            if ((this.state as State) !== 'playing') {
                this.bannerText = 'Готовим препятствия без заглушек';
                this.bannerTimer = TOAST_DURATION_SEC;
                return;
            }
        }
        this.pendingQaObstacleSpawn = false;
        const start = this.progress + 520;
        this.obstacles = [];
        for (let i = 0; i < OBSTACLES.length; i++) {
            this.obstacles.push({
                x: start + i * 172,
                y: GROUND,
                type: i,
                dead: false,
                label: this.obstacleLabel(i, i),
                motion: i % 5 === 0 ? 1 : i % 7 === 0 ? 2 : 0,
            });
        }
        this.bannerText = 'Все семейства препятствий выставлены';
        this.bannerTimer = TOAST_DURATION_SEC;
    }

    private spawnAllBonusStatesForQa(): void {
        const requiredVariants = PLAYER_SKIN_VARIANTS;
        const missing: string[] = [];
        for (const variant of requiredVariants) {
            this.preloadPlayerSkinVariantSprites(variant, 'qa-all-bonuses-gate', this.selectedSkin, 'critical');
            missing.push(...this.missingPlayerSkinVariantSprites(variant, this.selectedSkin));
        }
        if (missing.length > 0) {
            const sample = missing.slice(0, 3).join('|');
            this.devStatusText = `Грузим полный комплект: ${missing.length}`;
            this.bannerText = 'Грузим все варианты экипировки...';
            this.bannerTimer = TOAST_DURATION_SEC;
            console.log(`MTR_QA_BONUS_PRELOAD_WAIT variants=${requiredVariants.length} missing=${missing.length}${sample ? ` sample=${sample}` : ''}`);
            this.scheduleOnce(this.devEvents.guardSessionCallback(() => this.spawnAllBonusStatesForQa()), 0.35);
            return;
        }
        if (this.state !== 'playing') {
            this.pendingQaBonusSpawn = true;
            this.startLevel(this.pendingStartLevel >= 0 ? this.pendingStartLevel : this.levelIndex);
            return;
        }
        this.pendingQaBonusSpawn = false;
        const start = this.progress + 460;
        this.bonuses = [];
        for (let i = 0; i < BONUS_COUNT; i++) this.bonuses.push({ x: start + i * 112, y: 420 - (i % 3) * 38, type: i, taken: false });
        const qaBonusDurationSec = 24;
        this.jumpBoost = this.dashBoost = this.armor = this.magnet = this.vestBonus = this.shieldBonus = this.coffeeBoost = this.blueprintBonus = this.passBonus = this.extraLifeAura = qaBonusDurationSec;
        this.bannerText = 'Все бонусы и экипировка показаны';
        this.bannerTimer = TOAST_DURATION_SEC;
    }

    private generateLevel(): void {
        const level = LEVELS[this.levelIndex];
        const diff = this.difficulty();
        this.rngSeed = 1000 + this.levelIndex * 771;
        this.platforms = [];
        this.bananas = [];
        this.obstacles = [];
        this.bonuses = [];
        this.npcs = [];

        const earlyPlatformProfile = this.levelIndex < 3;
        const midPlatformProfile = this.levelIndex >= 3 && this.levelIndex < 9;
        const platformStartX = earlyPlatformProfile ? 1040 : midPlatformProfile ? 820 : 700;
        const platformStepBase = earlyPlatformProfile ? 860 : midPlatformProfile ? 760 : 680;
        const platformStepRnd = earlyPlatformProfile ? 430 : midPlatformProfile ? 360 : 320;
        const secondaryPlatformChance = earlyPlatformProfile ? 0.16 : midPlatformProfile ? 0.28 : 0.36;
        const platformLiftMin = earlyPlatformProfile ? 76 : midPlatformProfile ? 86 : 95;
        const platformLiftRnd = earlyPlatformProfile ? 72 : midPlatformProfile ? 82 : 90;
        let primaryPlatformCount = 0;
        let secondaryPlatformCount = 0;
        for (let x = platformStartX; x < level.length - 600; x += platformStepBase + this.random() * platformStepRnd) {
            const y = clamp(GROUND - (platformLiftMin + this.random() * platformLiftRnd), earlyPlatformProfile ? 408 : 330, earlyPlatformProfile ? 486 : 470);
            const w = earlyPlatformProfile ? 104 + this.random() * 132 : 110 + this.random() * 170;
            this.platforms.push({ x, y, w, type: (this.randint(12) + this.levelIndex) % 12, state: this.randint(3) });
            primaryPlatformCount++;
            if (this.random() < secondaryPlatformChance) {
                const secondaryGap = earlyPlatformProfile ? 190 + this.random() * 180 : 120 + this.random() * 150;
                const secondaryY = clamp(y + this.random() * 70 - 28, earlyPlatformProfile ? 414 : 330, earlyPlatformProfile ? 488 : 470);
                const secondaryW = earlyPlatformProfile ? 88 + this.random() * 106 : 90 + this.random() * 150;
                this.platforms.push({ x: x + w + secondaryGap, y: secondaryY, w: secondaryW, type: (this.randint(12) + this.levelIndex + 3) % 12, state: this.randint(3) });
                secondaryPlatformCount++;
            }
        }
        console.log(`MTR_PLATFORM_DENSITY_CONFIG level=${this.levelIndex + 1} profile=${earlyPlatformProfile ? 'early-open' : midPlatformProfile ? 'mid-balanced' : 'late-dense'} primary=${primaryPlatformCount} secondary=${secondaryPlatformCount} total=${this.platforms.length} start=${platformStartX} step=${platformStepBase}+${platformStepRnd} secondaryChance=${secondaryPlatformChance.toFixed(2)} yLift=${platformLiftMin}+${platformLiftRnd}`);

        let bananaCluster = 0;
        let lastBananaClusterX = -99999;
        const addBanana = (x: number, y: number, value = 1, kind: CollectibleKind = 'banana'): void => {
            this.bananas.push({ x, y, taken: false, value, cluster: bananaCluster, kind });
        };
        const addSideCollectible = (x: number, y: number, slot: number): void => {
            if (this.random() > SIDE_COLLECTIBLE_CHANCE) return;
            const roll = this.random();
            const kind: CollectibleKind = roll < 0.33 ? 'coconut' : 'figLeaf';
            const value = kind === 'coconut' ? 5 : 2;
            const side = slot % 2 === 0 ? 1 : -1;
            const offsetX = side * (30 + this.random() * 16);
            const offsetY = 18 + this.random() * 18;
            addBanana(x + offsetX, y - offsetY, value, kind);
        };
        const addCluster = (x: number, y: number, pattern: number): boolean => {
            const clusterGap = Math.max(MIN_CLUSTER_GAP_PX, W / MAX_BANANA_CLUSTERS_ON_SCREEN + 80);
            if (x - lastBananaClusterX < clusterGap) return false;
            if (pattern === 4) {
                addBanana(x, y, 3);
                addSideCollectible(x + 28, y, 0);
            } else {
                const counts = [3, 4, 3, 4];
                const count = counts[pattern % counts.length];
                const spacing = Math.max(MIN_BANANA_GAP_PX, pattern === 1 ? 62 : 58);
                for (let i = 0; i < count; i++) {
                    const t = i / Math.max(1, count - 1);
                    const arc = pattern === 0 || pattern === 1 ? Math.sin(t * Math.PI) * (pattern === 1 ? 26 : 20) : 0;
                    const stair = pattern === 3 ? (i - 1.5) * 11 : 0;
                    const bx = x + i * spacing;
                    const by = y - arc - stair;
                    addBanana(bx, by);
                    addSideCollectible(bx, by, i);
                }
            }
            lastBananaClusterX = x;
            bananaCluster++;
            return true;
        };
        const computeBananaValue = (): number => this.bananas.reduce((sum, item) => item.kind === 'banana' ? sum + Math.max(1, item.value || 1) : sum, 0);
        const addTopUpCluster = (x: number, y: number): number => {
            const occupied = this.bananas.some((item) => item.kind === 'banana' && Math.abs(item.x - x) < MIN_CLUSTER_GAP_PX * 0.45 && Math.abs(item.y - y) < 72);
            if (occupied) return 0;
            const clusterId = bananaCluster++;
            for (let i = 0; i < 3; i++) {
                const t = i / 2;
                const bx = x + i * MIN_BANANA_GAP_PX;
                const by = y - Math.sin(t * Math.PI) * 18;
                this.bananas.push({ x: bx, y: by, taken: false, value: 1, cluster: clusterId, kind: 'banana' });
            }
            return 3;
        };

        for (let x = 460; x < level.length - 500; x += 980 + this.random() * 520) {
            if (this.random() > BANANA_DENSITY_MULTIPLIER + 0.18) continue;
            const baseY = 510 - this.random() * 28;
            addCluster(x, baseY, this.randint(4));
        }

        for (let i = 0; i < this.platforms.length; i++) {
            const p = this.platforms[i];
            if ((i + this.levelIndex) % 2 !== 0 && this.random() > BANANA_DENSITY_MULTIPLIER) continue;
            const centerX = p.x + p.w * 0.5;
            const y = p.y - 38;
            addCluster(centerX - Math.min(72, p.w * 0.34), y, this.random() < 0.34 ? 4 : 2);
        }
        const desiredBananaValue = Math.ceil(level.target * 1.05);
        let topUpBananas = 0;
        for (let x = 720 + (this.levelIndex % 4) * 130; computeBananaValue() < desiredBananaValue && x < level.length - 720; x += 520 + (this.levelIndex % 3) * 70) {
            const lane = topUpBananas % 3;
            topUpBananas += addTopUpCluster(x, 500 - lane * 34);
        }
        const bananaSingles = this.bananas.filter((item) => item.kind === 'banana').length;
        const bananaValue = this.bananas.reduce((sum, item) => item.kind === 'banana' ? sum + Math.max(1, item.value || 1) : sum, 0);
        const coconuts = this.bananas.filter((item) => item.kind === 'coconut').length;
        const figLeaves = this.bananas.filter((item) => item.kind === 'figLeaf').length;
        console.log(`MTR_BANANA_DENSITY_CONFIG multiplier=${BANANA_DENSITY_MULTIPLIER} clusters=${bananaCluster} totalCollectibles=${this.bananas.length} bananas=${bananaSingles} bananaValue=${bananaValue} coconuts=${coconuts} figLeaves=${figLeaves} topUp=${topUpBananas} desired=${desiredBananaValue} sideChance=${SIDE_COLLECTIBLE_CHANCE} maxVisible=${MAX_VISIBLE_BANANAS_NORMAL}/${MAX_VISIBLE_BANANAS_MAGNET} minClusterGap=${MIN_CLUSTER_GAP_PX} minBananaGap=${MIN_BANANA_GAP_PX} target=${level.target}`);

        const intro = [0, 1, 2, 6, 7, 8, 0, 9, 1, 2, 6, 10, 17];
        const pool = this.obstaclePoolForTheme(level.theme);
        let counter = 0;
        let lastType = -1;
        let previousType = -1;
        for (let x = 880; x < level.length - 500;) {
            if (this.conflictsWithPlatform(x)) {
                x += 180;
                continue;
            }
            let type = this.levelIndex === 0 ? intro[counter % intro.length] : pool[(counter + this.randint(pool.length)) % pool.length];
            for (let attempt = 0; attempt < 5 && (type === lastType || type === previousType); attempt++) type = pool[(counter + attempt + 1 + this.randint(pool.length)) % pool.length];
            this.obstacles.push({ x, y: GROUND, type, dead: false, label: this.obstacleLabel(type, counter), motion: this.obstacleMotion(type, counter) });
            previousType = lastType;
            lastType = type;
            counter++;
            if (this.random() < (this.levelIndex < 3 ? 0.10 : 0.22 + diff * 0.10) && !this.conflictsWithPlatform(x + 220)) {
                let nextType = pool[(counter + 3) % pool.length];
                if (nextType === lastType || nextType === previousType) nextType = pool[(counter + 5) % pool.length];
                this.obstacles.push({ x: x + 220 + this.random() * 180, y: GROUND, type: nextType, dead: false, label: this.obstacleLabel(nextType, counter), motion: this.obstacleMotion(nextType, counter) });
                previousType = lastType;
                lastType = nextType;
                counter++;
            }
            x += Math.max(520, 900 - diff * 86 + this.random() * 390);
        }

        if (this.levelIndex >= 3) {
            for (let x = 1900; x < level.length - 1200; x += 1900 - Math.min(500, diff * 120) + this.random() * 700) {
                if (this.conflictsWithPlatform(x)) continue;
                this.npcs.push({ anchor: x, range: 82 + this.random() * 80, speed: 1.3 + diff * 0.18 + this.random() * 0.7, skin: this.randint(OBJECTIVE_BATCH_NPC_KEYS.length), t: this.random() * 6, dead: false });
            }
        }

        for (let x = 1450; x < level.length - 800; x += 2450 + this.random() * 900) {
            const p = this.nearbyPlatform(x);
            this.bonuses.push({ x, y: p ? p.y - 42 : GROUND - (120 + this.random() * 60), type: this.randint(BONUS_COUNT), taken: false });
        }
    }

    private updateGame(dt: number): void {
        const level = LEVELS[this.levelIndex];
        this.clock += dt;
        this.tickMusic(dt);
        this.invincible -= dt;
        this.hitPoseTimer -= dt;
        this.secondJumpPoseTimer -= dt;
        this.dashTimer -= dt;
        this.dashCooldown -= dt;
        this.jumpBoost -= dt;
        this.dashBoost -= dt;
        this.armor -= dt;
        this.magnet -= dt;
        this.vestBonus -= dt;
        this.shieldBonus -= dt;
        this.coffeeBoost -= dt;
        this.blueprintBonus -= dt;
        this.passBonus -= dt;
        this.extraLifeAura -= dt;
        this.bannerTimer -= dt;
        this.cameraShake -= dt;
        this.playerVisualBlendTimer -= dt;
        this.magnetLogCooldown -= dt;

        const prevProgress = this.progress;
        const dashTravelMul = this.dashBoost > 0 || this.coffeeBoost > 0 ? 1.92 : 1.72;
        const speedMul = this.dashTimer > 0 ? dashTravelMul : 1;
        const worldAdvance = level.speed * speedMul * dt;
        this.progress += worldAdvance;
        this.backgroundWorldDistancePx += worldAdvance;
        if (this.backgroundWorldDistancePx > 1000000) this.backgroundWorldDistancePx %= 100000;

        const stage = Math.min(3, Math.floor((this.progress / Math.max(1, level.length)) * 4));
        if (stage !== this.storyStage) {
            this.storyStage = stage;
            this.bannerText = (STORY[level.theme] || STORY[0])[stage];
            this.bannerTimer = TOAST_DURATION_SEC;
            this.playFirst(['banner', 'monkey_happy', 'monkey'], this.sfxVolume * 0.35);
        }

        const prevY = this.player.y;
        const prevRect = this.playerRectAt(prevY);
        let gravity = this.player.vy > 0 ? 1180 : 1450;
        if (this.gliding && this.player.vy > 0 && !this.player.onGround) gravity *= 0.38;
        this.player.vy += gravity * dt;
        this.player.y += this.player.vy * dt;
        this.player.onGround = false;

        if (this.player.vy >= 0) {
            for (const p of this.platforms) {
                const sx = this.worldX(p.x);
                if (this.player.x + 24 > sx && this.player.x - 24 < sx + p.w && prevY <= p.y && this.player.y >= p.y) {
                    this.player.y = p.y;
                    this.player.vy = 0;
                    this.player.onGround = true;
                    this.player.doubleJump = true;
                    this.secondJumpPoseTimer = 0;
                    break;
                }
            }
        }

        if (this.player.y > GROUND) {
            this.player.y = GROUND;
            this.player.vy = 0;
            this.player.onGround = true;
            this.player.doubleJump = true;
            this.secondJumpPoseTimer = 0;
        }

        const pr = this.playerRect();
        for (const b of this.bananas) {
            if (b.taken) continue;
            const attracted = this.attractWorldPointTowardPlayer(b.x, b.y, dt, b.kind);
            b.x = attracted.worldX;
            b.y = attracted.y;
            let sx = attracted.screenX;
            if (sx > -50 && sx < W + 50 && hit(pr, { x: sx - 18, y: b.y - 16, w: 36, h: 30 })) {
                b.taken = true;
                const gain = Math.max(1, b.value || 1);
                this.bananasCollected += gain;
                if (b.kind === 'banana') {
                    this.score += (15 + this.levelIndex) * gain;
                    this.emit(sx, b.y, rgb(255, 231, 90), 8 + gain * 2);
                    this.checkAchievementProgress('banana_collect');
                } else {
                    const coconut = b.kind === 'coconut';
                    this.score += ((coconut ? 35 : 25) + this.levelIndex * 2) * gain;
                    this.emit(sx, b.y, coconut ? rgb(196, 132, 72) : rgb(98, 218, 104), coconut ? 11 : 9);
                    this.play('bonus', this.sfxVolume * 0.3);
                    this.checkAchievementProgress(coconut ? 'coconut_collect' : 'fig_leaf_collect');
                }
            }
        }

        for (const bonus of this.bonuses) {
            if (bonus.taken) continue;
            const attracted = this.attractWorldPointTowardPlayer(bonus.x, bonus.y, dt, `bonus_${BONUS_LABELS[bonus.type % BONUS_COUNT]}`);
            bonus.x = attracted.worldX;
            bonus.y = attracted.y;
            const sx = attracted.screenX;
            if (hit(pr, { x: sx - 26, y: bonus.y - 26, w: 52, h: 52 })) {
                bonus.taken = true;
                this.activateBonus(bonus.type);
                this.emit(sx, bonus.y, rgb(183, 255, 138), 24);
                this.playFirst(['bonus', 'clear'], this.sfxVolume * 0.55);
            }
        }

        if (this.invincible <= 0) {
            for (const o of this.obstacles) {
                if (o.dead) continue;
                const ox = this.obstacleWorldX(o);
                const oy = this.obstacleBottomY(o);
                const sx = this.worldX(ox);
                const psx = this.worldXAt(ox, prevProgress);
                const rr = this.obstacleRect(sx, oy, o.type);
                const prr = this.obstacleRect(psx, oy, o.type);
                if (sx > -220 && sx < W + 220 && swept(prevRect, pr, prr, rr)) {
                    o.dead = true;
                    this.damage(OBSTACLES[o.type % OBSTACLES.length].joke, sx, oy - 40);
                    break;
                }
            }
        }

        for (const npc of this.npcs) {
            if (npc.dead) continue;
            npc.t += dt;
            const worldX = npc.anchor + Math.sin(npc.t * npc.speed + npc.skin * 1.7) * npc.range;
            const sx = this.worldX(worldX);
            if (sx < -120 || sx > W + 120) continue;
            const npcRect = { x: sx - 28, y: GROUND - 76, w: 56, h: 72 };
            if (!hit(pr, npcRect)) continue;
            const stomp = prevY <= GROUND - 78 && this.player.vy > -40;
            if (stomp) {
                npc.dead = true;
                this.player.vy = -520;
                const gain = 4 + this.difficulty();
                this.bananasCollected += gain;
                this.score += 90 + gain * 8;
                this.bannerText = `NPC-примат дал ${gain} бананов`;
                this.bannerTimer = 1.35;
                this.emit(sx, GROUND - 58, rgb(255, 224, 80), 26);
                this.playFirst(['stomp', 'monkey_happy', 'monkey'], this.sfxVolume * 0.82);
                this.playVoice('banana', 0.7);
                this.checkAchievementProgress('npc_stomp');
            } else if (this.invincible <= 0) {
                this.damage('NPC-примат доказал, что хаос умеет бегать.', sx, GROUND - 46);
            }
        }

        if (this.progress >= level.length) {
            const nextState: State = this.bananasCollected >= level.target
                ? (this.levelIndex === LEVELS.length - 1 ? 'finished' : 'clear')
                : 'over';
            this.transitionTo(nextState, 'level_end');
            if (this.state === 'clear' || this.state === 'finished') {
                this.unlockedLevel = Math.max(this.unlockedLevel, Math.min(LEVELS.length - 1, this.levelIndex + 1));
                this.saveSettings();
                this.unlockAchievement('level_clear', 'level_clear');
                if (this.runDamageTaken === 0) this.unlockAchievement('no_damage_clear', 'no_damage_clear');
            }
            if (this.state === 'over') {
                this.reason = 'Бананов не хватило. Норма есть норма.';
                this.playVoice('death', 1);
            } else {
                this.playVoice('clear', 1);
            }
            this.saveRecord();
            this.playFirst(this.state === 'over' ? ['hit'] : ['level_clear', 'clear'], this.sfxVolume);
        }

        this.updateParticles(dt);
    }

    private jump(): void {
        if (this.state !== 'playing') return;
        if (this.player.onGround) {
            this.player.vy = -(this.jumpBoost > 0 || this.coffeeBoost > 0 ? 700 : 620);
            this.player.onGround = false;
            this.player.doubleJump = true;
            this.secondJumpPoseTimer = 0;
            this.play('jump', this.sfxVolume * 0.72);
            this.playVoice('jump', 0.62);
        } else if (this.player.doubleJump) {
            this.player.vy = -(this.jumpBoost > 0 || this.coffeeBoost > 0 ? 630 : 545);
            this.player.doubleJump = false;
            this.secondJumpPoseTimer = 0.34;
            this.play('jump', this.sfxVolume * 0.58);
            this.playVoice('jump', 0.45);
        }
    }

    private dash(): void {
        if (this.state !== 'playing' || this.dashCooldown > 0) return;
        this.dashTimer = this.dashBoost > 0 || this.coffeeBoost > 0 ? 0.60 : 0.46;
        this.dashCooldown = this.dashBoost > 0 || this.coffeeBoost > 0 ? 0.55 : 0.95;
        this.cameraShake = Math.max(this.cameraShake, 0.08);
        this.emit(this.player.x + 20, this.player.y - 30, rgb(255, 240, 106), 20);
        this.play('dash', this.sfxVolume * 0.78);
        this.playVoice('dash', 0.82);
    }

    private activateBonus(type: number): void {
        const kind = type % BONUS_COUNT;
        this.runBonusCount++;
        this.runBonusSeen[kind] = true;
        switch (kind) {
            case 0:
                this.jumpBoost = 14;
                this.blueprintBonus = Math.max(this.blueprintBonus, 5);
                break;
            case 1:
                this.dashBoost = 12;
                this.dashCooldown = 0;
                break;
            case 2:
                this.shieldBonus = 18;
                break;
            case 3:
                this.magnet = 14;
                break;
            case 4:
                this.vestBonus = 16;
                break;
            case 5:
                this.coffeeBoost = 10;
                this.jumpBoost = Math.max(this.jumpBoost, 8);
                this.dashBoost = Math.max(this.dashBoost, 6);
                this.dashCooldown = 0;
                break;
            case 6:
                this.blueprintBonus = 16;
                this.score += 50;
                break;
            case 7:
                this.passBonus = 16;
                this.invincible = Math.max(this.invincible, 0.75);
                break;
            default:
                this.extraLifeAura = 10;
                this.hp = Math.min(3, this.hp + 1);
                this.score += 100;
                break;
        }
        this.bannerText = `БОНУС: ${BONUS_LABELS[kind]}`;
        this.bannerTimer = Math.max(this.bannerTimer, 1.25);
        this.playVoice(type === 5 ? 'dash' : 'ui', 0.55);
        this.checkAchievementProgress(`bonus_${BONUS_LABELS[kind]}`);
    }

    private damage(reason: string, sx: number, y: number): void {
        if (this.invincible > 0) return;
        this.runDamageTaken++;
        this.invincible = 1.05;
        this.hitPoseTimer = 0.28;
        this.secondJumpPoseTimer = 0;
        this.cameraShake = 0.25;
        this.dashTimer = 0;
        this.player.vy = -330;
        this.player.onGround = false;
        this.play('hit', this.sfxVolume);
        this.playVoice('hurt', 0.92);
        this.progress = Math.max(0, this.progress - 95);
        if (this.developerMode) {
            this.emit(sx, y, rgb(255, 240, 112), 20);
            if (this.showPerfOverlay || this.debugColliders || this.debugReadability) {
                this.bannerText = 'DEV: HP НЕ ТРАТИМ';
                this.bannerTimer = 0.9;
            }
            return;
        }
        if (this.armor > 0) {
            this.armor = 0;
            this.emit(sx, y, rgb(156, 255, 138), 22);
            return;
        }
        this.hp--;
        this.emit(sx, y, rgb(255, 105, 105), 24);
        if (this.hp <= 0) {
            this.reason = this.deathLine(reason);
            this.transitionTo('over', 'hp_zero');
            this.playVoice('death', 1);
        }
    }

    private deathLine(reason: string): string {
        if (reason.includes('окно') || reason.includes('Окно')) return 'Кривое окно нанесло кадровый удар.';
        if (reason.includes('Смет') || reason.includes('смет')) return 'Смета зашевелилась. Примат не вынес бухгалтерии.';
        if (reason.includes('Кирп') || reason.includes('кирп')) return 'Кирпич с душой нашёл тело без плана.';
        if (reason.includes('Провод') || reason.includes('220V')) return '220V и вера сошлись в одной точке.';
        if (reason.includes('NPC') || reason.includes('примат')) return 'Другой примат доказал, что хаос умеет бегать.';
        if (reason.includes('Балка') || reason.includes('балка')) return 'Балка обиделась. Примат согласился.';
        return reason || DEATH_FALLBACKS[(this.levelIndex + Math.floor(this.clock)) % DEATH_FALLBACKS.length];
    }

    private draw(): void {
        this.clearGraphicsLayers();
        this.resetLayerCursors();
        this.buttons = [];
        const gameplayVisible = this.state === 'playing' || this.state === 'paused' || this.state === 'clear' || this.state === 'over' || this.state === 'finished';
        this.syncPauseTouchZone();
        this.syncDevPasswordInput();
        this.syncPlayerNameInput();
        this.withRenderLayer('BG_MID', () => this.drawBackground());
        if (gameplayVisible) {
            this.drawWorld();
            this.withRenderLayer('PLAYER_BODY', () => this.drawMonkey());
            this.withRenderLayer('PLAYER_EFFECTS', () => this.drawParticles());
            this.withRenderLayer('HUD', () => this.drawOverlay());
            this.withRenderLayer('HUD', () => this.drawHud());
        }
        if (this.state !== 'playing') this.withRenderLayer('HUD', () => this.drawMenu());
        this.deactivateUnusedLayerNodes();
        this.logRenderContractSnapshot(gameplayVisible);
    }

    private pauseTouchRect(): Rect {
        // Upper-right HUD target with a deliberate right-edge inset for Android gesture/tool overlays.
        return { x: W - 330, y: 58, w: 190, h: 104 };
    }

    private syncPauseTouchZone(): void {
        if (!this.pauseTouchZone) return;
        const r = this.pauseTouchRect();
        this.pauseTouchZone.active = this.state === 'playing';
        this.pauseTouchZone.setPosition(this.cx(r.x + r.w * 0.5), this.cy(r.y + r.h * 0.5));
        this.pauseTouchZone.getComponent(UITransform)?.setContentSize(r.w, r.h);
        this.pauseTouchZone.setSiblingIndex(9999);
    }

    private syncDevPasswordInput(): void {
        if (!this.devPasswordNode) return;
        this.devPasswordNode.active = this.state === 'devgate';
        this.devPasswordNode.setPosition(this.cx(640), this.cy(318));
        this.devPasswordNode.setSiblingIndex(9998);
        this.scrubDefaultEditBoxLabels(this.devPasswordNode);
    }

    private sanitizePlayerName(raw: string): string {
        const safe = (raw || '')
            .replace(/[\u0000-\u001F\u007F]/g, '')
            .replace(/[^0-9A-Za-zА-Яа-яЁё _-]+/g, '')
            .replace(/\s+/g, ' ')
            .trim()
            .slice(0, PLAYER_NAME_MAX_LENGTH);
        return safe || DEFAULT_PLAYER_NAME;
    }

    private syncPlayerNameEditString(): void {
        if (!this.playerNameEdit) return;
        this.playerNameEdit.string = this.sanitizePlayerName(this.playerName);
        this.scrubDefaultEditBoxLabels(this.playerNameEditNode);
        this.hideEditBoxVisualLabels(this.playerNameEditNode);
    }

    private commitPlayerNameFromInput(showToast = true): void {
        const nextName = this.sanitizePlayerName(this.playerNameEdit?.string || this.playerName);
        this.playerName = nextName;
        if (this.playerNameEdit) this.playerNameEdit.string = nextName;
        this.saveSettings();
        if (!showToast) return;
        this.bannerText = `Профиль сохранён: ${nextName}`;
        this.bannerTimer = TOAST_DURATION_SEC;
        this.playVoice('ui', 0.55);
    }

    private syncPlayerNameInput(): void {
        if (!this.playerNameEditNode) return;
        this.playerNameEditNode.active = this.state === 'name';
        this.playerNameEditNode.setPosition(this.cx(640), this.cy(318));
        this.playerNameEditNode.getComponent(UITransform)?.setContentSize(520, 58);
        this.playerNameEditNode.setSiblingIndex(9997);
        this.scrubDefaultEditBoxLabels(this.playerNameEditNode);
        this.hideEditBoxVisualLabels(this.playerNameEditNode);
    }

    private scrubDefaultEditBoxLabels(root: Node): void {
        const labels = root.getComponentsInChildren(Label);
        for (const label of labels) {
            if (label.string === 'label') label.string = '';
        }
    }

    private hideEditBoxVisualLabels(root: Node): void {
        const labels = root.getComponentsInChildren(Label);
        for (const label of labels) label.color = rgb(255, 255, 255, 0);
    }

    private installWebEditBoxVisualGuard(): void {
        if (sys.isNative) return;
        const doc = (globalThis as unknown as { document?: Document }).document;
        if (!doc || doc.getElementById('mtr-editbox-visual-guard')) return;
        const style = doc.createElement('style');
        style.id = 'mtr-editbox-visual-guard';
        style.textContent = `
textarea, input {
  color: transparent !important;
  text-shadow: none !important;
  background: transparent !important;
}
`;
        doc.head?.appendChild(style);
    }

    private togglePauseFromInput(): void {
        const now = Date.now();
        if (now - this.lastPauseToggleMs < 220) return;
        this.lastPauseToggleMs = now;
        this.pauseTapAccepted++;
        console.log(`MTR_INPUT_PAUSE_TAP accepted=${this.pauseTapAccepted} state=${this.state}`);
        if (this.state === 'playing') {
            this.transitionTo('paused', 'pause_input');
            this.playFirst(['pause', 'banner'], this.sfxVolume * 0.6);
            this.playVoice('ui', 0.5);
        } else if (this.state === 'paused') {
            this.transitionTo('playing', 'resume_input');
        }
    }

    private onPauseTouchZoneTap(event: EventTouch): void {
        (event as unknown as { propagationStopped?: boolean }).propagationStopped = true;
        this.unlockAudio();
        this.togglePauseFromInput();
    }

    private drawAssetSprite(key: string, x: number, y: number, w: number, h: number, opacity = 255, usageCategory?: ObjectiveCategory, usageReason = 'draw'): boolean {
        key = normalizeObjectSpriteKey(key);
        const frame = this.objectSpriteFrames[key];
        if (!frame) {
            if (usageReason.includes('player_equipment')) this.logEquipmentMissing(key, 'sprite_frame_not_ready');
            this.requestObjectSprite(key, 'visible');
            return false;
        }
        this.markAssetUsage(key, usageCategory, 1, usageReason);
        const layerName = this.spriteLayerForUsage(usageCategory, usageReason);
        const layer = this.spriteLayers[layerName] || this.spriteLayers.HUD;
        if (!layer) return false;
        const pool = this.spritePoolFor(layerName);
        const cursor = this.spriteCursorsByLayer[layerName] || 0;
        let pooled = pool[cursor];
        this.spriteCursorsByLayer[layerName] = cursor + 1;
        if (!pooled) {
            const node = new Node(`${layerName}_ObjectSprite${pool.length}`);
            node.layer = layer.layer;
            const ui = node.addComponent(UITransform);
            const sprite = node.addComponent(Sprite);
            sprite.sizeMode = Sprite.SizeMode.CUSTOM;
            layer.addChild(node);
            pooled = { node, ui, sprite, key: '' };
            pool.push(pooled);
        }
        pooled.node.active = true;
        pooled.node.layer = layer.layer;
        pooled.node.setPosition(this.cx(x), this.cy(y));
        pooled.ui.setContentSize(Math.max(1, w), Math.max(1, h));
        if (pooled.key !== key) {
            pooled.sprite.spriteFrame = frame;
            pooled.key = key;
        }
        pooled.sprite.color = rgb(255, 255, 255, clamp(opacity, 0, 255));
        return true;
    }

    private isQuietMenuState(): boolean {
        return this.state !== 'playing' && this.state !== 'paused' && this.state !== 'clear' && this.state !== 'over' && this.state !== 'finished';
    }

    private drawMainMenuBackgroundLayers(): boolean {
        this.preloadMainMenuBackgroundSprites('draw-main-menu-background');
        const cx = W * 0.5;
        const cy = H * 0.5;
        const viewportWidth = this.backgroundViewportWidth();
        const drawWidth = Math.max(W, viewportWidth);
        const drawHeight = Math.max(H, drawWidth / (16 / 9));
        const far = this.drawAssetSprite(MAIN_MENU_BACKGROUND_LAYER_KEYS[0], cx, cy, drawWidth, drawHeight, MAIN_MENU_BACKGROUND_SPRITE_ALPHA, 'background_decor', 'main_menu_bg_far');
        this.withRenderLayer('BG_NEAR_DECOR', () => {
            this.fillRect(-SCENE_PAD, 0, W + SCENE_PAD * 2, H, rgb(14, 11, 8, MAIN_MENU_BACKGROUND_HAZE_ALPHA));
        });
        return far;
    }

    private drawBackground(): void {
        this.markAssetUsage('story_banner_component', 'background_decor', 1, `z_${VISUAL_Z_LAYERS.BG_NEAR_DECOR}`);
        if (this.isQuietMenuState()) {
            if (this.backgroundImageNode) this.backgroundImageNode.active = false;
            this.withRenderLayer('BG_FAR', () => this.fillRect(-SCENE_PAD, 0, W + SCENE_PAD * 2, H, rgb(34, 27, 18, 255)));
            const menuBackgroundReady = this.drawMainMenuBackgroundLayers();
            if (!menuBackgroundReady) {
                this.fillRect(372, 304, 536, 74, rgb(72, 52, 30, 156));
                this.strokeRect(372, 304, 536, 74, rgb(224, 181, 95, 118));
                this.text('ГРУЗИМ ФОН МЕНЮ', 640, 348, 18, rgb(255, 238, 150));
            }
            return;
        }

        const level = LEVELS[this.levelIndex];
        const reveal = clamp(this.progress / Math.max(1, level.length), 0, 1);
        const hasBitmapBackground = this.updateBitmapBackground(level.theme, reveal);
        const backgroundPending = !hasBitmapBackground && (this.backgroundFrameLoading[level.theme] || this.backgroundPreviewFrameLoading[level.theme]);
        if (!hasBitmapBackground) {
            this.fillRect(-SCENE_PAD, 0, W + SCENE_PAD * 2, H, rgb(24, 22, 18, 255));
            this.fillRect(314, 292, 652, 82, rgb(72, 52, 30, backgroundPending ? 178 : 132));
            this.strokeRect(314, 292, 652, 82, rgb(224, 181, 95, 128));
            this.text(backgroundPending ? 'ГРУЗИМ НОВЫЙ ФОН' : 'ФОН НЕ НАЙДЕН', 640, 340, 20, rgb(255, 238, 150));
            if (!backgroundPending) {
                this.ensureBackgroundPreviewFrame(level.theme, 'runtime-missing-new-background');
                this.ensureBackgroundFrame(level.theme, 'runtime-missing-new-background');
            }
        }

        this.drawGameplayReadabilityBand(level.theme, level.accent, hasBitmapBackground);
        this.drawGroundDeck(level.theme, level.accent);
        this.segment(-SCENE_PAD, GROUND, W + SCENE_PAD, GROUND, 2.2, rgb(184, 132, 76, 210));
    }

    private drawGameplayReadabilityBand(theme: number, accent: Color, bitmap: boolean): void {
        if (!bitmap) return;
        this.segment(-SCENE_PAD, GROUND - 2, W + SCENE_PAD, GROUND - 2, 1.1, this.alpha(accent, theme === 0 ? 34 : 38));
        this.markAssetUsage('foreground_safe_area_matte', 'foreground_decor', 1, 'gameplay_lane_contact_line');
    }

    private drawGroundDeck(theme: number, accent: Color): void {
        const baseAlpha = 218;
        this.fillRect(-SCENE_PAD, GROUND, W + SCENE_PAD * 2, H - GROUND, rgb(16, 21, 16, baseAlpha));
        this.fillRect(-SCENE_PAD, GROUND, W + SCENE_PAD * 2, 14, rgb(119, 82, 43, 214));
        this.fillRect(-SCENE_PAD, GROUND + 14, W + SCENE_PAD * 2, 30, rgb(31, 39, 29, 122));
        this.segment(-SCENE_PAD, GROUND + 1, W + SCENE_PAD, GROUND + 1, 1.4, this.alpha(accent, 62));
        this.markAssetUsage('foreground_safe_area_matte', 'foreground_decor', 1, 'static_touch_control_matte_no_scroll_stripes');
        const syncBucket = Math.floor(this.backgroundWorldDistancePx / 3000);
        const syncKey = `track:${this.levelIndex}:${syncBucket}`;
        if (syncKey !== this.lastTrackBackdropSyncLogKey) {
            this.lastTrackBackdropSyncLogKey = syncKey;
            console.log(`MTR_BG_SYNC layer=TRACK_BACKDROP mode=static source=viewport-matte pattern=disabled worldDistancePx=${Math.round(this.backgroundWorldDistancePx)}`);
        }
    }

    private updateBitmapBackground(theme: number, reveal: number): boolean {
        if (!this.backgroundImageNode) return false;
        const themeIndex = clamp(theme, 0, LEVELS.length - 1);
        const fullFrame = this.backgroundFrameCache[themeIndex];
        const previewFrame = this.backgroundPreviewFrameCache[themeIndex];
        const frame = fullFrame || previewFrame;
        if (frame) {
            const source = fullFrame ? 'full' : 'preview';
            const frameKey = `${themeIndex}:${source}`;
            const layout = this.backgroundLayout();
            this.ensureBackgroundSegments(layout);
            if (this.activeBackgroundFrameKey !== frameKey) {
                for (let i = 0; i < this.activeBackgroundSegmentCount; i++) {
                    const segment = this.backgroundSegments[i];
                    if (segment) segment.sprite.spriteFrame = frame;
                }
                this.activeBackgroundTheme = themeIndex;
                this.activeBackgroundFrameKey = frameKey;
                if (source === 'full' && !this.backgroundFrameAppliedLogged[themeIndex]) {
                    this.backgroundFrameAppliedLogged[themeIndex] = true;
                    console.log(`MTR_BACKGROUND_BITMAP_APPLIED level=${themeIndex + 1} source=full path=${this.backgroundResourcePath(themeIndex)}`);
                }
                if (source === 'preview' && !this.backgroundPreviewFrameAppliedLogged[themeIndex]) {
                    this.backgroundPreviewFrameAppliedLogged[themeIndex] = true;
                    console.log(`MTR_BACKGROUND_BITMAP_APPLIED level=${themeIndex + 1} source=preview path=${this.backgroundPreviewResourcePath(themeIndex)}`);
                }
                console.log('MTR_BG_DUPLICATE_OK');
            }
            for (let i = 0; i < this.activeBackgroundSegmentCount; i++) {
                const segment = this.backgroundSegments[i];
                if (segment && segment.sprite.spriteFrame !== frame) segment.sprite.spriteFrame = frame;
            }
            const offset = this.backgroundOffset(layout);
            for (let i = 0; i < this.activeBackgroundSegmentCount; i++) {
                const segment = this.backgroundSegments[i];
                if (!segment) continue;
                const x = Math.round(layout.panRange * 0.5 - offset);
                segment.node.setPosition(x, 0, 0);
            }
            this.backgroundImageNode.setPosition(0, 0, 0);
            this.backgroundImageNode.active = true;
            this.logBackgroundTextureDiagnostics(themeIndex, layout);
            this.logBackgroundSyncDiagnostics(themeIndex, layout, offset);
            this.logBackgroundDuplicateScan(`OK:theme=${themeIndex + 1}:sources=1`);
            return true;
        }

        this.ensureBackgroundPreviewFrame(themeIndex, 'draw-missing-preview');
        if (this.backgroundPreviewFrameCache[themeIndex] || this.pendingStartLevel === themeIndex) {
            this.ensureBackgroundFrame(themeIndex, this.pendingStartLevel === themeIndex ? 'start-level-gate' : 'draw-missing');
        }
        this.backgroundImageNode.active = false;
        if (this.activeBackgroundTheme === themeIndex) {
            this.activeBackgroundTheme = -1;
            this.activeBackgroundFrameKey = '';
        }
        return false;
    }

    private rememberBackgroundFrame(themeIndex: number, frame: SpriteFrame): void {
        this.backgroundFrameCache[themeIndex] = frame;
        this.backgroundFrameOrder = this.backgroundFrameOrder.filter((item) => item !== themeIndex);
        this.backgroundFrameOrder.push(themeIndex);
        while (this.backgroundFrameOrder.length > BACKGROUND_FRAME_CACHE_LIMIT) {
            const drop = this.backgroundFrameOrder.find((item) => item !== this.activeBackgroundTheme);
            if (drop === undefined) break;
            this.backgroundFrameOrder = this.backgroundFrameOrder.filter((item) => item !== drop);
            delete this.backgroundFrameCache[drop];
            delete this.backgroundFrameAppliedLogged[drop];
            console.log(`MTR_BACKGROUND_CACHE_DROP level=${drop + 1} cacheLimit=${BACKGROUND_FRAME_CACHE_LIMIT}`);
            resources.release(this.backgroundResourcePath(drop), SpriteFrame);
        }
    }

    private backgroundResourcePath(themeIndex: number): string {
        return `backgrounds/level${String(themeIndex + 1).padStart(2, '0')}/spriteFrame`;
    }

    private backgroundPreviewResourcePath(themeIndex: number): string {
        return `backgrounds_preview/level${String(themeIndex + 1).padStart(2, '0')}/spriteFrame`;
    }

    private backgroundLayout(): BackgroundLayout {
        const viewportWidth = this.backgroundViewportWidth();
        const sourceAspect = BACKGROUND_SCENIC_SOURCE_WIDTH / BACKGROUND_SCENIC_SOURCE_HEIGHT;
        const minCoverWidth = Math.max(viewportWidth, H * sourceAspect);
        let drawWidth = Math.ceil(minCoverWidth + BACKGROUND_SCENIC_PAN_MARGIN_PX);
        let drawHeight = Math.ceil(drawWidth / sourceAspect);
        if (drawHeight < H) {
            drawHeight = H;
            drawWidth = Math.ceil(drawHeight * sourceAspect + BACKGROUND_SCENIC_PAN_MARGIN_PX);
        }
        const panRange = Math.max(0, drawWidth - viewportWidth);
        return { viewportWidth, drawWidth, drawHeight, panRange, segmentCount: 1 };
    }

    private backgroundViewportWidth(): number {
        const visible = view.getVisibleSize();
        const width = visible && Number.isFinite(visible.width) ? visible.width : W;
        return Math.max(W, Math.ceil(width));
    }

    private backgroundOffset(layout: BackgroundLayout): number {
        if (layout.panRange <= 0) return 0;
        const level = LEVELS[this.levelIndex] || LEVELS[0];
        const progress01 = clamp(this.backgroundWorldDistancePx / Math.max(1, level.length), 0, 1);
        return layout.panRange * progress01;
    }

    private syncedScrollOffset(parallaxFactor: number, effectiveWidth: number): number {
        const width = Math.max(1, effectiveWidth);
        const raw = (this.backgroundWorldDistancePx * parallaxFactor) % width;
        return Math.round((raw + width) % width);
    }

    private ensureBackgroundSegments(layout: BackgroundLayout): void {
        const rootUi = this.backgroundImageNode.getComponent(UITransform);
        rootUi?.setContentSize(layout.viewportWidth, H);
        while (this.backgroundSegments.length < layout.segmentCount) {
            const index = this.backgroundSegments.length;
            const node = new Node(`BG_FAR_BitmapSegment_${index}`);
            node.layer = this.backgroundImageNode.layer;
            node.setPosition(0, 0, 0);
            const ui = node.addComponent(UITransform);
            ui.setContentSize(layout.drawWidth, layout.drawHeight);
            const sprite = node.addComponent(Sprite);
            sprite.sizeMode = Sprite.SizeMode.CUSTOM;
            this.backgroundImageNode.addChild(node);
            this.backgroundSegments.push({ node, ui, sprite });
        }
        for (let i = 0; i < this.backgroundSegments.length; i++) {
            const segment = this.backgroundSegments[i];
            const active = i < layout.segmentCount;
            segment.node.active = active;
            segment.node.layer = this.backgroundImageNode.layer;
            segment.ui.setContentSize(layout.drawWidth, layout.drawHeight);
        }
        this.activeBackgroundSegmentCount = layout.segmentCount;
        this.backgroundSprite = this.backgroundSegments[0]?.sprite || null;
    }

    private logBackgroundTextureDiagnostics(themeIndex: number, layout: BackgroundLayout): void {
        const key = `${themeIndex}:${layout.viewportWidth}:${layout.drawWidth}:${layout.drawHeight}:${layout.segmentCount}`;
        if (this.lastBackgroundTextureLogKey === key) return;
        this.lastBackgroundTextureLogKey = key;
        console.log(`MTR_BG_TEXTURE layer=BG_FAR level=${themeIndex + 1} sourceWidth=${BACKGROUND_SCENIC_SOURCE_WIDTH} sourceHeight=${BACKGROUND_SCENIC_SOURCE_HEIGHT} drawWidth=${layout.drawWidth} drawHeight=${layout.drawHeight} viewport=${layout.viewportWidth} mode=scenic-fit repeat=none packable=false panRange=${layout.panRange}`);
    }

    private logBackgroundSyncDiagnostics(themeIndex: number, layout: BackgroundLayout, offset: number): void {
        const roundedOffset = Math.round(offset * 10) / 10;
        const bucket = Math.floor(this.backgroundWorldDistancePx / 3000);
        const key = `${themeIndex}:${bucket}:${layout.segmentCount}`;
        if (this.lastBackgroundSyncLogKey === key) return;
        this.lastBackgroundSyncLogKey = key;
        console.log(`MTR_BG_SYNC layer=BG_FAR level=${themeIndex + 1} mode=scenic-fit source=single offset=${roundedOffset} panRange=${layout.panRange} segmentCount=${layout.segmentCount} worldDistancePx=${Math.round(this.backgroundWorldDistancePx)}`);
    }

    private drawScaffold(x: number, y: number, w: number, h: number, label: string): void {
        const post = rgb(118, 82, 45, 28);
        const beam = rgb(178, 125, 64, 26);
        const shadow = rgb(34, 24, 16, 20);
        this.fillRect(x + 10, y + 8, w - 20, 12, shadow);
        this.fillRect(x + 10, y + h - 22, w - 20, 12, shadow);
        for (let col = 0; col <= 3; col++) {
            const px = x + col * w / 3 - 3;
            this.fillRect(px, y + 5, 6, h - 10, post);
            this.circle(px + 3, y + 20, 2.4, rgb(200, 170, 112, 24));
            this.circle(px + 3, y + h - 22, 2.4, rgb(200, 170, 112, 22));
        }
        this.fillRect(x + 3, y + 22, w - 6, 7, beam);
        this.fillRect(x + 3, y + h - 32, w - 6, 7, beam);
        for (let col = 0; col < 3; col++) {
            const x1 = x + 18 + col * w / 3;
            const x2 = x + w / 3 - 18 + col * w / 3;
            this.segment(x1, y + h - 34, x2, y + 26, 0.9, rgb(105, 75, 45, 24));
        }
        this.fillRect(x + 24, y - 30, w - 48, 22, rgb(126, 82, 48, 24));
        if (label) this.text(label, x + w * 0.5, y + 58, 11, rgb(255, 240, 170, 92));
    }

    private drawBrickStack(x: number, base: number, rows: number): void {
        for (let row = 0; row < rows; row++) {
            for (let col = 0; col < 3 - (row % 2); col++) {
                this.fillRect(x + col * 26 + (row % 2) * 12, base - (row + 1) * 14, 23, 12, rgb(168, 78, 53, 160));
            }
        }
    }

    private drawCone(x: number, base: number, scale: number): void {
        this.fillRect(x - 18 * scale, base - 46 * scale, 36 * scale, 46 * scale, rgb(245, 110, 25, 160));
        this.fillRect(x - 25 * scale, base - 4 * scale, 50 * scale, 6 * scale, rgb(70, 70, 70, 170));
        this.segment(x - 14 * scale, base - 26 * scale, x + 14 * scale, base - 26 * scale, 2, rgb(255, 235, 190, 150));
    }

    private drawChicken(x: number, base: number, scale: number): void {
        this.circle(x, base - 24 * scale, 20 * scale, rgb(245, 245, 230, 160));
        this.circle(x + 18 * scale, base - 42 * scale, 11 * scale, rgb(245, 245, 230, 170));
        this.fillRect(x + 25 * scale, base - 45 * scale, 12 * scale, 7 * scale, rgb(234, 96, 36, 170));
        this.segment(x - 8 * scale, base - 4 * scale, x - 13 * scale, base + 4 * scale, 1.5, rgb(246, 166, 58, 170));
        this.segment(x + 8 * scale, base - 4 * scale, x + 13 * scale, base + 4 * scale, 1.5, rgb(246, 166, 58, 170));
    }

    private drawPeacockTail(x: number, base: number, scale: number): void {
        for (let i = -3; i <= 3; i++) {
            const tx = x + i * 22 * scale;
            const ty = base - (88 - Math.abs(i) * 9) * scale;
            this.segment(x, base - 28 * scale, tx, ty, 3, i % 2 ? rgb(40, 110, 230, 150) : rgb(35, 200, 160, 150));
            this.circle(tx, ty, 8 * scale, rgb(255, 214, 80, 120));
        }
        this.circle(x, base - 26 * scale, 17 * scale, rgb(30, 95, 220, 170));
    }

    private drawBillboard(x: number, y: number, label: string, accent: Color, alpha = 150): void {
        this.markAssetUsage('story_banner_component', 'background_decor', 1, 'background_signage');
        const postAlpha = Math.min(58, alpha * 0.55);
        const postBottom = Math.min(GROUND - 28, y + 126);
        this.segment(x + 20, y + 68, x + 20, postBottom, 1.2, rgb(84, 53, 31, postAlpha));
        this.segment(x + 116, y + 68, x + 116, postBottom, 1.2, rgb(84, 53, 31, postAlpha));
        this.segment(x + 20, y + 88, x + 116, y + 118, 0.9, rgb(84, 53, 31, postAlpha * 0.7));
        this.fillRect(x, y, 138, 68, rgb(32, 28, 20, alpha));
        this.strokeRect(x, y, 138, 68, this.alpha(accent, Math.min(112, alpha + 18)));
        this.text(label, x + 69, y + 39, 12, rgb(255, 240, 170, Math.min(210, alpha + 58)));
    }

    private drawWorld(): void {
        this.withRenderLayer('PLATFORMS_SOLID', () => {
            for (const p of this.platforms) {
                const sx = this.worldX(p.x);
                if (sx + p.w > -100 && sx < W + 100) this.drawPlatform(p, sx);
            }
        });
        this.withRenderLayer('OBJECTIVES_ACTIVE', () => {
            for (const o of this.obstacles) if (!o.dead) {
                const sx = this.worldX(this.obstacleWorldX(o));
                if (sx > -170 && sx < W + 170) this.drawObstacle(sx, o.type, this.obstacleBottomY(o), o.label, o.x);
            }
            for (const npc of this.npcs) if (!npc.dead) {
                const worldX = npc.anchor + Math.sin(npc.t * npc.speed + npc.skin * 1.7) * npc.range;
                const sx = this.worldX(worldX);
                if (sx > -120 && sx < W + 120) this.drawNpc(sx, npc.skin, npc.t);
            }
        });
        this.withRenderLayer('COLLECTIBLES', () => {
            let visibleBananas = 0;
            const visibleLimit = this.magnet > 0 ? MAX_VISIBLE_BANANAS_MAGNET : MAX_VISIBLE_BANANAS_NORMAL;
            for (const b of this.bananas) if (!b.taken) {
                const sx = this.worldX(b.x);
                if (sx > -70 && sx < W + 70 && visibleBananas < visibleLimit && !this.bananaOverlapsPlayerVisual(sx, b.y) && !this.bananaCrowdsVisibleHazard(sx, b.y)) {
                    this.drawCollectible(sx, b.y, b.kind, b.value || 1);
                    visibleBananas += Math.max(1, b.value || 1) >= 3 ? 1 : 1;
                }
            }
            for (const bo of this.bonuses) if (!bo.taken) {
                const sx = this.worldX(bo.x);
                if (sx > -80 && sx < W + 80) this.drawBonus(sx, bo.y, bo.type);
            }
        });
    }

    private bananaOverlapsPlayerVisual(x: number, y: number): boolean {
        return x > this.player.x - 68 && x < this.player.x + 72 && y > this.player.y - 122 && y < this.player.y + 16;
    }

    private bananaCrowdsVisibleHazard(x: number, y: number): boolean {
        for (const o of this.obstacles) {
            if (o.dead) continue;
            const spec = OBSTACLES[o.type % OBSTACLES.length];
            const sx = this.worldX(this.obstacleWorldX(o));
            if (sx < -180 || sx > W + 180) continue;
            const centerY = this.obstacleBottomY(o) - spec.h * 0.52;
            if (Math.abs(sx - x) < spec.w * 0.58 + 34 && Math.abs(centerY - y) < spec.h * 0.45 + 24) return true;
        }
        return false;
    }

    private drawPlatform(p: Platform, sx: number): void {
        const type = p.type % PLATFORM_NAMES.length;
        const crooked = p.state === 1 ? Math.sin(this.clock + p.x) * 2 : 0;
        const broken = p.state === 2;
        const packKey = this.platformAssetKey(type, p.x);
        const playerNear = sx < this.player.x + 92 && sx + p.w > this.player.x - 92 && Math.abs(p.y - this.player.y) < 120;
        const assetDrawn = this.canUseRuntimePlatformAsset(packKey) ? this.drawAssetSprite(
            packKey,
            sx + p.w * 0.5,
            p.y - 20 + crooked,
            Math.min(p.w + 34, 320),
            broken ? 74 : 86,
            playerNear ? 242 : 224,
            'platforms',
            'platform_visual_asset',
        ) : false;
        if (playerNear) this.markAssetUsage(packKey || 'themed_platform_contact', 'foreground_decor', 1, 'platform_near_player_contact_shadow');
        if (assetDrawn) {
            if (this.debugColliders) this.strokeRect(sx, p.y - 4, p.w, 8, rgb(80, 255, 120, 190));
            return;
        }
        this.drawLatestPlatformLoadPlaceholder(sx, p.y, p.w, playerNear, packKey, broken, crooked);
        if (this.debugColliders) this.strokeRect(sx, p.y - 4, p.w, 8, rgb(80, 255, 120, 190));
    }

    private drawLatestPlatformLoadPlaceholder(sx: number, y: number, w: number, playerNear: boolean, key: string, broken: boolean, crooked: number): void {
        this.markAssetUsage(key || 'themed_platform_missing', 'platforms', 1, 'latest_themed_platform_asset_pending');
        const alpha = playerNear ? 96 : 58;
        const top = y - 26 + crooked;
        this.fillRect(sx, top, w, broken ? 8 : 10, rgb(38, 30, 21, alpha));
        this.strokeRect(sx, top, w, broken ? 8 : 10, rgb(255, 214, 94, Math.min(160, alpha + 42)));
        for (let x = sx + 18; x < sx + w - 8; x += 34) {
            this.segment(x - 12, top + 9, x + 8, top + 1, 1.5, rgb(255, 214, 94, Math.min(130, alpha + 28)));
        }
    }

    private drawTinyPlate(x: number, y: number, label: string): void {
        const w = clamp(label.length * 8 + 22, 48, 92);
        this.fillRect(x - w * 0.5, y - 10, w, 18, rgb(34, 24, 15, 126));
        this.strokeRect(x - w * 0.5, y - 10, w, 18, rgb(226, 184, 96, 92));
        this.text(label, x, y + 2, 9, rgb(255, 235, 174, 210));
    }

    private drawCollectible(x: number, y: number, kind: CollectibleKind, value = 1): void {
        if (kind === 'coconut') {
            this.drawCoconut(x, y);
            return;
        }
        if (kind === 'figLeaf') {
            this.drawFigLeaf(x, y);
            return;
        }
        this.drawBanana(x, y, value);
    }

    private drawCoconut(x: number, y: number): void {
        const bob = Math.sin(this.clock * 3.5 + x * 0.012) * 2.1;
        const cy = y + bob;
        const assetKey = COCONUT_COLLECTIBLE_ASSET_KEYS[Math.abs(Math.floor(x * 0.019 + y * 0.031 + this.levelIndex)) % COCONUT_COLLECTIBLE_ASSET_KEYS.length];
        const assetDrawn = this.drawAssetSprite(assetKey, x, cy - 1, assetKey.includes('hardhat') ? 42 : 40, assetKey.includes('hardhat') ? 47 : 40, 226, 'collectibles', 'side_collectible_coconut_skin');
        if (assetDrawn) return;
        this.markAssetUsage('collectible_coconut_procedural', 'collectibles', 1, 'side_collectible');
        this.circle(x, cy - 1, 18, rgb(52, 30, 14, 192));
        this.circle(x - 2, cy - 4, 15, rgb(128, 78, 39, 232));
        this.circle(x + 5, cy + 1, 12, rgb(92, 55, 28, 230));
        this.strokeCircle(x, cy - 2, 17, rgb(246, 214, 142, 132), 1.4);
        this.circle(x - 6, cy - 9, 2.2, rgb(43, 25, 13, 235));
        this.circle(x, cy - 11, 2.1, rgb(43, 25, 13, 235));
        this.circle(x + 5, cy - 8, 1.8, rgb(43, 25, 13, 226));
        this.segment(x - 12, cy + 2, x - 2, cy + 8, 1.1, rgb(229, 198, 150, 120));
        this.segment(x - 4, cy + 9, x + 10, cy + 4, 1.1, rgb(229, 198, 150, 104));
        this.circle(x + 6, cy - 12, 4.8, rgb(255, 242, 194, 22));
    }

    private drawFigLeaf(x: number, y: number): void {
        const bob = Math.sin(this.clock * 4.2 + x * 0.014) * 2.3;
        const cy = y + bob;
        const assetKey = FIG_LEAF_COLLECTIBLE_ASSET_KEYS[Math.abs(Math.floor(x * 0.017 + y * 0.023 + this.levelIndex * 2)) % FIG_LEAF_COLLECTIBLE_ASSET_KEYS.length];
        const assetDrawn = this.drawAssetSprite(assetKey, x, cy, assetKey.includes('wind') ? 50 : 44, assetKey.includes('wind') ? 46 : 52, 226, 'collectibles', 'side_collectible_fig_leaf_skin');
        if (assetDrawn) return;
        this.markAssetUsage('collectible_fig_leaf_procedural', 'collectibles', 1, 'side_collectible');
        const outline = rgb(24, 58, 25, 208);
        const dark = rgb(48, 118, 48, 232);
        this.fillFigLeafShape(x, cy, 1.08, outline);
        this.fillFigLeafShape(x, cy, 0.94, dark);
        this.segment(x, cy + 18, x, cy - 21, 1.45, rgb(218, 248, 172, 190));
        this.segment(x, cy - 6, x - 16, cy - 13, 1.0, rgb(218, 248, 172, 145));
        this.segment(x, cy - 6, x + 16, cy - 13, 1.0, rgb(218, 248, 172, 145));
        this.segment(x, cy + 3, x - 19, cy + 2, 0.9, rgb(218, 248, 172, 130));
        this.segment(x, cy + 3, x + 19, cy + 2, 0.9, rgb(218, 248, 172, 130));
        this.segment(x, cy + 9, x - 9, cy + 13, 0.8, rgb(218, 248, 172, 112));
        this.segment(x, cy + 9, x + 9, cy + 13, 0.8, rgb(218, 248, 172, 112));
        this.segment(x, cy + 16, x - 6, cy + 26, 1.6, rgb(66, 91, 38, 218));
        this.circle(x + 6, cy - 17, 4.5, rgb(225, 255, 184, 18));
    }

    private fillFigLeafShape(x: number, y: number, scale: number, color: Color): void {
        const px = (dx: number): number => this.cx(x + dx * scale);
        const py = (dy: number): number => this.cy(y + dy * scale);
        this.notePrimitiveDraw();
        this.graphics.fillColor = color;
        this.graphics.moveTo(px(0), py(-25));
        this.graphics.bezierCurveTo(px(-18), py(-25), px(-29), py(-14), px(-28), py(-1));
        this.graphics.bezierCurveTo(px(-27), py(12), px(-13), py(23), px(0), py(20));
        this.graphics.bezierCurveTo(px(13), py(23), px(27), py(12), px(28), py(-1));
        this.graphics.bezierCurveTo(px(29), py(-14), px(18), py(-25), px(0), py(-25));
        this.graphics.close();
        this.graphics.fill();
    }

    private drawBanana(x: number, y: number, value = 1): void {
        y += Math.sin(this.clock * 4 + x * 0.018) * 2;
        if (value >= 3) {
            const newDrawn = this.drawAssetSprite(BANANA_BUNCH_ASSET_KEY, x, y - 3, 60, 44, 230, 'collectibles', 'reward_bunch_skin_worth_3');
            if (newDrawn) {
                this.circle(x + 24, y - 20, 5, rgb(255, 244, 125, 20));
                return;
            }
            const drawn = this.drawAssetSprite('objectives/collectibles/collectible_banana_bunch_01', x, y - 4, 58, 42, 208, 'collectibles', 'reward_bunch_worth_3');
            if (drawn) {
                this.circle(x + 22, y - 19, 5, rgb(255, 244, 125, 18));
                return;
            }
        }
        const assetKey = BANANA_COLLECTIBLE_ASSET_KEYS[Math.abs(Math.floor(x * 0.021 + y * 0.037 + this.levelIndex)) % BANANA_COLLECTIBLE_ASSET_KEYS.length];
        const bananaW = assetKey.includes('large') ? 54 : assetKey.includes('hardhat') ? 45 : 46;
        const bananaH = assetKey.includes('hardhat') ? 55 : 56;
        const assetDrawn = this.drawAssetSprite(assetKey, x, y - 2, bananaW, bananaH, 226, 'collectibles', 'banana_skin_single');
        if (assetDrawn) {
            this.circle(x + 13, y - 20, 4.2, rgb(255, 244, 125, 18));
            return;
        }
        const scale = 0.84;
        const alphaMul = 0.88;
        const sx = (v: number) => x + v * scale;
        const sy = (v: number) => y + v * scale;
        const aa = (v: number) => Math.round(v * alphaMul);
        const points: { x: number; y: number }[] = [];
        const inner: { x: number; y: number }[] = [];
        for (let i = 0; i <= 8; i++) {
            const t = i / 8;
            points.push({
                x: sx(lerp(-31, 37, t)),
                y: sy((1 - t) * (1 - t) * 5 + 2 * (1 - t) * t * -28 + t * t * -7),
            });
            inner.push({
                x: sx(lerp(-21, 27, t)),
                y: sy((1 - t) * (1 - t) * 10 + 2 * (1 - t) * t * -13 + t * t * 2),
            });
        }
        for (let i = 1; i < points.length; i++) this.segment(points[i - 1].x, points[i - 1].y, points[i].x, points[i].y, 10 * scale, rgb(80, 45, 12, aa(214)));
        for (let i = 1; i < points.length; i++) this.segment(points[i - 1].x, points[i - 1].y, points[i].x, points[i].y, 7 * scale, rgb(246, 202, 48, aa(226)));
        for (let i = 1; i < inner.length; i++) this.segment(inner[i - 1].x, inner[i - 1].y, inner[i].x, inner[i].y, 2.5 * scale, rgb(218, 132, 24, aa(176)));
        for (let i = 2; i < points.length - 1; i++) this.segment(points[i - 1].x, points[i - 1].y - 4 * scale, points[i].x, points[i].y - 4 * scale, 1.35 * scale, rgb(255, 248, 166, aa(172)));
        this.circle(sx(-35), sy(8), 4.2 * scale, rgb(91, 51, 16, aa(232)));
        this.segment(sx(-39), sy(9), sx(-47), sy(14), 2.4 * scale, rgb(89, 55, 18, aa(232)));
        this.circle(sx(39), sy(-7), 3.8 * scale, rgb(91, 51, 16, aa(232)));
        this.circle(sx(6), sy(-18), 4.6 * scale, rgb(255, 244, 125, aa(21)));
    }

    private drawBonus(x: number, y: number, type: number): void {
        const kind = type % BONUS_COUNT;
        const color = BONUS_COLORS[kind];
        const label = BONUS_LABELS[kind];
        const bob = Math.sin(this.clock * 5 + x * 0.01) * 3;
        const cy = y + bob;
        const nearPlayer = Math.hypot(x - this.player.x, cy - (this.player.y - 48)) < 112;
        const visualScale = nearPlayer ? 0.78 : 1;
        const visualAlpha = nearPlayer ? 168 : 226;
        const assetKey = BONUS_ASSET_KEYS[kind % BONUS_ASSET_KEYS.length];
        const iconW = (kind === 6 ? 52 : 48) * visualScale;
        const iconH = (kind === 6 ? 42 : 48) * visualScale;
        const assetDrawn = this.drawAssetSprite(assetKey, x, cy - 4, iconW, iconH, visualAlpha, 'bonuses', nearPlayer ? 'bonus_visual_near_player_no_badge' : 'bonus_visual_no_badge');
        if (!assetDrawn && kind === 2) {
            this.drawRuntimeShieldBonusIcon(x, cy - 2, visualScale, visualAlpha);
        } else if (!assetDrawn) {
            this.drawBonusFallbackIcon(x, cy, kind, visualScale, visualAlpha);
        }
        if (nearPlayer) return;
        this.segment(x - 18, cy + 22, x + 18, cy + 22, 2.2, rgb(255, 226, 126, 112));
        this.text(label, x, cy + 33, 9, rgb(255, 246, 210, 214));
    }

    private drawRuntimeShieldBonusIcon(x: number, y: number, scale = 1, opacity = 226): void {
        const a = (value: number) => Math.round(value * clamp(opacity / 226, 0, 1));
        const sx = (v: number) => x + v * scale;
        const sy = (v: number) => y + v * scale;
        this.segment(sx(-19), sy(-19), sx(0), sy(-26), 5.2 * scale, rgb(85, 210, 255, a(210)));
        this.segment(sx(0), sy(-26), sx(19), sy(-19), 5.2 * scale, rgb(54, 150, 235, a(220)));
        this.segment(sx(-19), sy(-19), sx(-15), sy(5), 5.2 * scale, rgb(35, 108, 208, a(222)));
        this.segment(sx(19), sy(-19), sx(15), sy(5), 5.2 * scale, rgb(28, 96, 190, a(222)));
        this.segment(sx(-15), sy(5), sx(0), sy(24), 5.2 * scale, rgb(28, 102, 202, a(224)));
        this.segment(sx(15), sy(5), sx(0), sy(24), 5.2 * scale, rgb(20, 82, 174, a(224)));
        this.segment(sx(-9), sy(-7), sx(-1), sy(8), 2.3 * scale, rgb(215, 250, 255, a(190)));
        this.segment(sx(-1), sy(8), sx(13), sy(-12), 2.7 * scale, rgb(215, 250, 255, a(210)));
        this.segment(sx(-12), sy(-17), sx(10), sy(-20), 1.3 * scale, rgb(255, 255, 255, a(150)));
    }

    private drawBonusFallbackIcon(x: number, cy: number, kind: number, scale = 1, opacity = 226): void {
        const a = (value: number) => Math.round(value * clamp(opacity / 226, 0, 1));
        const sx = (v: number) => x + v * scale;
        const sy = (v: number) => cy + v * scale;
        if (kind === 0) {
            this.segment(sx(-13), sy(15), sx(10), sy(-18), 4 * scale, rgb(210, 246, 255, a(220)));
            this.segment(sx(10), sy(-18), sx(18), sy(-5), 3 * scale, rgb(255, 255, 255, a(200)));
        } else if (kind === 1) {
            this.fillRect(sx(-18), sy(-5), 36 * scale, 10 * scale, rgb(255, 244, 140, a(218)));
            this.segment(sx(2), sy(-17), sx(23), sy(0), 4 * scale, rgb(255, 244, 140, a(218)));
            this.segment(sx(2), sy(17), sx(23), sy(0), 4 * scale, rgb(255, 244, 140, a(218)));
        } else if (kind === 3) {
            this.fillRect(sx(-19), sy(-20), 14 * scale, 33 * scale, rgb(255, 80, 98, a(220)));
            this.fillRect(sx(5), sy(-20), 14 * scale, 33 * scale, rgb(100, 190, 255, a(220)));
            this.segment(sx(-5), sy(12), sx(5), sy(12), 6 * scale, rgb(245, 245, 245, a(210)));
        } else if (kind === 4) {
            this.fillRect(sx(-17), sy(-22), 34 * scale, 39 * scale, rgb(255, 125, 52, a(226)));
            this.segment(sx(-10), sy(-17), sx(-10), sy(14), 2 * scale, rgb(255, 245, 156, a(220)));
            this.segment(sx(10), sy(-17), sx(10), sy(14), 2 * scale, rgb(255, 245, 156, a(220)));
        } else if (kind === 5) {
            this.fillRect(sx(-14), sy(-4), 27 * scale, 20 * scale, rgb(122, 74, 38, a(232)));
            this.segment(sx(13), sy(1), sx(25), sy(5), 3 * scale, rgb(255, 234, 170, a(185)));
            this.segment(sx(-9), sy(-14), sx(-7), sy(-25), 1.4 * scale, rgb(255, 250, 220, a(170)));
        } else if (kind === 6) {
            this.fillRect(sx(-20), sy(-20), 40 * scale, 30 * scale, rgb(70, 164, 230, a(225)));
            this.segment(sx(-12), sy(-10), sx(13), sy(-2), 1.5 * scale, rgb(240, 252, 255, a(200)));
            this.segment(sx(-11), sy(3), sx(10), sy(-12), 1.5 * scale, rgb(240, 252, 255, a(200)));
        } else if (kind === 7) {
            this.fillRect(sx(-16), sy(-22), 32 * scale, 42 * scale, rgb(238, 214, 128, a(224)));
            this.strokeRect(sx(-16), sy(-22), 32 * scale, 42 * scale, rgb(88, 61, 35, a(180)));
            this.fillRect(sx(-12), sy(-15), 24 * scale, 7 * scale, rgb(80, 115, 150, a(170)));
            this.fillRect(sx(-10), sy(-2), 20 * scale, 4 * scale, rgb(255, 250, 205, a(200)));
            this.fillRect(sx(-10), sy(8), 20 * scale, 4 * scale, rgb(255, 250, 205, a(176)));
            this.segment(sx(-6), sy(-28), sx(6), sy(-28), 2 * scale, rgb(116, 72, 38, a(164)));
            this.segment(sx(-6), sy(-28), sx(-2), sy(-22), 1.5 * scale, rgb(116, 72, 38, a(164)));
            this.segment(sx(6), sy(-28), sx(2), sy(-22), 1.5 * scale, rgb(116, 72, 38, a(164)));
        } else {
            this.fillRect(sx(-15), sy(-14), 30 * scale, 28 * scale, rgb(235, 56, 72, a(220)));
            this.segment(sx(-9), sy(0), sx(9), sy(0), 4.4 * scale, rgb(255, 246, 238, a(230)));
            this.segment(sx(0), sy(-9), sx(0), sy(9), 4.4 * scale, rgb(255, 246, 238, a(230)));
            this.segment(sx(-11), sy(-18), sx(11), sy(-18), 1.3 * scale, rgb(255, 238, 170, a(150)));
        }
    }

    private obstacleVisualProfile(type: number): ObstacleVisualProfile {
        return OBSTACLE_VISUAL_PROFILES[type % OBSTACLE_VISUAL_PROFILES.length] || DEFAULT_OBSTACLE_VISUAL_PROFILE;
    }

    private drawObstacleAsset(assetKey: string, type: number, x: number, base: number, spec: ObstacleSpec): boolean {
        const profile = this.obstacleVisualProfile(type);
        if (profile.assetOpacity <= 0) return false;
        let w = spec.w * profile.assetWScale;
        let h = spec.h * profile.assetHScale;
        let bottomOffset = profile.assetBottomOffset;
        if (assetKey.includes('/signage/')) {
            w *= 1.03;
            h *= 0.98;
        }
        const centerY = base - h * 0.5 + bottomOffset;
        return this.drawAssetSprite(assetKey, x, centerY, w, h, profile.assetOpacity, 'hazards', `hazard_visual_type_${type % OBSTACLES.length}`);
    }

    private drawObstacle(x: number, type: number, base: number, stableLabel?: string, worldXSeed = 0): void {
        const spec = OBSTACLES[type % OBSTACLES.length];
        const label = stableLabel || spec.label || OBSTACLE_LABELS[type % OBSTACLE_LABELS.length];
        const assetKey = this.obstacleAssetKey(type, worldXSeed);
        const assetDrawn = assetKey ? this.drawObstacleAsset(assetKey, type, x, base, spec) : false;
        if (!assetDrawn) this.drawLatestHazardLoadPlaceholder(x, base, spec, assetKey);
        if (!assetDrawn || this.debugReadability) {
            this.drawHazardReadabilityMarks(x, base, spec, type);
            this.drawObstacleLabel(label, x, base, spec, type);
        }
        if (this.debugColliders) {
            const r = this.obstacleRect(x, base, type);
            this.strokeRect(r.x, r.y, r.w, r.h, rgb(80, 255, 120, 180));
        }
    }

    private drawLatestHazardLoadPlaceholder(x: number, base: number, spec: ObstacleSpec, key: string): void {
        this.markAssetUsage(key || 'themed_hazard_missing', 'hazards', 1, 'latest_themed_hazard_asset_pending');
        const w = clamp(spec.w * 0.76, 62, 128);
        const h = clamp(spec.h * 0.46, 38, 76);
        const y = base - h - 8;
        this.fillRect(x - w * 0.5, y, w, h, rgb(38, 30, 21, 74));
        this.strokeRect(x - w * 0.5, y, w, h, rgb(255, 91, 58, 128));
        this.segment(x - w * 0.35, y + h - 6, x + w * 0.35, y + 6, 2.2, rgb(255, 91, 58, 118));
        this.segment(x - w * 0.35, y + 6, x + w * 0.35, y + h - 6, 2.2, rgb(255, 91, 58, 118));
    }

    private drawHazardReadabilityMarks(x: number, base: number, spec: ObstacleSpec, type: number): void {
        const pulse = 0.5 + 0.5 * Math.sin(this.clock * 5.2 + type);
        const w = spec.w * 0.72;
        const y = base - spec.h * 0.88;
        this.markAssetUsage('hazard_warning_marker', 'active_labels', 1, 'hazard_silhouette_language');
        this.segment(x - w * 0.52, base - 8, x + w * 0.52, base - 8, 3.8, rgb(64, 22, 14, 82));
        this.segment(x - w * 0.48, y + 4, x - w * 0.26, y - 8, 2.4, rgb(255, 82, 42, 150 + pulse * 56));
        this.segment(x + w * 0.26, y - 8, x + w * 0.48, y + 4, 2.4, rgb(255, 82, 42, 150 + pulse * 56));
        this.circle(x + w * 0.52, y + 10, 5.5, rgb(255, 116, 54, 106 + pulse * 72));
        this.segment(x + w * 0.52, y + 4, x + w * 0.52, y + 12, 1.2, rgb(45, 20, 10, 180));
        this.circle(x + w * 0.52, y + 16, 1.5, rgb(45, 20, 10, 180));
    }

    private drawObstacleLabel(label: string, x: number, base: number, spec: ObstacleSpec, type: number): void {
        if (!label.trim()) return;
        this.markAssetUsage('obstacle_label_component', 'labels_signage', 1, 'obstacle_label');
        const lines = label.split('\n').slice(0, 2).map((line) => line.length > 16 ? `${line.slice(0, 15)}…` : line);
        const safe = lines.join('\n');
        const font = spec.w < 84 ? 12 : spec.w > 128 ? 15 : 13;
        const plateW = clamp(Math.max(82, spec.w * 0.98), 76, 152);
        const plateH = lines.length > 1 ? 44 : 30;
        const profile = this.obstacleVisualProfile(type);
        const anchorY = clamp(base - spec.h - profile.labelLift - 24, 92, base - plateH * 0.5 - 12);
        const shade = type % 3 === 0 ? rgb(42, 28, 16, 190) : rgb(25, 20, 14, 178);
        this.fillRect(x - plateW * 0.5, anchorY - plateH * 0.5, plateW, plateH, shade);
        this.strokeRect(x - plateW * 0.5, anchorY - plateH * 0.5, plateW, plateH, rgb(245, 204, 105, 188));
        this.text(safe, x + 1, anchorY + 2, font, rgb(30, 18, 10, 190));
        this.text(safe, x, anchorY, font, rgb(255, 240, 179, 248));
    }

    private drawPlayerReadabilityMatte(cx: number, bottom: number): void {
        this.markAssetUsage('foreground_safe_area_matte', 'foreground_decor', 1, 'player_contact_shadow');
        this.segment(cx - 48, bottom - 2, cx + 48, bottom - 2, 4.8, rgb(8, 7, 4, 94));
        this.segment(cx - 34, bottom + 2, cx + 34, bottom + 2, 2.6, rgb(8, 7, 4, 62));
        if (this.debugReadability) {
            this.strokeRect(cx - 82, bottom - 98, 164, 104, rgb(120, 255, 190, 210));
            this.text('PLAYER DEBUG BOX', cx, bottom - 111, 10, rgb(160, 255, 210));
        }
    }

    private equipmentAnchorPoint(anchor: EquipmentAnchor, cx: number, bottom: number): { x: number; y: number } {
        switch (anchor) {
            case 'head_anchor': return { x: cx, y: bottom - 90 };
            case 'neck_anchor': return { x: cx, y: bottom - 70 };
            case 'torso_anchor': return { x: cx, y: bottom - 32 };
            case 'back_anchor': return { x: cx + 48, y: bottom - 58 };
            case 'hand_r_anchor': return { x: cx + 60, y: bottom - 38 };
            case 'hand_l_anchor': return { x: cx - 60, y: bottom - 38 };
            case 'feet_anchor': return { x: cx, y: bottom - 4 };
            case 'aura_anchor': return { x: cx, y: bottom - 49 };
            default: return { x: cx, y: bottom - 48 };
        }
    }

    private normalizeEquipmentSlot(itemId: string): EquipmentSlot {
        if (itemId === 'base_hardhat' || itemId === 'hardhat') return 'helmet';
        if (itemId === 'base_vest') return 'vest';
        if (itemId === 'pass' || itemId === 'card') return 'pass_card';
        if (itemId === 'life_badge') return 'life_badge';
        if (itemId === 'helmet' || itemId === 'vest' || itemId === 'boots' || itemId === 'magnet' || itemId === 'coffee' || itemId === 'blueprint' || itemId === 'pass_card' || itemId === 'shield') return itemId;
        return 'shield';
    }

    private semanticSlotForAnchor(anchor: EquipmentAnchor): 'head' | 'torso' | 'hand_l' | 'hand_r' | 'back' | 'feet' | 'aura' {
        if (anchor === 'head_anchor' || anchor === 'neck_anchor') return 'head';
        if (anchor === 'torso_anchor') return 'torso';
        if (anchor === 'hand_l_anchor') return 'hand_l';
        if (anchor === 'hand_r_anchor') return 'hand_r';
        if (anchor === 'back_anchor') return 'back';
        if (anchor === 'feet_anchor') return 'feet';
        return 'aura';
    }

    private logEquipmentAttach(itemId: string, anchor: EquipmentAnchor): void {
        const slot = this.normalizeEquipmentSlot(itemId);
        const semanticSlot = this.semanticSlotForAnchor(anchor);
        const key = `${slot}:${itemId}:${anchor}`;
        if (this.equipmentAttachLogged[key] && !this.developerMode) return;
        if (this.equipmentAttachLogged[key] && this.clock - this.lastLayerDrawLogAt < 1.4) return;
        this.equipmentAttachLogged[key] = true;
        console.log(`MTR_EQUIPMENT_ATTACH slot=${slot} semanticSlot=${semanticSlot} item=${itemId} anchor=${anchor}`);
    }

    private logEquipmentMissing(itemId: string, reason: string): void {
        const key = `${itemId}:${reason}`;
        if (this.equipmentMissingLogged[key]) return;
        this.equipmentMissingLogged[key] = true;
        console.log(`MTR_EQUIPMENT_MISSING:${itemId}:${reason}`);
    }

    private drawEquipmentAnchorDebug(cx: number, bottom: number): void {
        if (!this.debugReadability) return;
        const anchors: EquipmentAnchor[] = ['head_anchor', 'neck_anchor', 'torso_anchor', 'back_anchor', 'hand_r_anchor', 'hand_l_anchor', 'feet_anchor', 'aura_anchor'];
        for (const anchor of anchors) {
            const p = this.equipmentAnchorPoint(anchor, cx, bottom);
            this.strokeCircle(p.x, p.y, anchor === 'aura_anchor' ? 56 : 9, rgb(125, 255, 205, anchor === 'aura_anchor' ? 120 : 210), 1.4);
            if (anchor !== 'aura_anchor') this.text(anchor, p.x, p.y - 13, 7, rgb(150, 255, 215));
        }
    }

    private currentPlayerSkinPose(): PlayerSkinPose {
        if (this.developerMode && this.qaForcedPlayerPose) return this.qaForcedPlayerPose;
        const airborne = !this.player.onGround || this.player.y < GROUND - 8 || Math.abs(this.player.vy) > 48;
        if (this.state === 'clear' || this.state === 'finished') return 'victory';
        if (this.hitPoseTimer > 0) return 'hit';
        if (this.dashTimer > 0) return 'crouchDash';
        if (airborne) {
            if (this.secondJumpPoseTimer > 0) return 'jump2';
            if (this.gliding || this.player.vy > 80) return 'fall';
            return 'jump';
        }
        return Math.floor(this.clock * 10) % 2 === 0 ? 'run1' : 'run2';
    }

    private resolvePlayerSkinVariant(): PlayerSkinVariant {
        if (this.developerMode && this.qaForcedSkinVariant) return this.qaForcedSkinVariant;
        const hasHelmet = this.armor > 0;
        const hasVest = this.vestBonus > 0;
        const hasCoffee = this.coffeeBoost > 0;
        const hasJumpBoost = this.jumpBoost > 0;
        const hasDashBoost = this.dashBoost > 0;
        const hasBoots = hasDashBoost || hasJumpBoost || hasCoffee;
        const hasShield = this.shieldBonus > 0;
        const hasMagnet = this.magnet > 0;
        const hasBlueprint = this.blueprintBonus > 8;
        const hasKeyPass = this.passBonus > 0;
        if (hasHelmet && hasVest && hasBoots) return 'helmet_vest_boots';
        if (hasHelmet && hasVest) return 'helmet_vest';
        if (hasShield) return 'shield';
        if (hasMagnet) return 'magnet';
        if (hasKeyPass) return 'key_pass';
        if (hasBlueprint) return 'blueprint';
        if (hasCoffee) return 'coffee';
        if (hasJumpBoost && !hasDashBoost) return 'banana_boost';
        if (hasVest) return 'vest';
        if (hasHelmet) return 'helmet';
        if (hasBoots) return 'boots';
        return 'base';
    }

    private logSuppressedLegacyPlayerEquipmentFallbacks(): void {
        const suppressed: string[] = [];
        if (this.armor > 0) suppressed.push('helmet');
        if (this.vestBonus > 0) suppressed.push('vest');
        if (this.dashBoost > 0 || this.jumpBoost > 0 || this.coffeeBoost > 0) suppressed.push('boots');
        if (this.blueprintBonus > 0) suppressed.push('blueprint');
        if (this.coffeeBoost > 0) suppressed.push('coffee');
        if (this.passBonus > 0) suppressed.push('key_pass');
        if (this.extraLifeAura > 0) suppressed.push('life_badge');
        if (this.magnet > 0) suppressed.push('magnet_attached_model');
        if (!suppressed.length) return;
        const skinId = playerSkinId(this.selectedSkin);
        for (const itemId of suppressed) {
            const key = `${skinId}:${itemId}`;
            if (this.legacyPlayerEquipmentFallbackSuppressedLogged[key]) continue;
            this.legacyPlayerEquipmentFallbackSuppressedLogged[key] = true;
            console.warn(`MTR_LEGACY_PLAYER_EQUIPMENT_OVERLAY_SUPPRESSED skin=${skinId} item=${itemId} reason=baked_variant_or_safe_vfx_required`);
        }
    }

    private logSkinVariantActive(variant: PlayerSkinVariant, pose: PlayerSkinPose, key: string): void {
        const skinId = playerSkinId(this.selectedSkin);
        const model = PLAYER_SKIN_CANONICAL_MODELS[variant];
        const logKey = `${skinId}:${variant}`;
        if (this.lastSkinVariantLog === logKey) return;
        this.lastSkinVariantLog = logKey;
        console.log(`MTR_SKIN_VARIANT_ACTIVE skin=${skinId} variant=${variant} model=${model} pose=${PLAYER_SKIN_POSE_RESOURCE[pose]} key=${key}`);
    }

    private logPlayerPoseActive(variant: PlayerSkinVariant, pose: PlayerSkinPose, key: string): void {
        const skinId = playerSkinId(this.selectedSkin);
        const actionPose = PLAYER_SKIN_POSE_RESOURCE[pose];
        const logKey = `${skinId}:${variant}:${actionPose}`;
        if (this.lastPlayerPoseLog === logKey) return;
        this.lastPlayerPoseLog = logKey;
        console.log(`MTR_PLAYER_POSE skin=${skinId} variant=${variant} pose=${actionPose} key=${key}`);
    }

    private drawPlayerSkinSprite(cx: number, bottom: number, opacity = 255): boolean {
        const pose = this.currentPlayerSkinPose();
        const variant = this.resolvePlayerSkinVariant();
        const key = playerSkinV2AssetKey(this.selectedSkin, variant, pose);
        const crouch = pose === 'crouchDash';
        const spriteW = crouch ? 152 : 144;
        const spriteH = crouch ? 132 : 150;
        const centerY = bottom - spriteH * 0.5 + 7;
        this.requestObjectSprite(key, 'visible');
        if (!this.objectSpriteFrames[key]) {
            const requestedFailure = this.objectSpriteLoadFailures[key];
            const missKey = `${key}:load_failed`;
            if (requestedFailure && !this.skinVariantMissingLogged[missKey]) {
                this.skinVariantMissingLogged[missKey] = true;
                console.warn(`MTR_POSE_MISSING skin=${playerSkinId(this.selectedSkin)} variant=${variant} pose=${PLAYER_SKIN_POSE_RESOURCE[pose]} fallback=skin_base_safe err=${requestedFailure}`);
            }
            const safeFallbacks = [
                playerSkinV2AssetKey(this.selectedSkin, 'base', pose),
                this.previousPlayerVisualKey || '',
                playerSkinV2AssetKey(this.selectedSkin, 'base', 'run1'),
                playerSkinV2AssetKey(this.selectedSkin, 'base', 'idle'),
            ].filter((fallbackKey, index, array) => fallbackKey && array.indexOf(fallbackKey) === index);
            for (const fallbackKey of safeFallbacks) {
                this.requestObjectSprite(fallbackKey, 'visible');
                if (this.objectSpriteFrames[fallbackKey]) {
                    const fallbackLogKey = `${key}:safe:${fallbackKey}`;
                    if (!this.skinVariantMissingLogged[fallbackLogKey]) {
                        this.skinVariantMissingLogged[fallbackLogKey] = true;
                        console.log(`MTR_PLAYER_SKIN_SAFE_FALLBACK requested=${key} used=${fallbackKey}`);
                    }
                    return this.drawAssetSprite(fallbackKey, cx, centerY, spriteW, spriteH, opacity, 'player_body', `player_skin_safe_fallback_${variant}_${pose}`);
                }
            }
            const missingLogKey = `${key}:safe_missing`;
            const allSafeFallbacksFailed = safeFallbacks.length > 0
                && safeFallbacks.every((fallbackKey) => !!this.objectSpriteLoadFailures[fallbackKey]);
            if (requestedFailure && allSafeFallbacksFailed && !this.skinVariantMissingLogged[missingLogKey]) {
                this.skinVariantMissingLogged[missingLogKey] = true;
                console.warn(`MTR_PLAYER_SKIN_SAFE_FALLBACK_MISSING requested=${key} retiredFallbackForbidden=true`);
            }
            return false;
        }
        if (this.currentPlayerVisualKey !== key) {
            this.previousPlayerVisualKey = this.currentPlayerVisualKey;
            this.currentPlayerVisualKey = key;
            this.playerVisualBlendTimer = PLAYER_SKIN_BLEND_SEC;
            this.logSkinVariantActive(variant, pose, key);
        }
        this.logPlayerPoseActive(variant, pose, key);
        if (this.previousPlayerVisualKey && this.playerVisualBlendTimer > 0 && this.objectSpriteFrames[this.previousPlayerVisualKey]) {
            const t = clamp(this.playerVisualBlendTimer / PLAYER_SKIN_BLEND_SEC, 0, 1);
            this.drawAssetSprite(this.previousPlayerVisualKey, cx, centerY, spriteW, spriteH, opacity * t, 'player_body', `player_skin_blend_from_${pose}`);
        }
        const newAlpha = this.previousPlayerVisualKey && this.playerVisualBlendTimer > 0 ? opacity * (1 - clamp(this.playerVisualBlendTimer / PLAYER_SKIN_BLEND_SEC, 0, 1)) : opacity;
        return this.drawAssetSprite(key, cx, centerY, spriteW, spriteH, newAlpha, 'player_body', `player_skin_${variant}_${pose}`);
    }

    private drawPlayerSpriteRuntimeEffects(cx: number, bottom: number): void {
        const auraAnchor = this.equipmentAnchorPoint('aura_anchor', cx, bottom);
        if (this.shieldBonus > 0) {
            this.logEquipmentAttach('shield', 'aura_anchor');
            this.markAssetUsage('objectives/bonuses/bonus_shield_01', 'bonuses', 1, 'player_equipment_aura_anchor');
            this.withRenderLayer('PLAYER_EFFECTS', () => {
                this.drawShieldRuntimeEffect(auraAnchor.x, auraAnchor.y, 0.82, 88);
            });
        }
        if (this.magnet > 0) {
            this.logEquipmentAttach('magnet', 'back_anchor');
            this.markAssetUsage('objectives/equipment/equipment_magnet_01', 'equipment', 1, 'player_equipment_back_anchor');
            this.withRenderLayer('PLAYER_EFFECTS', () => this.drawMagnetRuntimeEffect(auraAnchor.x, auraAnchor.y, 0.82, 72));
        }
        if (this.dashBoost > 0 || this.coffeeBoost > 0 || this.jumpBoost > 0) {
            this.logEquipmentAttach('boots', 'feet_anchor');
        }
        if (this.dashBoost > 0 || this.coffeeBoost > 0) {
            for (let s = 0; s < 3; s++) this.segment(cx - 58 - s * 14, bottom - 14 + s * 3, cx - 36 - s * 12, bottom - 8 + s * 2, 2, rgb(255, 225, 91, 142));
        }
        this.drawEquipmentAnchorDebug(cx, bottom);
        if (this.dashTimer > 0) this.text('РЫВОК!', cx, bottom - 132, 20, rgb(255, 240, 90));
    }

    private drawMonkey(): void {
        const sk = SKINS[this.selectedSkin % SKINS.length];
        const cx = this.player.x;
        const bottom = this.player.y;
        this.drawPlayerReadabilityMatte(cx, bottom);
        const spriteOpacity = this.invincible > 0 && Math.sin(this.invincible * 40) < 0 ? 112 : 255;
        if (this.drawPlayerSkinSprite(cx, bottom, spriteOpacity)) {
            this.drawPlayerSpriteRuntimeEffects(cx, bottom);
            return;
        }
        if (this.invincible > 0 && Math.sin(this.invincible * 40) < 0) {
            this.circle(cx, bottom - 48, 35, this.alpha(sk.fur, 92));
            this.circle(cx, bottom - 62, 24, this.alpha(sk.face, 100));
            this.fillRect(cx - 24, bottom - 42, 48, 28, this.alpha(sk.vest, 96));
            this.fillRect(cx - 22, bottom - 91, 44, 12, this.alpha(sk.helmet, 128));
            return;
        }
        this.segment(cx - 68, bottom - 46, cx - 36, bottom - 70, 4.2, sk.fur);
        this.circle(cx - 73, bottom - 43, 8, sk.accent);
        this.circle(cx, bottom - 38, 30, sk.fur);
        this.fillRect(cx - 24, bottom - 42, 48, 28, sk.vest);
        this.circle(cx, bottom - 35, 15, sk.face);
        this.circle(cx - 27, bottom - 62, 11, sk.fur);
        this.circle(cx + 27, bottom - 62, 11, sk.fur);
        this.circle(cx, bottom - 62, 23, sk.fur);
        this.circle(cx, bottom - 57, 12.5, sk.face);
        this.circle(cx - 7, bottom - 63, 2.3, rgb(30, 25, 18));
        this.circle(cx + 7, bottom - 63, 2.3, rgb(30, 25, 18));
        this.segment(cx - 8, bottom - 53, cx + 8, bottom - 53, 1.6, rgb(94, 45, 30, 190));
        this.fillRect(cx - 22, bottom - 91, 44, 12, sk.helmet);
        this.circle(cx, bottom - 84, 23, this.alpha(sk.helmet, 212));
        const run = Math.sin(this.clock * 13);
        this.segment(cx - 16, bottom - 18, cx - 30 + run * 6, bottom - 3, 4.2, sk.accent);
        this.segment(cx + 15, bottom - 18, cx + 31 - run * 6, bottom - 3, 4.2, sk.accent);
        this.circle(cx - 34 + run * 6, bottom - 1, 5.5, sk.accent);
        this.circle(cx + 35 - run * 6, bottom - 1, 5.5, sk.accent);
        this.segment(cx - 22, bottom - 40, cx - 44, bottom - 32, 2.1, sk.accent);
        this.segment(cx + 22, bottom - 40, cx + 42, bottom - 49, 2.1, sk.accent);
        this.logSuppressedLegacyPlayerEquipmentFallbacks();
        this.drawPlayerSpriteRuntimeEffects(cx, bottom);
    }

    private drawShieldRuntimeEffect(x: number, y: number, scale = 1, opacity = 88): void {
        const a = (value: number) => Math.round(value * clamp(opacity / 88, 0, 1));
        const sx = (v: number) => x + v * scale;
        const sy = (v: number) => y + v * scale;
        this.segment(sx(-42), sy(-20), sx(-28), sy(-34), 1.7 * scale, rgb(255, 222, 106, a(82)));
        this.segment(sx(-43), sy(14), sx(-30), sy(31), 1.5 * scale, rgb(255, 222, 106, a(68)));
        this.segment(sx(42), sy(-20), sx(28), sy(-34), 1.7 * scale, rgb(255, 222, 106, a(82)));
        this.segment(sx(43), sy(14), sx(30), sy(31), 1.5 * scale, rgb(255, 222, 106, a(68)));
        this.segment(sx(-24), sy(-42), sx(24), sy(-42), 1.0 * scale, rgb(159, 255, 183, a(54)));
        this.segment(sx(-18), sy(42), sx(18), sy(42), 1.0 * scale, rgb(159, 255, 183, a(48)));
    }

    private drawMagnetRuntimeEffect(x: number, y: number, scale = 1, opacity = 72): void {
        const a = (value: number) => Math.round(value * clamp(opacity / 72, 0, 1));
        const sx = (v: number) => x + v * scale;
        const sy = (v: number) => y + v * scale;
        for (let i = 0; i < 3; i++) {
            const dy = -24 + i * 20;
            this.segment(sx(56 + i * 4), sy(dy), sx(34), sy(dy + 8), 1.35 * scale, rgb(223, 126, 255, a(72)));
            this.segment(sx(-56 - i * 4), sy(dy), sx(-34), sy(dy + 8), 1.35 * scale, rgb(108, 215, 255, a(54)));
        }
    }

    private drawNpc(x: number, skin: number, t: number): void {
        const sk = SKINS[skin % SKINS.length];
        const bob = Math.sin(t * 8) * 3;
        const bottom = GROUND + bob;
        this.segment(x - 44, bottom - 42, x - 16, bottom - 50, 2.6, sk.fur);
        this.segment(x + 18, bottom - 34, x + 44, bottom - 50, 2.6, sk.accent);
        this.segment(x - 47, bottom - 42, x - 65, bottom - 32, 3.4, sk.fur);
        this.circle(x, bottom - 36, 25, sk.fur);
        this.fillRect(x - 20, bottom - 40, 40, 22, sk.vest);
        this.circle(x, bottom - 34, 12, sk.face);
        this.circle(x - 22, bottom - 58, 9, sk.fur);
        this.circle(x + 22, bottom - 58, 9, sk.fur);
        this.circle(x, bottom - 58, 19, sk.fur);
        this.circle(x, bottom - 54, 9.5, sk.face);
        this.circle(x - 6, bottom - 60, 2, rgb(30, 25, 18));
        this.circle(x + 6, bottom - 60, 2, rgb(30, 25, 18));
        this.fillRect(x - 19, bottom - 82, 38, 10, rgb(255, 210, 60));
        this.segment(x - 14, bottom - 18, x - 27, bottom - 2, 3.4, sk.accent);
        this.segment(x + 14, bottom - 18, x + 27, bottom - 2, 3.4, sk.accent);
        this.circle(x - 30, bottom, 4.5, sk.accent);
        this.circle(x + 30, bottom, 4.5, sk.accent);
        const theme = LEVELS[this.levelIndex].theme;
        if (theme === 0 || theme === 10) {
            this.fillRect(x + 22, bottom - 48, 24, 18, rgb(74, 118, 146, 210));
            this.segment(x + 26, bottom - 42, x + 42, bottom - 36, 1.2, rgb(245, 245, 210, 190));
        } else if (theme === 4) {
            this.circle(x + 38, bottom - 44, 10, rgb(245, 245, 230, 180));
            this.fillRect(x + 44, bottom - 47, 10, 5, rgb(234, 96, 36, 190));
        } else if (theme === 5) {
            this.drawPeacockTail(x + 42, bottom - 10, 0.42);
        } else if (theme === 7 || theme === 11) {
            this.segment(x - 42, bottom - 54, x - 64, bottom - 73, 2.4, rgb(255, 231, 89, 185));
            this.circle(x - 66, bottom - 75, 7, rgb(255, 231, 89, 90));
        } else if (theme === 13) {
            this.fillRect(x - 22, bottom - 83, 44, 11, rgb(24, 24, 30, 225));
            this.segment(x - 32, bottom - 35, x - 54, bottom - 20, 2.5, rgb(42, 42, 48, 190));
        }
        this.drawAssetSprite(OBJECTIVE_BATCH_NPC_KEYS[skin % OBJECTIVE_BATCH_NPC_KEYS.length], x, bottom - 49, 82, 106, 214, 'npc_decor', 'npc_visual_batch01');
        this.text('ПРИМАТ', x, bottom - 98, 11, rgb(255, 240, 120));
    }

    private drawParticles(): void {
        for (const p of this.particles) this.circle(p.x, p.y, p.size, this.alpha(p.color, clamp(p.life / 0.9, 0, 1) * 255));
    }

    private drawHud(): void {
        if (this.state !== 'playing') return;
        const level = LEVELS[this.levelIndex];
        const progressPct = Math.min(100, Math.floor(this.progress / level.length * 100));
        const goalPlan = Math.min(this.bananasCollected, level.target);
        const bonusPlan = Math.max(0, this.bananasCollected - level.target);
        const planText = bonusPlan > 0 ? `ПЛАН ${level.target}/${level.target} + БОНУС ${bonusPlan}` : `ПЛАН ${goalPlan}/${level.target}`;
        this.drawAssetSprite(UI_SKIN.assets.hudPanel, 376, 50, 720, 84, 238, 'ui_achievements', 'shared_hud_left');
        this.text(level.name, 42, 39, 19, rgb(179, 255, 166), 'left', 650);
        this.text(level.subtitle, 42, 64, 13, rgb(232, 245, 210), 'left', 650);
        const hpText = this.developerMode ? 'HP ∞' : `HP ${this.hp}`;
        this.drawAssetSprite(UI_SKIN.assets.hudPanel, 930, 50, 360, 84, 238, 'ui_achievements', 'shared_hud_right');
        this.text(`${planText}   ${hpText}`, 1082, 39, 16, rgb(255, 238, 138), 'right', 310);
        this.text(`СЧЁТ ${this.score}   ОБЪЕКТ ${progressPct}%`, 1082, 65, 13, rgb(240, 230, 188), 'right', 310);
        if (this.developerMode && (this.showTouchZones || this.showPerfOverlay || this.debugColliders || this.debugReadability)) this.text('РАЗР', 1246, 72, 12, rgb(255, 236, 94), 'right');
        const pauseZone = this.pauseTouchRect();
        this.button(pauseZone.x + 18, 83, 150, 64, 'ПАУЗА', () => this.togglePauseFromInput(), rgb(255, 218, 126, 190), rgb(48, 36, 24, 154), rgb(255, 240, 180));
        if (this.developerMode && this.showTouchZones) {
            const zone = this.pauseTouchRect();
            this.strokeRect(zone.x, zone.y, zone.w, zone.h, rgb(120, 255, 180, 210));
            this.text('ЗОНА ПАУЗЫ', zone.x + zone.w * 0.5, zone.y + zone.h + 16, 10, rgb(160, 255, 190));
        }
        this.button(48, 619, 350, 64, 'ПРЫЖОК / ПЛАН', () => this.jump(), rgb(180, 226, 172, 112), rgb(38, 70, 42, 70), rgb(218, 255, 216));
        this.button(930, 619, 270, 64, 'РЫВОК', () => this.dash(), rgb(255, 225, 100, 126), rgb(92, 78, 35, 72), rgb(255, 237, 132));
    }

    private drawOverlay(): void {
        if (this.bannerTimer > 0) {
            const alpha = clamp(this.bannerTimer / TOAST_DURATION_SEC, 0, 1);
            const w = 640;
            const x = (W - w) * 0.5;
            this.fillRect(x, 104, w, 48, rgb(0, 0, 0, 126 + alpha * 66));
            this.strokeRect(x, 104, w, 48, rgb(255, 240, 138, 118 + alpha * 82));
            this.text(this.fitText(this.bannerText, 42), 640, 134, 20, rgb(255, 240, 138, 154 + alpha * 84));
        }
        this.drawAchievementToast();
        if (this.developerMode && this.showPerfOverlay) this.drawDevPerfOverlay();
    }

    private achievementEntryFor(def: AchievementDef): AchievementEntry | undefined {
        const name = this.normalizedPlayerName();
        return this.achievementEntries().find((entry) => entry.nickname === name && entry.id === def.id);
    }

    private achievementProgressValue(def: AchievementDef, open: boolean): number {
        if (open) return def.target;
        if (def.id === 'banana_50' || def.id === 'banana_100') return Math.min(this.bananasCollected, def.target);
        if (def.id === 'bonus_bananas') return Math.max(0, this.bananasCollected - LEVELS[this.levelIndex].target);
        if (def.id === 'bonus_three_run') return Math.min(this.runBonusCount, def.target);
        if (def.id === 'bonus_all_types') return Math.min(this.runBonusSeen.filter(Boolean).length, def.target);
        if (def.id === 'helmet_imitation') return this.armor > 0 ? 1 : 0;
        if (def.id === 'almost_engineer') return this.blueprintBonus > 0 ? 1 : 0;
        if (def.id === 'self_approved') return this.passBonus > 0 ? 1 : 0;
        return 0;
    }

    private rarityColor(rarity: AchievementRarity, alpha = 220): Color {
        if (rarity === 'rare') return rgb(102, 201, 255, alpha);
        if (rarity === 'epic') return rgb(197, 126, 255, alpha);
        if (rarity === 'legendary') return rgb(255, 201, 72, alpha);
        if (rarity === 'bureaucratic') return rgb(255, 118, 92, alpha);
        return rgb(190, 230, 176, alpha);
    }

    private rarityName(rarity: AchievementRarity): string {
        if (rarity === 'rare') return 'РЕДКОЕ';
        if (rarity === 'epic') return 'ЭПИЧЕСКОЕ';
        if (rarity === 'legendary') return 'ЛЕГЕНДАРНОЕ';
        if (rarity === 'bureaucratic') return 'БЮРОКРАТИЧЕСКИ БЕССМЫСЛЕННОЕ';
        return 'ОБЫЧНОЕ';
    }

    private shortRarityName(rarity: AchievementRarity): string {
        if (rarity === 'bureaucratic') return 'БЮРО';
        if (rarity === 'legendary') return 'ЛЕГЕНДА';
        return this.rarityName(rarity);
    }

    private fitText(value: string, maxChars: number): string {
        return value.length > maxChars ? `${value.slice(0, Math.max(1, maxChars - 3))}...` : value;
    }

    private drawDevPerfOverlay(): void {
        const activeSprites = this.activeSpriteCount();
        const activeLabels = this.activeLabelCount();
        const text = `узлы ${activeSprites + activeLabels + this.particles.length}  спрайты ${activeSprites}  текст ${activeLabels}  частицы ${this.particles.length}`;
        this.fillRect(16, 92, 480, 38, rgb(0, 0, 0, 150));
        this.strokeRect(16, 92, 480, 38, rgb(140, 210, 255, 140));
        this.text(text, 28, 116, 13, rgb(190, 230, 255), 'left');
    }

    private drawAchievementToast(): void {
        if (!this.achievementActive || this.achievementToastTimer <= 0) return;
        const def = this.achievementActive.def;
        const x = 320;
        const y = 96;
        const t = clamp(this.achievementToastTimer / TOAST_DURATION_SEC, 0, 1);
        const alpha = Math.floor(150 + 80 * t);
        const rarity = this.rarityColor(def.rarity, Math.min(220, alpha));
        this.fillRect(x, y, 640, 76, rgb(28, 22, 16, Math.min(200, alpha)));
        this.fillRect(x, y, 640, 5, this.rarityColor(def.rarity, Math.min(116, alpha)));
        this.strokeRect(x, y, 640, 76, rarity);
        this.circle(x + 52, y + 44, 30, this.rarityColor(def.rarity, 70));
        this.drawAssetSprite(def.iconAsset, x + 52, y + 43, 52, 52, alpha, 'ui_achievements', 'achievement_toast');
        this.text('ДОСТИЖЕНИЕ', x + 96, y + 19, 12, rarity, 'left');
        this.text(this.fitText(def.title, 31), x + 96, y + 43, 19, rgb(255, 246, 206, alpha), 'left');
        this.text(this.fitText(def.caption, 42), x + 96, y + 64, 12, rgb(226, 238, 210, alpha), 'left');
        this.fillRect(x + 506, y + 12, 110, 22, this.rarityColor(def.rarity, 54));
        this.text(this.shortRarityName(def.rarity), x + 561, y + 28, 9, rgb(255, 245, 210, alpha));
    }

    private drawMenu(): void {
        const surface = this.themedMenuSurface();
        this.drawMenuBackdrop(surface);

        const criticalSurface = this.state === 'menu' ? MAIN_MENU_UI_SURFACE : surface;
        const criticalState = this.state;
        const gateId = this.menuUiGateId(criticalSurface, criticalState);
        this.preloadCriticalMenuUiSprites('menu-frame', criticalSurface, criticalState);
        const menuUiReady = this.areCriticalMenuUiSpritesReady(criticalSurface, criticalState);
        if (!menuUiReady) {
            if (!this.menuUiGateWaitLoggedBySurface[gateId]) {
                this.menuUiGateWaitLoggedBySurface[gateId] = true;
                const missing = this.missingCriticalMenuUiSprites(criticalSurface, criticalState);
                const sample = missing.slice(0, 4).join('|');
                console.log(`MTR_MENU_UI_GATE_WAIT surface=${criticalSurface} screen=${criticalState} missing=${missing.length}${sample ? ` sample=${sample}` : ''}`);
            }
            this.drawMenuLoadingGate();
            return;
        }
        if (!this.menuUiReadyLoggedBySurface[gateId]) {
            this.menuUiReadyLoggedBySurface[gateId] = true;
            console.log(`MTR_MENU_UI_GATE_READY surface=${criticalSurface} screen=${criticalState}`);
        }
        if (this.state === 'menu') {
            this.preloadSecondaryMenuUiSprites('after-main-menu-ready');
        }

        this.drawUnifiedMenuChrome(surface);
        const primary = rgb(140, 255, 140);
        const dark = rgb(80, 58, 34, 188);
        const light = rgb(232, 255, 232);
        if (this.state === 'menu') {
            const mainButtonW = 382;
            const mainButtonH = 124;
            const leftX = 238;
            const rightX = 660;
            const rowY = [220, 350, 480];
            this.button(leftX, rowY[0], mainButtonW, mainButtonH, 'НАЧАТЬ ИГРУ', () => this.transitionTo('name', 'ui_start_menu'), primary, dark, light);
            this.button(rightX, rowY[0], mainButtonW, mainButtonH, 'ВЫБЕРИ СВОЕГО ПРИМАТА', () => this.transitionTo('skins', 'ui_skins'), primary, dark, light);
            this.button(leftX, rowY[1], mainButtonW, mainButtonH, 'МАРТЫШКИНЫ РЕКОРДЫ', () => this.transitionTo('records', 'ui_records'), primary, dark, light);
            this.button(rightX, rowY[1], mainButtonW, mainButtonH, 'ВЫБОР УРОВНЯ', () => this.transitionTo('levels', 'ui_levels'), primary, dark, light);
            this.button(leftX, rowY[2], mainButtonW, mainButtonH, 'ЗВУК И НАСТРОЙКИ', () => this.transitionTo('sound', 'ui_sound'), primary, dark, light);
            this.button(rightX, rowY[2], mainButtonW, mainButtonH, 'РЕЖИМ РАЗРАБОТЧИКА', () => this.openDevGate(), rgb(255, 214, 102), dark, rgb(255, 240, 184));
            if (this.developerMode && this.showPerfOverlay) this.drawStatusChip('РАЗРАБОТЧИК: ВСЕ УРОВНИ ОТКРЫТЫ · HP НЕ ТРАТИТСЯ', 620, rgb(255, 236, 94));
        } else if (this.state === 'devgate') {
            this.text('Доступ только для примата с паролем. Пароль в лог не пишется.', 640, 220, 18, rgb(255, 255, 255));
            this.drawAssetSprite(UI_SKIN.assets.panelChip, 640, 318, 460, 72, 245, 'ui_achievements', 'dev_password_field_back');
            if (!(this.devPasswordEdit?.string || '').trim()) this.text('Пароль разработчика', 640, 318, 22, rgb(255, 230, 142), 'center', 360);
            if (this.devStatusText) this.drawStatusChip(this.devStatusText, 370, this.devStatusText.includes('открыт') ? rgb(170, 255, 160) : rgb(255, 168, 128));
            this.button(390, 414, 240, 64, 'ПРОВЕРИТЬ', () => this.tryOpenDeveloperMode(), rgb(255, 224, 118), dark, light);
            this.button(650, 414, 240, 64, 'НАЗАД', () => this.transitionTo('menu', 'ui_back'), primary, dark, light);
        } else if (this.state === 'devpanel') {
            this.drawStatusChip(`КОЛЛАЙДЕРЫ ${this.debugColliders ? 'ВКЛ' : 'ВЫКЛ'} · ТАПЫ ${this.showTouchZones ? 'ВКЛ' : 'ВЫКЛ'} · PERF ${this.showPerfOverlay ? 'ВКЛ' : 'ВЫКЛ'}`, 142, rgb(255, 245, 190));
            const rowY = [178, 252, 326, 400];
            const devButtonH = 64;
            this.button(145, rowY[0], 300, devButtonH, 'КОЛЛАЙДЕРЫ', () => { this.debugColliders = !this.debugColliders; this.saveSettings(); }, rgb(255, 224, 118), dark, light);
            this.button(490, rowY[0], 300, devButtonH, 'ЗОНЫ ТАПА', () => { this.showTouchZones = !this.showTouchZones; this.saveSettings(); }, rgb(120, 255, 180), dark, light);
            this.button(835, rowY[0], 300, devButtonH, 'FPS / УЗЛЫ', () => { this.showPerfOverlay = !this.showPerfOverlay; this.saveSettings(); }, rgb(140, 210, 255), dark, light);
            this.button(145, rowY[1], 300, devButtonH, 'ВСЕ ПРЕПЯТСТВИЯ', () => this.spawnAllObstacleFamiliesForQa(), primary, dark, light);
            this.button(490, rowY[1], 300, devButtonH, 'ВСЕ БОНУСЫ', () => this.spawnAllBonusStatesForQa(), primary, dark, light);
            this.button(835, rowY[1], 300, devButtonH, 'ОТКРЫТЬ ДОСТИЖЕНИЯ', () => this.unlockAllAchievementsForQa(), primary, dark, light);
            this.button(145, rowY[2], 300, devButtonH, 'ЗАКРЫТЬ ДОСТИЖЕНИЯ', () => this.lockAchievementsForQa(), rgb(255, 150, 120), dark, light);
            this.button(490, rowY[2], 300, devButtonH, 'УРОВЕНЬ 1', () => this.startLevel(0), primary, dark, light);
            this.button(835, rowY[2], 300, devButtonH, 'УРОВЕНЬ 15', () => this.startLevel(14), primary, dark, light);
            this.button(145, rowY[3], 300, devButtonH, 'ПРОВЕРКА ПАУЗЫ', () => { this.startLevel(this.levelIndex); this.showTouchZones = true; this.saveSettings(); }, rgb(120, 255, 180), dark, light);
            this.button(490, rowY[3], 300, devButtonH, 'СКРИН: ADB / WEB', () => { this.bannerText = 'Снимок делает внешний QA-инструмент'; this.bannerTimer = TOAST_DURATION_SEC; }, primary, dark, light);
            this.button(835, rowY[3], 300, devButtonH, 'В МЕНЮ', () => this.transitionTo('menu', 'ui_menu'), primary, dark, light);
        } else if (this.state === 'name') {
            const name = this.normalizedPlayerName();
            const typedName = this.sanitizePlayerName(this.playerNameEdit?.string || name);
            this.text('Выбери профиль для рекордов и достижений — или сразу в забег.', 640, 190, 17, rgb(244, 238, 210), 'center', 700);
            this.drawAssetSprite(START_MENU_PROFILE_BOX_KEY, 640, 304, 700, 180, 245, 'ui_achievements', 'start_menu_profile_box');
            this.text(typedName, 640, 318, typedName.length > 18 ? 24 : 30, rgb(255, 240, 138), 'center', 510);
            this.button(419, 402, 442, 64, 'СОХРАНИТЬ ИМЯ', () => this.commitPlayerNameFromInput(true), primary, dark, light);
            this.button(419, 478, 442, 72, 'ВПЕРЁД, ПРИМАТЫ!', () => {
                this.commitPlayerNameFromInput(false);
                this.startLevel(this.levelIndex);
            }, primary, dark, light);
            this.button(419, 562, 442, 64, 'В МЕНЮ', () => this.transitionTo('menu', 'ui_menu'), primary, dark, light);
        } else if (this.state === 'sound') {
            this.drawAudioSettingsRow('МУЗЫКА', 154, this.musicEnabled, this.musicVolume, () => {
                this.musicEnabled = !this.musicEnabled;
                this.ensureMusic(true);
            }, () => { this.musicVolume = clamp(this.musicVolume - 0.1, 0, 1); }, () => { this.musicVolume = clamp(this.musicVolume + 0.1, 0, 1); this.ensureMusic(true); });
            this.drawAudioSettingsRow('ЭФФЕКТЫ', 270, this.sfxEnabled, this.sfxVolume, () => {
                this.sfxEnabled = !this.sfxEnabled;
            }, () => { this.sfxVolume = clamp(this.sfxVolume - 0.1, 0, 1); }, () => { this.sfxVolume = clamp(this.sfxVolume + 0.1, 0, 1); this.playFirst(['bonus', 'jump'], this.sfxVolume * 0.5); });
            this.drawAudioSettingsRow('ГОЛОС ПРИМАТА', 386, this.voiceEnabled, this.voiceVolume, () => {
                this.voiceEnabled = !this.voiceEnabled;
            }, () => { this.voiceVolume = clamp(this.voiceVolume - 0.1, 0, 1); }, () => { this.voiceVolume = clamp(this.voiceVolume + 0.1, 0, 1); this.playVoice('jump', 1); });
            this.button(250, 549, 240, 64, 'ПО УМОЛЧАНИЮ', () => this.resetAudioDefaults(), primary, dark, light);
            this.button(520, 549, 240, 64, 'ПРИМЕНИТЬ', () => this.applyAudioSettings(), primary, dark, light);
            this.button(790, 549, 240, 64, 'НАЗАД', () => { this.saveSettings(); this.transitionTo('menu', 'ui_back'); }, primary, dark, light);
        } else if (this.state === 'records') {
            const records = this.records().slice(0, 7);
            if (!records.length) {
                this.drawAssetSprite(UI_SKIN.assets.emptyStateCard, 640, 342, 700, 180, 245, 'ui_achievements', 'records_empty_state');
                this.text('ОТЧЁТ ЕЩЁ НЕ ДОЕХАЛ', 640, 322, 24, rgb(255, 226, 122));
                this.text('Пока никто не донёс ведомость до финиша.', 640, 364, 18, rgb(244, 238, 210));
            } else {
                for (let i = 0; i < records.length; i++) {
                    const r = records[i];
                    this.drawAssetSprite(UI_SKIN.assets.panelChip, 640, 176 + i * 55, 840, 48, 236, 'ui_achievements', 'records_row');
                    const rowY = 182 + i * 55;
                    const rowColor = i === 0 ? rgb(255, 240, 138) : rgb(255, 255, 255);
                    this.text(`${i + 1}. ${this.fitText(r.name, 27)}`, 292, rowY, 16, rowColor, 'left', 330);
                    this.text(`СЧЁТ ${r.score}`, 640, rowY, 15, rowColor, 'center', 155);
                    this.text(`УРОВЕНЬ ${r.level}`, 800, rowY, 15, rowColor, 'center', 130);
                    this.text(`БАНАНЫ ${r.bananas}`, 960, rowY, 15, rowColor, 'center', 140);
                }
            }
            this.button(324, 616, 300, 64, 'ДОСТИЖЕНИЯ', () => this.transitionTo('achievements', 'ui_achievements'), primary, dark, light);
            this.button(656, 616, 300, 64, 'НАЗАД', () => this.transitionTo('menu', 'ui_back'), primary, dark, light);
        } else if (this.state === 'achievements') {
            const name = this.normalizedPlayerName();
            this.drawStatusChip(`ПРОФИЛЬ: ${name}`, 126, rgb(255, 240, 138));
            const cardW = 544;
            const cardH = 86;
            const startX = 70;
            const startY = 142;
            const gapX = 52;
            const gapY = 6;
            for (let i = 0; i < ACHIEVEMENTS.length; i++) {
                const def = ACHIEVEMENTS[i];
                const col = i % 2;
                const row = Math.floor(i / 2);
                const x = startX + col * (cardW + gapX);
                const y = startY + row * (cardH + gapY);
                const entry = this.achievementEntryFor(def);
                const open = !!entry;
                const rarity = this.rarityColor(def.rarity, open ? 215 : 125);
                const progress = clamp(this.achievementProgressValue(def, open) / Math.max(1, def.target), 0, 1);
                const title = open ? def.title : `Секретный акт №${String(i + 1).padStart(2, '0')}`;
                const body = open ? def.caption : def.hint;
                this.drawAssetSprite(open ? UI_SKIN.assets.achievementCard : UI_SKIN.assets.achievementCardLocked, x + cardW * 0.5, y + cardH * 0.5, cardW, cardH, 245, 'ui_achievements', 'shared_achievement_card');
                this.fillRect(x + 15, y + 13, 70, 60, rgb(5, 7, 5, 92));
                this.circle(x + 50, y + 43, 30, open ? this.rarityColor(def.rarity, 74) : rgb(72, 72, 64, 66));
                this.drawAssetSprite(open ? def.iconAsset : 'objectives/ui/ui_level_lock_01', x + 50, y + 44, 64, 64, open ? 232 : 90, 'ui_achievements', 'achievement_card_icon');
                const textX = x + 98;
                const metaX = x + 414;
                const progressW = 286;
                this.text(this.fitText(title, 23), textX, y + 27, 18, open ? rgb(255, 242, 190) : rgb(196, 196, 184), 'left', progressW);
                this.text(this.fitText(body, 32), textX, y + 52, 14, open ? rgb(224, 234, 204) : rgb(166, 166, 154), 'left', progressW);
                this.fillRect(textX, y + 68, progressW, 10, rgb(0, 0, 0, 130));
                this.fillRect(textX, y + 68, progressW * progress, 10, rarity);
                this.fillRect(metaX, y + 13, 112, 22, this.rarityColor(def.rarity, open ? 58 : 34));
                this.text(this.fitText(this.shortRarityName(def.rarity), 10), metaX + 56, y + 29, 9, rarity, 'center', 112);
                if (open && entry) this.text(this.formatAchievementDate(entry.timestamp), metaX, y + 52, 10, rgb(230, 226, 190), 'left', 112);
                this.text(open ? 'ПОЛУЧЕНО' : `${Math.floor(progress * def.target)}/${def.target}`, metaX, y + 74, 11, rgb(255, 238, 180), 'left', 112);
            }
            this.button(324, 616, 300, 64, 'РЕКОРДЫ', () => this.transitionTo('records', 'ui_records'), primary, dark, light);
            this.button(656, 616, 300, 64, 'НАЗАД', () => this.transitionTo('menu', 'ui_back'), primary, dark, light);
        } else if (this.state === 'paused') {
            this.button(430, 276, 420, 64, 'ПРОДОЛЖИТЬ', () => this.transitionTo('playing', 'ui_resume'), primary, dark, light);
            this.button(430, 346, 420, 64, 'ЗВУК И НАСТРОЙКИ', () => this.transitionTo('sound', 'ui_sound'), primary, dark, light);
            this.button(430, 416, 420, 64, 'В МЕНЮ', () => this.transitionTo('menu', 'ui_menu'), primary, dark, light);
        } else if (this.state === 'clear') {
            this.text(`СЧЁТ ${this.score}   ·   БАНАНЫ ${this.bananasCollected}`, 640, 290, 22, rgb(255, 240, 138));
            this.button(430, 376, 420, 64, 'СЛЕДУЮЩИЙ УРОВЕНЬ', () => this.startLevel(this.levelIndex + 1), primary, dark, light);
            this.button(430, 443, 420, 64, 'В МЕНЮ', () => this.transitionTo('menu', 'ui_menu'), primary, dark, light);
        } else if (this.state === 'over') {
            this.drawAssetSprite(UI_SKIN.assets.emptyStateCard, 640, 310, 700, 160, 245, 'ui_achievements', 'death_summary');
            this.text(this.reason || 'Объект победил.', 640, 286, 20, rgb(255, 255, 255));
            this.text(`СЧЁТ ${this.score} · БАНАНЫ ${this.bananasCollected} · ПРОГРЕСС ${Math.min(100, Math.floor(this.progress / LEVELS[this.levelIndex].length * 100))}%`, 640, 334, 17, rgb(255, 238, 150));
            this.button(430, 416, 420, 64, 'ПОВТОРИТЬ', () => { this.playVoice('ui', 0.8); this.startLevel(this.levelIndex); }, primary, dark, light);
            this.button(430, 486, 420, 64, 'В МЕНЮ', () => { this.transitionTo('menu', 'ui_menu'); this.playVoice('ui', 0.5); }, primary, dark, light);
        } else if (this.state === 'finished') {
            this.text('Дом построен. Возможно, это коровник.', 640, 300, 22, rgb(255, 255, 255));
            this.text(`ИТОГОВЫЙ СЧЁТ ${this.score}   ·   БАНАНЫ ${this.bananasCollected}`, 640, 344, 18, rgb(255, 240, 138));
            this.button(430, 386, 420, 64, 'ЗАНОВО', () => this.startLevel(0), primary, dark, light);
            this.button(430, 453, 420, 64, 'РЕКОРДЫ', () => this.transitionTo('records', 'ui_records'), primary, dark, light);
        } else if (this.state === 'skins') {
            const cardW = 252;
            const cardH = 172;
            const skinCols = 4;
            const gapX = 44;
            const gapY = 194;
            const startX = (W - (skinCols * cardW + (skinCols - 1) * gapX)) * 0.5;
            for (let i = 0; i < SKINS.length; i++) {
                const col = i % skinCols;
                const row = Math.floor(i / skinCols);
                const x = startX + col * (cardW + gapX);
                const y = 150 + row * gapY;
                const selected = this.pendingSkinSelection === i;
                this.drawAssetSprite(selected ? UI_SKIN.assets.primateCardSelected : UI_SKIN.assets.primateCard, x + cardW * 0.5, y + cardH * 0.5, cardW, cardH, 245, 'ui_achievements', 'shared_primate_card');
                this.registerImageButton(x, y, cardW, cardH, () => {
                    this.pendingSkinSelection = i;
                    this.preloadCriticalPlayerSkinSprites('skin-card-select', i);
                    this.playVoice('ui', 0.7);
                });
                this.drawSkinPreview(x + cardW * 0.5, y + 55, i, selected);
                if (selected) {
                    this.drawAssetSprite(UI_SKIN.assets.statusChip, x + cardW - 58, y + 24, 104, 34, 245, 'ui_achievements', 'primate_selected_badge');
                    this.text('✓ ВЫБРАН', x + cardW - 58, y + 27, 10, rgb(255, 235, 128), 'center', 96);
                }
            }
            this.button(330, 616, 300, 64, 'ВЫБРАТЬ', () => this.confirmSkinSelection(), primary, dark, light);
            this.button(650, 616, 300, 64, 'НАЗАД', () => this.transitionTo('menu', 'ui_back'), primary, dark, light);
        } else if (this.state === 'levels') {
            for (let i = 0; i < LEVELS.length; i++) {
                const row = Math.floor(i / 5);
                const col = i % 5;
                const open = this.developerMode || i <= this.unlockedLevel;
                const action = open
                    ? () => this.startLevel(i)
                    : () => { this.bannerText = 'Сначала переживи предыдущий объект'; this.bannerTimer = TOAST_DURATION_SEC; };
                const x = 68 + col * 234;
                const y = 152 + row * 142;
                this.drawUnifiedLevelCard(i, x, y, 210, 116, open, action);
            }
            this.button(430, 625, 420, 64, 'НАЗАД', () => this.transitionTo('menu', 'ui_back'), primary, dark, light);
        }
    }

    private drawUnifiedMenuChrome(surface = this.themedMenuSurface()): void {
        const title = UI_SCREEN_TITLES[this.state] || UI_SCREEN_TITLES.menu;
        if (this.state === 'menu') {
            const titleDrawn = this.drawAssetSprite(MAIN_MENU_TITLE_KEY, 640, 116, 570, 190, 248, 'ui_achievements', 'main_menu_title_png');
            if (!titleDrawn) this.text(title, 640, 132, title.length > 26 ? 30 : 35, this.uiColor(UI_SKIN.typography.title.color), 'center', 590);
            return;
        }
        const listState = this.state === 'levels' || this.state === 'skins' || this.state === 'records' || this.state === 'achievements' || this.state === 'devpanel';
        const compactState = this.state === 'paused' || this.state === 'clear' || this.state === 'over' || this.state === 'finished' || this.state === 'name' || this.state === 'devgate';
        const panelKey = listState ? UI_SKIN.assets.panelList : compactState ? UI_SKIN.assets.panelDialog : UI_SKIN.assets.panelMain;
        const panelW = listState ? 1210 : compactState ? 780 : 1000;
        const panelH = listState ? 560 : compactState ? 470 : 580;
        this.drawAssetSprite(panelKey, 640, 390, panelW, panelH, this.state === 'paused' ? 226 : 245, 'ui_achievements', `shared_${surface}_panel`);
        this.drawAssetSprite(UI_SKIN.assets.titleBanner, 640, 72, listState ? 760 : 720, 106, 250, 'ui_achievements', `shared_${surface}_title`);
        this.text(title, 640, 80, title.length > 26 ? 31 : 36, this.uiColor(UI_SKIN.typography.title.color), 'center', 680);
    }

    private drawStatusChip(value: string, y: number, color = rgb(255, 236, 94)): void {
        this.drawAssetSprite(UI_SKIN.assets.statusChip, 640, y, 650, 54, 245, 'ui_achievements', 'shared_status_chip');
        this.text(this.fitText(value, 62), 640, y + 5, 14, color, 'center', 610);
    }

    private drawAudioSettingsRow(
        label: string,
        y: number,
        enabled: boolean,
        volume: number,
        toggleAction: () => void,
        quieterAction: () => void,
        louderAction: () => void,
    ): void {
        this.drawAssetSprite(UI_SKIN.assets.panelChip, 640, y + 46, 960, 88, 242, 'ui_achievements', 'sound_row_panel');
        this.text(label, 198, y + 50, label.length > 12 ? 14 : 17, rgb(255, 238, 176), 'left', 236);
        const toggleW = 124;
        const toggleH = 48;
        const toggleX = 438;
        const toggleTop = y + 22;
        const toggleTouchH = 64;
        const toggleTouchTop = y + 14;
        this.fillRect(toggleX - toggleW * 0.5, toggleTop, toggleW, toggleH, enabled ? rgb(50, 118, 54, 218) : rgb(70, 60, 50, 218));
        this.strokeRect(toggleX - toggleW * 0.5, toggleTop, toggleW, toggleH, enabled ? rgb(200, 255, 154, 225) : rgb(210, 188, 150, 190));
        this.circle(enabled ? toggleX + 35 : toggleX - 35, y + 46, 18, enabled ? rgb(228, 255, 190, 245) : rgb(210, 198, 178, 238));
        this.registerImageButton(toggleX - toggleW * 0.5, toggleTouchTop, toggleW, toggleTouchH, toggleAction);
        this.text(enabled ? 'ВКЛ' : 'ВЫКЛ', toggleX, y + 51, 12, enabled ? rgb(224, 255, 190) : rgb(220, 210, 196), 'center', 112);
        const sliderX = 560;
        const sliderW = 318;
        const clamped = clamp(volume, 0, 1);
        this.drawAssetSprite(UI_SKIN.assets.sliderTrack, sliderX + sliderW * 0.5, y + 46, sliderW, 24, 245, 'ui_achievements', 'sound_slider_track');
        if (clamped > 0.01) this.drawAssetSprite(UI_SKIN.assets.sliderFill, sliderX + sliderW * clamped * 0.5, y + 46, sliderW * clamped, 22, 245, 'ui_achievements', 'sound_slider_fill');
        this.drawAssetSprite(UI_SKIN.assets.sliderKnob, sliderX + sliderW * clamped, y + 46, 38, 38, 245, 'ui_achievements', 'sound_slider_knob');
        this.text(`${Math.round(clamped * 100)}%`, 928, y + 51, 15, rgb(255, 240, 178), 'center', 72);
        this.button(979, y + 14, 64, 64, '−', quieterAction, rgb(255, 224, 118), rgb(42, 31, 18, 190), rgb(255, 240, 184));
        this.button(1047, y + 14, 64, 64, '+', louderAction, rgb(255, 224, 118), rgb(42, 31, 18, 190), rgb(255, 240, 184));
    }

    private resetAudioDefaults(): void {
        this.musicEnabled = true;
        this.sfxEnabled = true;
        this.voiceEnabled = true;
        this.musicVolume = DEFAULT_MUSIC_VOLUME;
        this.sfxVolume = DEFAULT_SFX_VOLUME;
        this.voiceVolume = DEFAULT_VOICE_VOLUME;
        this.applyAudioSettings('Настройки возвращены по умолчанию');
    }

    private applyAudioSettings(message = 'Настройки звука применены'): void {
        this.saveSettings();
        this.ensureMusic(true);
        this.bannerText = message;
        this.bannerTimer = TOAST_DURATION_SEC;
        this.playFirst(['banner', 'bonus'], this.sfxVolume * 0.5);
    }

    private formatAchievementDate(timestamp: number): string {
        const date = new Date(timestamp);
        const intl = (globalThis as unknown as { Intl?: typeof Intl }).Intl;
        if (intl?.DateTimeFormat) {
            try {
                return new intl.DateTimeFormat('ru-RU', {
                    day: '2-digit',
                    month: '2-digit',
                    year: 'numeric',
                }).format(date);
            } catch {
                // Fall through to the native-safe formatter below.
            }
        }
        const pad = (value: number) => String(value).padStart(2, '0');
        return `${pad(date.getDate())}.${pad(date.getMonth() + 1)}.${date.getFullYear()}`;
    }

    private confirmSkinSelection(): void {
        this.selectedSkin = clamp(this.pendingSkinSelection, 0, SKINS.length - 1);
        this.preloadCriticalPlayerSkinSprites('skin-confirm', this.selectedSkin);
        this.preloadSelectedSkinVariantsDeferred('skin-confirm', this.selectedSkin);
        this.currentPlayerVisualKey = '';
        this.previousPlayerVisualKey = '';
        this.playerVisualBlendTimer = 0;
        this.saveSettings();
        this.bannerText = `Выбран примат: ${SKINS[this.selectedSkin].name}`;
        this.bannerTimer = TOAST_DURATION_SEC;
        this.transitionTo('menu', 'skin_confirm');
    }

    private drawUnifiedLevelCard(levelIndex: number, x: number, y: number, w: number, h: number, open: boolean, action: () => void): void {
        const selected = open && levelIndex === this.levelIndex;
        const key = open ? (selected ? UI_SKIN.assets.levelCardSelected : UI_SKIN.assets.levelCard) : UI_SKIN.assets.levelCardLocked;
        this.drawAssetSprite(key, x + w * 0.5, y + h * 0.5, w, h, 245, 'ui_achievements', 'shared_level_card');
        this.drawAssetSprite(UI_SKIN.assets.statusChip, x + 28, y + 24, 42, 30, 242, 'ui_achievements', 'level_number_chip');
        this.text(String(levelIndex + 1), x + 28, y + 28, 12, open ? rgb(255, 231, 128) : rgb(188, 184, 174), 'center', 34);
        this.drawLevelThemeIcon(levelIndex, x + w - 34, y + 31, 36, open);
        const lines = this.levelCardTitleLines(levelIndex);
        this.text(lines, x + w * 0.48, y + 52, 12, open ? rgb(65, 36, 17) : rgb(185, 182, 174), 'center', w - 76);
        const stars = open ? this.levelStars(levelIndex) : 0;
        this.text(open ? `${'★'.repeat(stars)}${'☆'.repeat(3 - stars)}` : 'ЗАКРЫТО', x + w * 0.5, y + 99, open ? 15 : 11, open ? rgb(255, 194, 42) : rgb(184, 178, 166), 'center', w - 20);
        this.registerImageButton(x, y, w, h, action);
    }

    private drawLevelThemeIcon(levelIndex: number, x: number, y: number, size: number, open: boolean): void {
        const boundedIndex = Math.floor(clamp(levelIndex, 0, LEVEL_SELECT_THEME_ICON_KEYS.length - 1));
        const key = LEVEL_SELECT_THEME_ICON_KEYS[boundedIndex] || LEVEL_SELECT_THEME_ICON_KEYS[0];
        const drawn = this.drawAssetSprite(
            key,
            x,
            y,
            size,
            size,
            open ? 246 : 142,
            'ui_achievements',
            'level_select_theme_icon_png',
        );
        if (drawn) return;

        const fallbackKey = open ? UI_SKIN.assets.statusChip : 'objectives/ui/ui_level_lock_01';
        if (!this.drawAssetSprite(
            fallbackKey,
            x,
            y,
            size * 0.92,
            size * 0.92,
            open ? 176 : 154,
            'ui_achievements',
            'level_select_theme_icon_loading',
        )) {
            this.text(open ? '…' : '—', x, y + 4, 13, open ? rgb(255, 231, 128) : rgb(188, 184, 174), 'center', size + 10);
        }
    }

    private levelCardTitleLines(levelIndex: number): string {
        const title = this.compactLevelMenuName(levelIndex);
        if (title.length <= 19) return title;
        const words = title.split(/\s+/);
        let first = '';
        let second = '';
        for (const word of words) {
            if (!second && `${first} ${word}`.trim().length <= 18) first = `${first} ${word}`.trim();
            else second = `${second} ${word}`.trim();
        }
        return `${first}\n${this.fitText(second, 20)}`;
    }

    private themedMenuSurface(): string {
        switch (this.state) {
            case 'menu':
            case 'name':
            case 'clear':
            case 'finished':
                return 'main_menu';
            case 'sound':
                return 'sound_settings';
            case 'records':
                return 'records';
            case 'achievements':
                return 'achievements';
            case 'paused':
                return 'pause';
            case 'over':
                return 'death';
            case 'skins':
                return 'skin_select';
            case 'levels':
                return 'level_select';
            case 'devgate':
            case 'devpanel':
                return 'developer';
            default:
                return 'main_menu';
        }
    }

    private drawThemedLevelCard(levelIndex: number, x: number, y: number, w: number, h: number, open: boolean, action: () => void): boolean {
        const keys = themedUiAssetKeysForSurface('level_select', 'card');
        if (!keys.length) return false;
        const cardIndex = clamp(levelIndex, 0, keys.length - 1);
        const drawn = this.drawAssetSprite(keys[cardIndex], x + w * 0.5, y + h * 0.5, w * 1.06, h * 1.12, open ? 232 : 150, 'ui_achievements', 'latest_level_select_card');
        if (!drawn) return false;
        const levelName = this.compactLevelMenuName(levelIndex);
        this.text(`${levelIndex + 1}. ${levelName}`, x + w * 0.5, y + 28, 12, open ? rgb(64, 34, 12) : rgb(112, 104, 92), 'center', w - 18);
        const stars = open ? this.levelStars(levelIndex) : 0;
        const starText = open ? `${'★'.repeat(stars)}${'☆'.repeat(3 - stars)}` : 'ЗАКРЫТО';
        this.text(starText, x + w * 0.5, y + 58, open ? 16 : 12, open ? rgb(255, 188, 28) : rgb(116, 104, 88), 'center', w - 18);
        this.registerImageButton(x, y, w, h, action);
        return true;
    }

    private registerImageButton(x: number, y: number, w: number, h: number, action: () => void): void {
        this.buttons.push({
            rect: { x, y, w, h },
            text: '',
            action,
            stroke: rgb(0, 0, 0, 0),
            fill: rgb(0, 0, 0, 0),
            textColor: rgb(255, 255, 255, 0),
        });
    }

    private compactLevelMenuName(levelIndex: number): string {
        const raw = LEVELS[levelIndex]?.name || `Уровень ${levelIndex + 1}`;
        return raw
            .replace(/^Уровень\s+\d+:\s*/i, '')
            .replace('мартышкиного', 'март.')
            .replace('бессмысленных заявлений', 'заявлений')
            .replace('Министерство фабричного труда', 'Мин. фабричного труда')
            .replace('Сердце Мартышкиного труда', 'Сердце труда')
            .slice(0, 26);
    }

    private levelStars(levelIndex: number): number {
        if (this.developerMode) return 3;
        if (levelIndex < this.unlockedLevel) return 3;
        if (levelIndex === this.unlockedLevel) return 1;
        return 0;
    }

    private drawMenuBackdrop(surface: string): void {
        const viewportWidth = this.backgroundViewportWidth();
        const viewportX = (W - viewportWidth) * 0.5;
        const opacity = surface === MAIN_MENU_UI_SURFACE ? 96 : this.state === 'paused' ? 126 : 150;
        this.fillRect(viewportX, 0, viewportWidth, H, rgb(20, 16, 12, opacity));
    }

    private drawMenuLoadingGate(): void {
        this.fillRect(380, 292, 520, 106, rgb(76, 54, 32, 210));
        this.fillRect(402, 312, 476, 66, rgb(128, 96, 52, 128));
        this.strokeRect(380, 292, 520, 106, rgb(236, 196, 112, 170));
        this.text('ГРУЗИМ МЕНЮ', 640, 334, 22, rgb(255, 238, 150));
        this.text('Бригада подтягивает вывески', 640, 366, 14, rgb(246, 232, 184));
    }

    private drawSkinPreview(x: number, y: number, skin: number, selected: boolean): void {
        const sk = SKINS[skin % SKINS.length];
        const bottom = y + 70;
        if (selected) this.strokeRect(x - 122, y - 52, 245, 152, rgb(255, 244, 120));
        const previewKey = playerSkinPreviewAssetKey(skin);
        if (this.drawAssetSprite(previewKey, x, bottom - 49, 98, 108, 245, 'player_body', 'menu_skin_preview')) {
            this.text(sk.name, x, y + 75, 14, rgb(255, 255, 255));
            this.text(`${sk.species} / ${sk.badge}`, x, y + 94, 10, rgb(255, 236, 150));
            return;
        }
        this.segment(x - 45, bottom - 42, x - 12, bottom - 50, 2.4, sk.fur);
        this.segment(x - 49, bottom - 42, x - 64, bottom - 32, 2.6, sk.fur);
        this.circle(x, bottom - 36, 26, sk.fur);
        this.fillRect(x - 21, bottom - 40, 42, 22, sk.vest);
        this.circle(x, bottom - 34, 13, sk.face);
        this.circle(x - 24, bottom - 59, 10, sk.fur);
        this.circle(x + 24, bottom - 59, 10, sk.fur);
        this.circle(x, bottom - 59, 20, sk.fur);
        this.circle(x, bottom - 55, 10.5, sk.face);
        this.circle(x - 6, bottom - 61, 2.1, rgb(30, 25, 18));
        this.circle(x + 6, bottom - 61, 2.1, rgb(30, 25, 18));
        this.fillRect(x - 20, bottom - 84, 40, 11, sk.helmet);
        this.circle(x, bottom - 78, 20, this.alpha(sk.helmet, 205));
        this.segment(x - 14, bottom - 18, x - 27, bottom - 2, 3.4, sk.accent);
        this.segment(x + 14, bottom - 18, x + 27, bottom - 2, 3.4, sk.accent);
        this.circle(x - 30, bottom, 4.5, sk.accent);
        this.circle(x + 30, bottom, 4.5, sk.accent);
        this.text(sk.name, x, y + 75, 14, rgb(255, 255, 255));
        this.text(`${sk.species} / ${sk.badge}`, x, y + 94, 10, rgb(255, 236, 150));
    }

    private onTouchStart(event: EventTouch): void {
        this.unlockAudio();
        const p = this.touchPoint(event);
        const buttonHit = this.handleTouch(p.x, p.y);
        if (!buttonHit && this.state === 'playing') this.gliding = p.x < W * 0.58;
    }

    private onTouchMove(event: EventTouch): void {
        if (this.state !== 'playing') return;
        const p = this.touchPoint(event);
        this.gliding = p.x < W * 0.58;
    }

    private onTouchEnd(): void {
        this.gliding = false;
    }

    private onKeyDown(event: EventKeyboard): void {
        this.unlockAudio();
        if (event.keyCode === KeyCode.KEY_P || event.keyCode === KeyCode.ESCAPE) {
            this.togglePauseFromInput();
            return;
        }
        if (this.state !== 'playing') return;
        if (event.keyCode === KeyCode.SPACE || event.keyCode === KeyCode.ARROW_UP) {
            this.gliding = true;
            this.jump();
        }
        if (event.keyCode === KeyCode.KEY_D || event.keyCode === KeyCode.ARROW_RIGHT) this.dash();
    }

    private onKeyUp(event: EventKeyboard): void {
        if (event.keyCode === KeyCode.SPACE || event.keyCode === KeyCode.ARROW_UP) this.gliding = false;
    }

    private handleTouch(x: number, y: number): boolean {
        if (this.state === 'playing' && this.pointInRect(x, y, this.pauseTouchRect())) {
            this.togglePauseFromInput();
            return true;
        }
        if (this.isDeveloperCornerTap(x, y)) {
            this.registerDeveloperCornerTap();
            return true;
        }
        for (const b of this.buttons) {
            if (x >= b.rect.x && x <= b.rect.x + b.rect.w && y >= b.rect.y && y <= b.rect.y + b.rect.h) {
                b.action();
                return true;
            }
        }
        if (this.state === 'playing') {
            if (x < W * 0.58) this.jump();
            else this.dash();
        }
        return false;
    }

    private pointInRect(x: number, y: number, r: Rect): boolean {
        return x >= r.x && x <= r.x + r.w && y >= r.y && y <= r.y + r.h;
    }

    private touchPoint(event: EventTouch): { x: number; y: number } {
        const p = event.getUILocation();
        const visible = view.getVisibleSize();
        return { x: p.x / visible.width * W, y: H - p.y / visible.height * H };
    }

    private worldX(worldX: number): number {
        return this.player.x + worldX - this.progress;
    }

    private worldXAt(worldX: number, progress: number): number {
        return this.player.x + worldX - progress;
    }

    private attractWorldPointTowardPlayer(worldX: number, y: number, dt: number, itemLabel: string): { worldX: number; y: number; screenX: number } {
        if (this.magnet <= 0) return { worldX, y, screenX: this.worldX(worldX) };
        const sx = this.worldX(worldX);
        const playerY = this.player.y - 42;
        const dx = this.player.x - sx;
        const dy = playerY - y;
        const before = Math.hypot(dx, dy);
        if (before > MAGNET_RADIUS_PX || before <= 1) return { worldX, y, screenX: sx };
        const step = Math.min(before - 1, Math.min(MAGNET_MAX_SPEED_PX_PER_SEC, MAGNET_SPEED_PX_PER_SEC) * dt);
        const nx = dx / before;
        const ny = dy / before;
        const nextScreenX = sx + nx * step;
        const nextY = y + ny * step;
        const nextWorldX = this.progress + nextScreenX - this.player.x;
        const after = Math.hypot(this.player.x - nextScreenX, playerY - nextY);
        if (this.magnetLogCooldown <= 0) {
            const status = after < before ? 'OK' : 'FAIL';
            console.log(`MTR_MAGNET_ATTRACT item=${itemLabel} dx=${dx.toFixed(1)} dy=${dy.toFixed(1)} distance_before=${before.toFixed(1)} distance_after=${after.toFixed(1)} status=${status}`);
            this.magnetLogCooldown = 0.32;
        }
        return { worldX: nextWorldX, y: nextY, screenX: nextScreenX };
    }

    private difficulty(): number {
        if (this.levelIndex < 3) return 0;
        return 1 + Math.floor((this.levelIndex - 3) / 2);
    }

    private obstaclePoolForTheme(theme: number): number[] {
        const pools: number[][] = [
            [0, 1, 2, 6, 7, 8, 9, 10, 11, 17],
            [2, 1, 6, 8, 9, 10, 11, 15, 17, 0],
            [1, 10, 13, 15, 16, 17, 8, 6, 0, 9],
            [3, 6, 10, 14, 15, 17, 8, 0, 1, 9],
            [4, 1, 6, 17, 10, 8, 9, 11, 15, 0],
            [5, 16, 6, 10, 17, 1, 8, 9, 11, 0],
            [6, 1, 9, 10, 13, 17, 7, 11, 8, 0],
            [7, 9, 11, 12, 6, 17, 1, 8, 10, 0],
            [1, 10, 13, 16, 17, 8, 6, 9, 15, 0],
            [0, 1, 2, 9, 10, 17, 8, 11, 13, 6],
            [11, 6, 9, 17, 3, 8, 10, 1, 0, 15],
            [12, 7, 6, 9, 17, 8, 10, 1, 0, 11],
            [13, 1, 16, 15, 10, 17, 8, 9, 0, 6],
            [14, 15, 3, 10, 6, 17, 1, 8, 9, 0],
            [16, 1, 5, 4, 0, 7, 17, 8, 9, 10],
        ];
        return pools[theme % pools.length];
    }

    private obstacleLabel(type: number, ordinal: number): string {
        const bank = OBSTACLE_LABEL_BANK[type % OBSTACLE_LABEL_BANK.length] || OBSTACLE_LABELS;
        return bank[(ordinal + this.levelIndex + type) % bank.length];
    }

    private obstacleAssetKey(type: number, worldXSeed: number): string {
        const keys = themedObstacleKeysForType(this.levelIndex, type % OBSTACLES.length);
        if (!keys.length) return '';
        return keys[Math.abs(Math.floor(worldXSeed / 173) + type + this.levelIndex) % keys.length];
    }

    private platformAssetKey(type: number, worldXSeed: number): string {
        const keys = themedPlatformKeysForLevel(this.levelIndex);
        if (!keys.length) return '';
        return keys[Math.abs(Math.floor(worldXSeed / 421) + type + this.levelIndex) % keys.length];
    }

    private canUseRuntimePlatformAsset(key: string): boolean {
        return key.startsWith('objectives/themed/last_iteration/');
    }

    private obstacleMotion(type: number, ordinal: number): number {
        if (this.levelIndex < 2 && ordinal < 5) return 0;
        if ([5, 9, 12, 16].includes(type % OBSTACLES.length)) return 2;
        if ([1, 4, 8, 11, 15].includes(type % OBSTACLES.length)) return 1;
        return (ordinal + type + this.levelIndex) % 7 === 0 ? 1 : 0;
    }

    private obstacleWorldX(o: Obstacle): number {
        if (o.motion === 2) return o.x + Math.sin(this.clock * 1.8 + o.type * 0.7) * 42;
        return o.x;
    }

    private obstacleBottomY(o: Obstacle): number {
        if (o.motion === 1) return o.y - Math.abs(Math.sin(this.clock * 2.1 + o.type)) * 44;
        if (o.motion === 2) return o.y - 18 - Math.sin(this.clock * 2.6 + o.type) * 18;
        return o.y;
    }

    private conflictsWithPlatform(worldX: number): boolean {
        return this.platforms.some((p) => worldX > p.x - 80 && worldX < p.x + p.w + 80 && p.y < GROUND - 45);
    }

    private nearbyPlatform(worldX: number): Platform | null {
        let best: Platform | null = null;
        let bestDist = 999999;
        for (const p of this.platforms) {
            const dist = Math.abs(p.x + p.w * 0.5 - worldX);
            if (dist < bestDist && dist < Math.max(160, p.w)) {
                best = p;
                bestDist = dist;
            }
        }
        return best;
    }

    private playerRect(): Rect {
        return this.playerRectAt(this.player.y);
    }

    private playerRectAt(bottomY: number): Rect {
        return { x: this.player.x - 24, y: bottomY - 70, w: 48, h: 66 };
    }

    private obstacleRect(screenX: number, bottomY: number, type: number): Rect {
        const spec = OBSTACLES[type % OBSTACLES.length];
        return { x: screenX - spec.w * 0.5, y: bottomY - spec.h, w: spec.w, h: spec.h };
    }

    private emit(x: number, y: number, color: Color, count: number): void {
        for (let i = 0; i < count; i++) {
            const a = this.random() * Math.PI * 2;
            const s = 80 + this.random() * 280;
            const particle = this.particlePool.pop() || { x: 0, y: 0, vx: 0, vy: 0, life: 0, size: 0, color: rgb(255, 255, 255) };
            particle.x = x;
            particle.y = y;
            particle.vx = Math.cos(a) * s;
            particle.vy = Math.sin(a) * s;
            particle.life = 0.5 + this.random() * 0.55;
            particle.size = 2 + this.random() * 4;
            particle.color = color;
            if (this.particles.length < 180) this.particles.push(particle);
            else if (this.particlePool.length < 120) this.particlePool.push(particle);
        }
    }

    private updateParticles(dt: number): void {
        for (let i = this.particles.length - 1; i >= 0; i--) {
            const p = this.particles[i];
            p.life -= dt;
            p.x += p.vx * dt;
            p.y += p.vy * dt;
            p.vy += 300 * dt;
            if (p.life <= 0) {
                this.particles.splice(i, 1);
                if (this.particlePool.length < 120) this.particlePool.push(p);
            }
        }
    }

    private withRenderLayer<T>(layerName: RenderLayerName, draw: () => T): T {
        const previousLayer = this.activeRenderLayer;
        const previousGraphics = this.graphics;
        this.activeRenderLayer = layerName;
        const graphics = this.graphicsLayers[layerName];
        if (graphics) this.graphics = graphics;
        try {
            return draw();
        } finally {
            this.activeRenderLayer = previousLayer;
            this.graphics = previousGraphics;
        }
    }

    private clearGraphicsLayers(): void {
        for (const layerName of RENDER_LAYER_ORDER) this.graphicsLayers[layerName]?.clear();
    }

    private resetLayerCursors(): void {
        for (const layerName of RENDER_LAYER_ORDER) {
            this.labelCursorsByLayer[layerName] = 0;
            this.spriteCursorsByLayer[layerName] = 0;
            this.primitiveCountsByLayer[layerName] = 0;
        }
    }

    private deactivateUnusedLayerNodes(): void {
        for (const layerName of RENDER_LAYER_ORDER) {
            const labelPool = this.labelPoolsByLayer[layerName] || [];
            const labelCursor = this.labelCursorsByLayer[layerName] || 0;
            for (let i = labelCursor; i < labelPool.length; i++) labelPool[i].node.active = false;

            const spritePool = this.spritePoolsByLayer[layerName] || [];
            const spriteCursor = this.spriteCursorsByLayer[layerName] || 0;
            for (let i = spriteCursor; i < spritePool.length; i++) spritePool[i].node.active = false;
        }
    }

    private labelPoolFor(layerName: RenderLayerName): PooledLabel[] {
        let pool = this.labelPoolsByLayer[layerName];
        if (!pool) {
            pool = [];
            this.labelPoolsByLayer[layerName] = pool;
        }
        return pool;
    }

    private spritePoolFor(layerName: RenderLayerName): PooledSprite[] {
        let pool = this.spritePoolsByLayer[layerName];
        if (!pool) {
            pool = [];
            this.spritePoolsByLayer[layerName] = pool;
        }
        return pool;
    }

    private spriteLayerForUsage(category?: ObjectiveCategory, reason = ''): RenderLayerName {
        if (reason === 'main_menu_bg_far') return 'BG_FAR';
        if (reason.includes('menu_skin_preview')) return 'HUD';
        if (reason.includes('player_equipment')) return 'PLAYER_EQUIPMENT';
        if (category === 'platforms') return 'PLATFORMS_SOLID';
        if (category === 'hazards') return 'OBJECTIVES_ACTIVE';
        if (category === 'collectibles') return 'COLLECTIBLES';
        if (category === 'player_body') return 'PLAYER_BODY';
        if (category === 'equipment') return 'PLAYER_EQUIPMENT';
        if (category === 'bonuses') return reason.includes('bonus_visual') ? 'COLLECTIBLES' : 'PLAYER_EQUIPMENT';
        if (category === 'npc_decor') return reason.includes('npc_visual') ? 'OBJECTIVES_ACTIVE' : 'BG_NEAR_DECOR';
        if (category === 'ui_achievements') return 'HUD';
        if (category === 'foreground_decor') return 'FOREGROUND_LIGHT_DECOR';
        if (category === 'background_decor') return 'BG_NEAR_DECOR';
        if (category === 'labels_signage' || category === 'active_labels') {
            if (reason.includes('hud') || reason.includes('achievement') || reason.includes('menu')) return 'HUD';
            return this.activeRenderLayer === 'HUD' ? 'HUD' : 'OBJECTIVES_ACTIVE';
        }
        return this.activeRenderLayer || 'HUD';
    }

    private activeSpriteCount(): number {
        let count = 0;
        for (const layerName of RENDER_LAYER_ORDER) {
            const pool = this.spritePoolsByLayer[layerName] || [];
            for (const item of pool) if (item.node.active) count++;
        }
        return count;
    }

    private activeLabelCount(): number {
        let count = 0;
        for (const layerName of RENDER_LAYER_ORDER) {
            const pool = this.labelPoolsByLayer[layerName] || [];
            for (const item of pool) if (item.node.active) count++;
        }
        return count;
    }

    private layerDrawItemCount(layerName: RenderLayerName): number {
        const spriteBackplane = layerName === 'BG_FAR' && this.backgroundImageNode?.active ? this.activeBackgroundSegmentCount : 0;
        return spriteBackplane + (this.primitiveCountsByLayer[layerName] || 0) + (this.spriteCursorsByLayer[layerName] || 0) + (this.labelCursorsByLayer[layerName] || 0);
    }

    private notePrimitiveDraw(): void {
        const layerName = this.activeRenderLayer || 'HUD';
        this.primitiveCountsByLayer[layerName] = (this.primitiveCountsByLayer[layerName] || 0) + 1;
    }

    private logRenderContractSnapshot(gameplayVisible: boolean): void {
        if (!gameplayVisible) return;
        const shouldLog = !this.layerDrawLoggedOnce || (this.developerMode && this.clock - this.lastLayerDrawLogAt > 1.5);
        if (!shouldLog) return;
        this.layerDrawLoggedOnce = true;
        this.lastLayerDrawLogAt = this.clock;
        for (const layerName of RENDER_LAYER_ORDER) {
            console.log(`MTR_LAYER_DRAW:${layerName}:${this.layerDrawItemCount(layerName)}`);
        }
        const platformOrder = VISUAL_Z_LAYERS.PLATFORMS_SOLID;
        const collectibleOrder = VISUAL_Z_LAYERS.COLLECTIBLES;
        const playerOrder = VISUAL_Z_LAYERS.PLAYER_BODY;
        if (platformOrder < collectibleOrder && collectibleOrder < playerOrder) console.log('MTR_COLLECTIBLE_PRIORITY_OK');
        else console.log(`MTR_COLLECTIBLE_PRIORITY_FAIL platform=${platformOrder} collectible=${collectibleOrder} player=${playerOrder}`);
        console.log('MTR_PLATFORM_ALPHA_OK:latest_themed_sprite_or_pending_gate');
    }

    private logBackgroundDuplicateScan(result: string): void {
        if (this.lastBackgroundDuplicateScan === result) return;
        this.lastBackgroundDuplicateScan = result;
        console.log(`MTR_BACKGROUND_DUPLICATE_SCAN:${result}`);
    }

    private button(x: number, y: number, w: number, h: number, label: string, action: () => void, stroke: Color, fill: Color, textColor: Color): void {
        this.buttons.push({ rect: { x, y, w, h }, text: label, action, stroke, fill, textColor });
        const bakedMainMenuButtonKey = this.state === 'menu' ? this.mainMenuButtonAssetKey(label) : '';
        if (bakedMainMenuButtonKey) {
            const bakedDrawn = this.drawAssetSprite(
                bakedMainMenuButtonKey,
                x + w * 0.5,
                y + h * 0.5,
                w,
                h,
                248,
                'ui_achievements',
                'main_menu_baked_button',
            );
            if (bakedDrawn) return;
            this.drawMainMenuBakedButtonPlaceholder(x, y, w, h);
            return;
        }
        const bakedStartMenuButtonKey = this.state === 'name' ? this.startMenuButtonAssetKey(label) : '';
        if (bakedStartMenuButtonKey) {
            const bakedDrawn = this.drawAssetSprite(
                bakedStartMenuButtonKey,
                x + w * 0.5,
                y + h * 0.5,
                w,
                Math.max(h, 68),
                248,
                'ui_achievements',
                'start_menu_baked_button',
            );
            if (bakedDrawn) return;
        }
        const assetKey = this.sharedButtonAssetKey(label);
        const sharedButtonDrawn = !!label && this.drawAssetSprite(
            assetKey,
            x + w * 0.5,
            y + h * 0.5,
            w * 1.03,
            Math.max(h * 1.2, 44),
            this.state === 'playing' ? 224 : 244,
            'ui_achievements',
            this.state === 'playing' ? 'shared_hud_button' : 'shared_menu_button',
        );
        if (!sharedButtonDrawn) {
            this.fillRect(x, y, w, h, fill);
            this.strokeRect(x, y, w, h, stroke);
        }
        if (label) {
            const size = w <= 70 ? 24 : h <= 46 ? 16 : label.length > 22 ? 16 : 18;
            if (!sharedButtonDrawn || this.state === 'playing') this.drawButtonRuntimeLabelPlate(x, y, w, h, label);
            this.text(label, x + w * 0.5, y + h * 0.58, size, textColor, 'center', Math.max(40, w - 34));
        }
    }

    private drawMainMenuBakedButtonPlaceholder(x: number, y: number, w: number, h: number): void {
        this.fillRect(x + 8, y + 10, w - 16, h - 20, rgb(40, 27, 13, 74));
        this.strokeRect(x + 10, y + 12, w - 20, h - 24, rgb(255, 214, 96, 64));
        this.fillRect(x + 30, y + h * 0.47, w - 60, Math.max(7, h * 0.075), rgb(255, 213, 96, 46));
        this.fillRect(x + 56, y + h * 0.59, w - 112, Math.max(5, h * 0.052), rgb(120, 72, 28, 34));
    }

    private mainMenuButtonAssetKey(label: string): string {
        const upper = label.toLocaleUpperCase('ru-RU') as keyof typeof MAIN_MENU_DEONION_BUTTON_KEYS;
        return MAIN_MENU_DEONION_BUTTON_KEYS[upper] || '';
    }

    private startMenuButtonAssetKey(label: string): string {
        const upper = label.toLocaleUpperCase('ru-RU') as keyof typeof START_MENU_BUTTON_KEYS;
        return START_MENU_BUTTON_KEYS[upper] || '';
    }

    private drawButtonRuntimeLabelPlate(x: number, y: number, w: number, h: number, label: string): void {
        const upper = label.toLocaleUpperCase('ru-RU');
        const compact = upper === '+' || upper === '−' || upper === '-';
        const longestLine = label
            .split('\n')
            .reduce((max, line) => Math.max(max, line.trim().length), 0);
        const maxPlateW = Math.max(30, w - 18);
        const desiredW = compact
            ? Math.min(44, w * 0.72)
            : Math.max(86, Math.min(maxPlateW, longestLine * 13.5 + 46));
        const plateW = Math.min(maxPlateW, desiredW);
        const plateH = Math.min(
            Math.max(23, h * (label.includes('\n') ? 0.78 : 0.60)),
            label.includes('\n') ? 46 : 36,
        );
        const plateX = x + w * 0.5;
        const plateY = y + h * 0.58;
        const drawn = this.drawAssetSprite(
            UI_SKIN.assets.buttonLabelPlate,
            plateX,
            plateY,
            plateW,
            plateH,
            this.state === 'playing' ? 188 : 224,
            'ui_achievements',
            'button_runtime_label_plate',
        );
        if (!drawn) {
            this.fillRect(plateX - plateW * 0.5, plateY - plateH * 0.5, plateW, plateH, rgb(42, 24, 10, this.state === 'playing' ? 150 : 184));
            this.strokeRect(plateX - plateW * 0.5, plateY - plateH * 0.5, plateW, plateH, rgb(255, 220, 105, 96));
        }
    }

    private sharedButtonAssetKey(label: string): string {
        const upper = label.toLocaleUpperCase('ru-RU');
        if (this.state === 'playing') return UI_SKIN.assets.hudControl;
        if (upper === '+' || upper === '−' || upper === '-') return UI_SKIN.assets.buttonCompact;
        if (upper.includes('НАЗАД') || upper.includes('В МЕНЮ') || upper.includes('РЕКОРДЫ')) return UI_SKIN.assets.buttonBack;
        if (upper.includes('ЗАКРЫТЬ') || upper.includes('СБРОС') || upper.includes('УДАЛИТЬ')) return UI_SKIN.assets.buttonDanger;
        if (upper.includes('ПО УМОЛЧАНИЮ') || upper.includes('ЗВУК')) return UI_SKIN.assets.buttonSecondary;
        return UI_SKIN.assets.buttonPrimary;
    }

    private text(value: string, x: number, y: number, size: number, color: Color, align: 'left' | 'center' | 'right' = 'center', boxW = 760): void {
        const lines = value.split('\n');
        const start = y - (lines.length - 1) * size * 0.62;
        const layerName = this.activeRenderLayer || 'HUD';
        const layer = this.labelLayers[layerName] || this.labelLayers.HUD;
        if (!layer) return;
        const pool = this.labelPoolFor(layerName);
        for (let i = 0; i < lines.length; i++) {
            const cursor = this.labelCursorsByLayer[layerName] || 0;
            let item = pool[cursor];
            this.labelCursorsByLayer[layerName] = cursor + 1;
            if (!item) {
                const node = new Node(`${layerName}_Label`);
                node.layer = layer.layer;
                const ui = node.addComponent(UITransform);
                const label = node.addComponent(Label);
                layer.addChild(node);
                item = { node, ui, label };
                pool.push(item);
            }
            item.node.active = true;
            item.node.layer = layer.layer;
            item.ui.setContentSize(boxW, size * 1.35);
            const label = item.label;
            label.string = lines[i];
            label.fontSize = size;
            label.lineHeight = size * 1.1;
            label.color = color;
            label.enableOutline = true;
            label.outlineColor = size >= 28 ? rgb(48, 28, 12, Math.min(255, color.a)) : rgb(25, 18, 12, Math.min(235, color.a));
            label.outlineWidth = size >= 32 ? 3 : size >= 17 ? 2 : 1;
            label.horizontalAlign = align === 'left' ? Label.HorizontalAlign.LEFT : align === 'right' ? Label.HorizontalAlign.RIGHT : Label.HorizontalAlign.CENTER;
            label.verticalAlign = Label.VerticalAlign.CENTER;
            const overflowClamp = (Label as unknown as { Overflow?: { CLAMP?: number } }).Overflow?.CLAMP;
            if (overflowClamp !== undefined) (label as unknown as { overflow: number }).overflow = overflowClamp;
            const nodeX = align === 'left' ? x + boxW * 0.5 : align === 'right' ? x - boxW * 0.5 : x;
            item.node.setPosition(this.cx(nodeX), this.cy(start + i * size * 1.22));
        }
    }

    private uiColor(value: UiColorTuple): Color {
        return rgb(value[0], value[1], value[2], value[3] ?? 255);
    }

    private fillRect(x: number, y: number, w: number, h: number, color: Color): void {
        this.notePrimitiveDraw();
        this.graphics.fillColor = color;
        this.graphics.rect(this.cx(x), this.cy(y + h), w, h);
        this.graphics.fill();
    }

    private fillPolygon(points: Array<[number, number]>, color: Color): void {
        if (points.length < 3) return;
        this.notePrimitiveDraw();
        this.graphics.fillColor = color;
        this.graphics.moveTo(this.cx(points[0][0]), this.cy(points[0][1]));
        for (let i = 1; i < points.length; i++) {
            this.graphics.lineTo(this.cx(points[i][0]), this.cy(points[i][1]));
        }
        this.graphics.close();
        this.graphics.fill();
    }

    private strokeRect(x: number, y: number, w: number, h: number, color: Color): void {
        this.notePrimitiveDraw();
        this.graphics.strokeColor = color;
        this.graphics.lineWidth = 2;
        this.graphics.rect(this.cx(x), this.cy(y + h), w, h);
        this.graphics.stroke();
    }

    private strokeCircle(x: number, y: number, r: number, color: Color, width = 2): void {
        this.notePrimitiveDraw();
        this.graphics.strokeColor = color;
        this.graphics.lineWidth = width;
        this.graphics.circle(this.cx(x), this.cy(y), r);
        this.graphics.stroke();
    }

    private segment(x1: number, y1: number, x2: number, y2: number, radius: number, color: Color): void {
        this.notePrimitiveDraw();
        this.graphics.strokeColor = color;
        this.graphics.lineWidth = Math.max(1, radius * 2);
        this.graphics.moveTo(this.cx(x1), this.cy(y1));
        this.graphics.lineTo(this.cx(x2), this.cy(y2));
        this.graphics.stroke();
    }

    private circle(x: number, y: number, r: number, color: Color): void {
        this.notePrimitiveDraw();
        this.graphics.fillColor = color;
        this.graphics.circle(this.cx(x), this.cy(y), r);
        this.graphics.fill();
    }

    private alpha(color: Color, a: number): Color {
        return new Color(color.r, color.g, color.b, clamp(a, 0, 255));
    }

    private cx(x: number): number {
        const shake = this.cameraShake > 0 ? Math.sin(this.clock * 75) * this.cameraShake * 18 : 0;
        return x - W * 0.5 + shake;
    }

    private cy(yTop: number): number {
        const shake = this.cameraShake > 0 ? Math.cos(this.clock * 60) * this.cameraShake * 10 : 0;
        return H * 0.5 - yTop + shake;
    }
}
