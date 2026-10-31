package local.quest.adbkeeper;

import android.content.Context;
import android.os.Handler;
import android.os.PowerManager;
import android.os.SystemClock;
import android.util.Log;
import java.io.BufferedReader;
import java.io.InputStreamReader;

/**
 * With FirstTimeNux and the store disabled, an empty Meta VR Home retries both panels many times
 * per second. Watching only that log line (READ_LOGS granted over ADB), open the app list instead.
 */
final class HomeIdleWatcher {
    static final String PATTERN="LaunchFirstTimeNux\\(crash_recovery\\)";
    static int bursts;
    static String result="not_started";
    private final Context context;
    private final Handler handler;
    private final IdleBurst burst=new IdleBurst();
    private volatile boolean running;
    private Process process;

    HomeIdleWatcher(Context context, Handler handler) { this.context=context; this.handler=handler; }

    static boolean permitted(Context c) {
        return c.checkSelfPermission("android.permission.READ_LOGS") == android.content.pm.PackageManager.PERMISSION_GRANTED;
    }

    void start() {
        if (running) return;
        if (!permitted(context)) { result="read_logs_not_granted"; return; }
        running=true;
        new Thread(new Runnable() { public void run() { loop(); } },"HomeIdleWatcher").start();
    }

    void stop() {
        running=false;
        Process p=process; if (p != null) p.destroy();
    }

    private void loop() {
        while (running) {
            try {
                process=Runtime.getRuntime().exec(new String[]{"logcat","-b","main","-v","brief","-T","1","--regex="+PATTERN});
                result="watching";
                BufferedReader in=new BufferedReader(new InputStreamReader(process.getInputStream()));
                String line;
                while (running && (line=in.readLine()) != null) {
                    if (line.contains("LaunchFirstTimeNux(crash_recovery)")) onHit();
                }
            } catch (Exception e) {
                result="logcat_failed"; Log.w("QuestHomeIdle","logcat unavailable",e);
            } finally {
                Process p=process; if (p != null) p.destroy();
            }
            if (running) SystemClock.sleep(5000);
        }
    }

    private void onHit() {
        PowerManager power=(PowerManager)context.getSystemService(Context.POWER_SERVICE);
        if (!State.idleLauncherEnabled(context) || !power.isInteractive()) { burst.reset(); return; }
        if (!burst.hit(SystemClock.elapsedRealtime())) return;
        handler.post(new Runnable() { public void run() {
            bursts++;
            Log.i("QuestHomeIdle","Empty VR Home detected; opening app list");
            AppListShortcut.openApps(context,"home_idle");
        }});
    }
}
