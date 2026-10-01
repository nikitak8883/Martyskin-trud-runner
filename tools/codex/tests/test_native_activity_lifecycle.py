"""Static native-bridge/order contracts; actual Java/runtime acceptance uses the emulator."""
from pathlib import Path
import re
import unittest
import importlib.util

ROOT = Path(__file__).resolve().parents[3]
ACTIVITY = ROOT / "native/engine/android/app/src/com/cocos/game/AppActivity.java"
QA = ROOT / "tools/codex/Run-MtrAndroidNativeLifecycleQa.ps1"


def body(source, name):
    match = re.search(r"(?:private|protected|public)\s+(?:static\s+)?(?:void|String)\s+" + name + r"\([^)]*\)\s*\{", source)
    if not match:
        raise ValueError(f"Missing method {name}")
    start = match.end()
    depth = 1
    for index in range(start, len(source)):
        depth += (source[index] == "{") - (source[index] == "}")
        if depth == 0:
            return source[start:index]
    raise ValueError(f"Unclosed method {name}")


def assert_intent_contract(source):
    latest = body(source, "onNewIntent")
    positions = [latest.find(call) for call in (
        "setIntent(intent);", "updateStartupQueryFromIntent(intent);",
        "super.onNewIntent(intent);", "SDKWrapper.shared().onNewIntent(intent);",
    )]
    if min(positions) < 0 or positions != sorted(positions):
        raise ValueError("Latest Intent must be retained before bridge/super/SDK forwarding")
    create = body(source, "onCreate")
    if create.find("updateStartupQueryFromIntent(getIntent());") < 0 or not (
        create.index("updateStartupQueryFromIntent(getIntent());") < create.index("super.onCreate(savedInstanceState);")
    ):
        raise ValueError("Recreation must read the retained Intent before native create")


class NativeActivityContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = ACTIVITY.read_text(encoding="utf-8")
        cls.qa = QA.read_text(encoding="utf-8")

    def test_actual_latest_intent_order(self):
        assert_intent_contract(self.source)

    def test_missing_set_intent_negative(self):
        with self.assertRaises(ValueError):
            assert_intent_contract(self.source.replace("setIntent(intent);", ""))

    def test_set_intent_after_super_negative(self):
        wrong = self.source.replace("setIntent(intent);", "").replace(
            "super.onNewIntent(intent);", "super.onNewIntent(intent); setIntent(intent);")
        with self.assertRaises(ValueError):
            assert_intent_contract(wrong)

    def test_create_after_native_negative(self):
        wrong = self.source.replace("updateStartupQueryFromIntent(getIntent());", "").replace(
            "super.onCreate(savedInstanceState);", "super.onCreate(savedInstanceState); updateStartupQueryFromIntent(getIntent());")
        with self.assertRaises(ValueError):
            assert_intent_contract(wrong)

    def test_debug_only_trace_and_no_user_data(self):
        create = body(self.source, "onCreate")
        self.assertIn("ApplicationInfo.FLAG_DEBUGGABLE", create)
        self.assertLess(create.index("lifecycleTraceEnabled ="), create.index("traceLifecycle("))
        trace = body(self.source, "traceLifecycle")
        self.assertLess(trace.index("if (!lifecycleTraceEnabled) return;"), trace.index("getResources()"))
        for forbidden in ("getIntent", "startupQuery", "getQuery", "getExtras", ".toString", "SDKWrapper"):
            self.assertNotIn(forbidden, trace)

    def test_lifecycle_entry_and_completion(self):
        for method, event in (("onStart", "start"), ("onResume", "resume"), ("onPause", "pause"),
                              ("onStop", "stop"), ("onNewIntent", "new_intent"),
                              ("onSaveInstanceState", "save"), ("onConfigurationChanged", "configuration")):
            fragment = body(self.source, method)
            self.assertIn(f'traceLifecycle("{event}_enter");', fragment)
            self.assertIn(f'traceLifecycle("{event}_ready");', fragment)
        destroy = body(self.source, "onDestroy")
        self.assertLess(destroy.index('traceLifecycle("destroy_enter");'), destroy.index("super.onDestroy();"))
        self.assertLess(destroy.index("super.onDestroy();"), destroy.index('traceLifecycle("destroy_after_cocos");'))

    def test_qa_strict_identity_audio_and_recreation(self):
        for guard in ("Assert-MtrAndroidQaAudioMuted", "Installed APK differs", "QA must use emulator user0",
                      "same_pid_expected", "create_enter_saved", "destroy_ready", "Evidence directory already exists"):
            self.assertIn(guard, self.qa)
        self.assertIn("'shell','sha256sum'", self.qa)
        self.assertIn("expected_case_count=5", self.qa)
        self.assertIn("retry_count=0", self.qa)
        self.assertIn("$watch.ElapsedMilliseconds -lt 35000", self.qa)

    def test_qa_restoration_fail_closed(self):
        self.assertIn("finally {", self.qa)
        self.assertIn("density.finally-restore.stdout.txt", self.qa)
        self.assertIn("Density restoration differs", self.qa)
        self.assertIn("if ($status -ne 'pass') { exit 1 }", self.qa)
        self.assertNotIn("AllowPhysicalDevice", self.qa)

    def test_default_launch_requires_no_stale_qa_query(self):
        self.assertIn("'fresh-default-menu' 'menu' $null $false", self.qa)
        self.assertIn("$state.log -notmatch 'MTR_NATIVE_STARTUP_QUERY_READY|MTR_QA_SCREEN_READY'", self.qa)
        self.assertIn("$changedState.instance -eq $initial.instance", self.qa)
        self.assertIn("$restored.instance -eq $changedState.instance", self.qa)

    def test_silent_inventory_discovers_compact_launch_arrays(self):
        path = ROOT / "tools/codex/validate_android_emulator_audio_policy.py"
        spec = importlib.util.spec_from_file_location("mtr_audio_inventory", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        for spelling in ("'am', 'start'", "'am','start'", '"am",\n"start"'):
            self.assertTrue(module.has_am_start(spelling))
        self.assertFalse(module.has_am_start("'am','get-current-user'"))
        self.assertTrue(module.has_am_start(self.qa))


if __name__ == "__main__":
    unittest.main()
