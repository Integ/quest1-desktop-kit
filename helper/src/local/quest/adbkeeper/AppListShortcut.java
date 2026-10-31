package local.quest.adbkeeper;

import android.content.Context;
import android.content.Intent;
import android.os.SystemClock;
import android.provider.Settings;
import android.util.Log;

final class AppListShortcut {
    static long lastOpened=-2000;
    static int opens;
    static String result="not_triggered";
    static void open(Context context,String source) {
        if (!State.launcherShortcutEnabled(context)) { result="disabled"; return; }
        openApps(context,source);
    }
    static void openApps(Context context,String source) {
        long now=SystemClock.elapsedRealtime();
        if (now-lastOpened < 1500) return;
        if (!Settings.canDrawOverlays(context)) { result="background_permission_missing"; return; }
        Intent launcher=context.getPackageManager().getLaunchIntentForPackage("com.threethan.launcher");
        if (launcher == null) { result="launcher_missing"; return; }
        launcher.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK|Intent.FLAG_ACTIVITY_REORDER_TO_FRONT);
        try {
            context.startActivity(launcher); lastOpened=now; opens++; result="opened_from_"+source;
            Log.i("QuestQuickLaunch","Opened app list from "+source);
        } catch (RuntimeException e) { result="launch_failed"; Log.w("QuestQuickLaunch","Cannot open app list",e); }
    }
}
