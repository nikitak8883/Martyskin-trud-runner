/****************************************************************************
Copyright (c) 2015-2016 Chukong Technologies Inc.
Copyright (c) 2017-2018 Xiamen Yaji Software Co., Ltd.

http://www.cocos2d-x.org

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
****************************************************************************/
package com.cocos.game;

import android.os.Bundle;
import android.content.Intent;
import android.content.res.Configuration;
import android.net.Uri;
import android.content.pm.ApplicationInfo;
import android.os.SystemClock;
import android.util.Log;

import com.cocos.service.SDKWrapper;
import com.cocos.lib.CocosActivity;

public class AppActivity extends CocosActivity {
    private static final String[] QA_QUERY_KEYS = {
        "mtr_dev",
        "mtr_autostart",
        "mtr_level",
        "mtr_pause",
        "mtr_show_touch_zones",
        "mtr_qa_obstacles",
        "mtr_spawn_obstacles",
        "mtr_qa_bonuses",
        "mtr_spawn_bonuses",
        "mtr_skin",
        "mtr_qa_skin",
        "mtr_variant",
        "mtr_qa_variant",
        "mtr_pose",
        "mtr_qa_pose",
        "mtr_state",
        "mtr_screen",
        "debugColliders",
        "mtr_debug_readability",
        "mtr_readability_debug",
        "mtr_unlock_achievements",
        "mtr_seed_records",
        "mtr_qa_reset_loops",
        "mtr_qa_collisions",
        "mtr_qa_powerups",
        "mtr_qa_ownership",
        "mtr_qa_atlas_pilot"
    };

    private static String startupQuery = "";
    private boolean lifecycleTraceEnabled;

    // Debug-only, numeric lifecycle evidence. Never log Intent/user data.
    private void traceLifecycle(String event) {
        if (!lifecycleTraceEnabled) return;
        Configuration config = getResources().getConfiguration();
        Log.d("MtrNativeLifecycle", "MTR_NATIVE_LIFECYCLE event=" + event
            + " instance=" + System.identityHashCode(this)
            + " uptimeMs=" + SystemClock.uptimeMillis()
            + " changing=" + isChangingConfigurations()
            + " finishing=" + isFinishing()
            + " configChanges=" + getChangingConfigurations()
            + " density=" + config.densityDpi
            + " orientation=" + config.orientation
            + " uiMode=" + config.uiMode);
    }

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        lifecycleTraceEnabled = (getApplicationInfo().flags & ApplicationInfo.FLAG_DEBUGGABLE) != 0;
        traceLifecycle(savedInstanceState == null ? "create_enter_fresh" : "create_enter_saved");
        updateStartupQueryFromIntent(getIntent());
        super.onCreate(savedInstanceState);
        traceLifecycle("create_after_cocos");
        SDKWrapper.shared().init(this);
        traceLifecycle("create_ready");
    }

    public static String getStartupQuery() {
        return startupQuery;
    }

    private static void updateStartupQueryFromIntent(Intent intent) {
        StringBuilder query = new StringBuilder();
        if (intent != null && intent.getData() != null && intent.getData().getQuery() != null) {
            query.append(intent.getData().getQuery());
        }
        Bundle extras = intent != null ? intent.getExtras() : null;
        if (extras != null) {
            for (String key : QA_QUERY_KEYS) {
                if (!extras.containsKey(key)) continue;
                Object value = extras.get(key);
                if (value == null) continue;
                appendQueryParam(query, key, String.valueOf(value));
            }
        }
        startupQuery = query.toString();
    }

    private static void appendQueryParam(StringBuilder query, String key, String value) {
        if (query.length() > 0) {
            query.append('&');
        }
        query.append(Uri.encode(key));
        query.append('=');
        query.append(Uri.encode(value));
    }

    @Override
    protected void onResume() {
        traceLifecycle("resume_enter");
        super.onResume();
        SDKWrapper.shared().onResume();
        traceLifecycle("resume_ready");
    }

    @Override
    protected void onPause() {
        traceLifecycle("pause_enter");
        super.onPause();
        SDKWrapper.shared().onPause();
        traceLifecycle("pause_ready");
    }

    @Override
    protected void onDestroy() {
        traceLifecycle("destroy_enter");
        super.onDestroy();
        traceLifecycle("destroy_after_cocos");
        // Workaround in https://stackoverflow.com/questions/16283079/re-launch-of-activity-on-home-button-but-only-the-first-time/16447508
        if (!isTaskRoot()) {
            traceLifecycle("destroy_non_root");
            return;
        }
        SDKWrapper.shared().onDestroy();
        traceLifecycle("destroy_ready");
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        SDKWrapper.shared().onActivityResult(requestCode, resultCode, data);
    }

    @Override
    protected void onNewIntent(Intent intent) {
        traceLifecycle("new_intent_enter");
        // onNewIntent does not replace getIntent(); recreation must use the latest launch.
        setIntent(intent);
        updateStartupQueryFromIntent(intent);
        super.onNewIntent(intent);
        SDKWrapper.shared().onNewIntent(intent);
        traceLifecycle("new_intent_ready");
    }

    @Override
    protected void onRestart() {
        super.onRestart();
        SDKWrapper.shared().onRestart();
    }

    @Override
    protected void onStop() {
        traceLifecycle("stop_enter");
        super.onStop();
        SDKWrapper.shared().onStop();
        traceLifecycle("stop_ready");
    }

    @Override
    public void onBackPressed() {
        SDKWrapper.shared().onBackPressed();
        super.onBackPressed();
    }

    @Override
    public void onConfigurationChanged(Configuration newConfig) {
        traceLifecycle("configuration_enter");
        SDKWrapper.shared().onConfigurationChanged(newConfig);
        super.onConfigurationChanged(newConfig);
        traceLifecycle("configuration_ready");
    }

    @Override
    protected void onRestoreInstanceState(Bundle savedInstanceState) {
        SDKWrapper.shared().onRestoreInstanceState(savedInstanceState);
        super.onRestoreInstanceState(savedInstanceState);
    }

    @Override
    protected void onSaveInstanceState(Bundle outState) {
        traceLifecycle("save_enter");
        SDKWrapper.shared().onSaveInstanceState(outState);
        super.onSaveInstanceState(outState);
        traceLifecycle("save_ready");
    }

    @Override
    protected void onStart() {
        traceLifecycle("start_enter");
        SDKWrapper.shared().onStart();
        super.onStart();
        traceLifecycle("start_ready");
    }

    @Override
    public void onLowMemory() {
        SDKWrapper.shared().onLowMemory();
        super.onLowMemory();
    }
}
