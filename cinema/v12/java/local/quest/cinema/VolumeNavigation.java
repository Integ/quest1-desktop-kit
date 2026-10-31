package local.quest.cinema;

import android.app.Activity;
import android.content.Intent;
import android.os.Handler;
import android.os.Looper;
import android.os.SystemClock;
import android.util.Log;
import android.view.InputDevice;
import android.view.KeyCharacterMap;
import android.view.KeyEvent;
import java.lang.ref.WeakReference;
import java.util.HashMap;
import java.util.Map;

/** Maps physical volume taps and holds to Cinema's gaze and gamepad controls. */
public final class VolumeNavigation {
    private static final VolumeKeyState state=new VolumeKeyState();
    private static final VolumeShortcutState shortcut=new VolumeShortcutState();
    private static final Handler main=new Handler(Looper.getMainLooper());
    private static final Map<Integer,Runnable> releases=new HashMap<Integer,Runnable>();
    private static WeakReference<Activity> owner=new WeakReference<Activity>(null);
    private static Runnable holding;
    private static Runnable shortcutTimeout;
    private static long nextActionAt;

    public static boolean onKey(final Activity activity, KeyEvent event) {
        final int code=event.getKeyCode();
        if (code != KeyEvent.KEYCODE_VOLUME_UP && code != KeyEvent.KEYCODE_VOLUME_DOWN) return false;
        if (owner.get() != activity) {
            Activity previous=owner.get();
            if (previous != null) reset(previous);
            owner=new WeakReference<Activity>(activity);
        }
        if (event.getAction() == KeyEvent.ACTION_DOWN) {
            if (event.getRepeatCount() != 0 || !state.press(code,event.getEventTime())) return true;
            if (holding != null) main.removeCallbacks(holding);
            holding=new Runnable() {
                public void run() {
                    holding=null;
                    handleAction(activity,state.hold(SystemClock.uptimeMillis()));
                }
            };
            main.postDelayed(holding,VolumeKeyState.HOLD_MS);
        } else if (event.getAction() == KeyEvent.ACTION_UP && state.activeCode() == code) {
            if (holding != null) main.removeCallbacks(holding);
            holding=null;
            if (event.isCanceled()) {
                state.cancel(); shortcut.cancel();
                if (shortcutTimeout != null) main.removeCallbacks(shortcutTimeout);
                shortcutTimeout=null;
            } else handleAction(activity,state.release(code,event.getEventTime()));
        }
        return true;
    }

    private static void handleAction(final Activity activity,int action) {
        if (action == VolumeKeyState.NONE) return;
        if (shortcutTimeout != null) main.removeCallbacks(shortcutTimeout);
        shortcutTimeout=null;
        queue(activity,shortcut.accept(action,SystemClock.uptimeMillis()));
        if (shortcut.pending()) {
            shortcutTimeout=new Runnable() {
                public void run() {
                    shortcutTimeout=null;
                    queue(activity,shortcut.expire(SystemClock.uptimeMillis()));
                }
            };
            main.postAtTime(shortcutTimeout,shortcut.deadline());
        }
    }

    private static void queue(final Activity activity,int[] actions) {
        for (final int action:actions) {
            long at=Math.max(SystemClock.uptimeMillis(),nextActionAt);
            nextActionAt=at+180;
            main.postAtTime(new Runnable() {
                public void run() {
                    if (owner.get() != activity || activity.isFinishing()) return;
                    if (action == VolumeShortcutState.OPEN_APP_LIST) openAppList(activity);
                    else perform(activity,action);
                }
            },at);
        }
    }

    private static void openAppList(Activity activity) {
        Intent launcher=activity.getPackageManager().getLaunchIntentForPackage("com.threethan.launcher");
        if (launcher == null) { Log.w("QuestVolume","App list is not installed"); return; }
        launcher.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK|Intent.FLAG_ACTIVITY_REORDER_TO_FRONT);
        reset(activity);
        try {
            activity.startActivity(launcher);
            Log.i("QuestVolume","Opened app list from volume shortcut");
        } catch (RuntimeException e) { Log.w("QuestVolume","Cannot open app list",e); }
    }

    private static int source(int key) {
        // Legacy VrActivity requires exactly 0x501 to mark DPAD as a joypad.
        return key == KeyEvent.KEYCODE_DPAD_LEFT || key == KeyEvent.KEYCODE_DPAD_RIGHT
            ? InputDevice.SOURCE_GAMEPAD | InputDevice.SOURCE_KEYBOARD
            : InputDevice.SOURCE_KEYBOARD;
    }
    private static void send(Activity activity, int key, int action) {
        long now=SystemClock.uptimeMillis();
        activity.dispatchKeyEvent(new KeyEvent(now,now,action,key,0,0,
            KeyCharacterMap.VIRTUAL_KEYBOARD,0,0,source(key)));
    }
    private static void perform(final Activity activity,int action) {
        if (action == VolumeKeyState.NONE || activity.isFinishing()) return;
        final int key=action == VolumeKeyState.CONFIRM ? KeyEvent.KEYCODE_BUTTON_A
                    : action == VolumeKeyState.BACK ? KeyEvent.KEYCODE_BACK
                    : action == VolumeKeyState.LEFT ? KeyEvent.KEYCODE_DPAD_LEFT
                    : KeyEvent.KEYCODE_DPAD_RIGHT;
        Runnable previous=releases.remove(key);
        if (previous != null) { main.removeCallbacks(previous); send(activity,key,KeyEvent.ACTION_UP); }
        send(activity,key,KeyEvent.ACTION_DOWN);
        Log.i("QuestVolume","action="+action+" key="+key+" source="+source(key));
        Runnable release=new Runnable() {
            public void run() {
                if (releases.get(key) != this) return;
                releases.remove(key);
                send(activity,key,KeyEvent.ACTION_UP);
            }
        };
        releases.put(key,release);
        main.postDelayed(release,120);
    }
    public static void reset(Activity activity) {
        state.cancel(); shortcut.cancel(); holding=null; shortcutTimeout=null; nextActionAt=0;
        main.removeCallbacksAndMessages(null);
        for (Integer key:releases.keySet()) send(activity,key,KeyEvent.ACTION_UP);
        releases.clear();
        owner.clear();
    }
}
