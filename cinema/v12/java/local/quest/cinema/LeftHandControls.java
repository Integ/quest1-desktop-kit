package local.quest.cinema;

import android.app.Activity;
import android.os.SystemClock;
import android.os.Handler;
import android.os.Looper;
import android.util.Log;
import android.view.KeyEvent;
import android.view.MotionEvent;

/** Left Touch controls for the legacy gaze-based Cinema VR interface. */
public final class LeftHandControls {
    private static final LeftControlState state = new LeftControlState();
    private static boolean touchSent;
    private static long touchStart;
    private static final LeftTapGesture taps = new LeftTapGesture();
    private static final Handler main = new Handler(Looper.getMainLooper());

    public static boolean onTouch(final Activity activity, MotionEvent event) {
        long now = event.getEventTime();
        switch (event.getActionMasked()) {
        case MotionEvent.ACTION_DOWN:
            return taps.down(now, event.getX(), event.getY());
        case MotionEvent.ACTION_MOVE:
            taps.move(event.getX(), event.getY());
            return taps.consuming();
        case MotionEvent.ACTION_UP:
            boolean consumed = taps.consuming();
            if (taps.up(now, event.getX(), event.getY())) {
                Log.i("QuestLeft", "double tap: toggle cinema menu");
                activity.dispatchKeyEvent(new KeyEvent(KeyEvent.ACTION_DOWN, KeyEvent.KEYCODE_BACK));
                main.postDelayed(new Runnable() {
                    public void run() {
                        activity.dispatchKeyEvent(new KeyEvent(KeyEvent.ACTION_UP, KeyEvent.KEYCODE_BACK));
                    }
                }, 80);
            }
            return consumed;
        case MotionEvent.ACTION_CANCEL:
            boolean cancelled = taps.consuming();
            taps.reset();
            return cancelled;
        default:
            return false;
        }
    }

    public static boolean onKey(Activity activity, KeyEvent event) {
        if (VolumeNavigation.onKey(activity,event)) return true;
        int code = event.getKeyCode();
        boolean down = event.getAction() == KeyEvent.ACTION_DOWN;
        if (!down && event.getAction() != KeyEvent.ACTION_UP) return false;
        if (code == KeyEvent.KEYCODE_BUTTON_L2) {
            state.digital(down);
            syncTouch(activity);
            return true;
        }
        int target;
        if (code == KeyEvent.KEYCODE_BUTTON_X) target = KeyEvent.KEYCODE_BUTTON_A;
        else if (code == KeyEvent.KEYCODE_BUTTON_Y || code == KeyEvent.KEYCODE_MENU ||
                 code == KeyEvent.KEYCODE_FORWARD ||
                 code == KeyEvent.KEYCODE_BUTTON_THUMBL) target = KeyEvent.KEYCODE_BACK;
        else return false;
        KeyEvent mapped = new KeyEvent(event.getDownTime(), event.getEventTime(),
            event.getAction(), target, event.getRepeatCount(), event.getMetaState(),
            event.getDeviceId(), event.getScanCode(), event.getFlags(), event.getSource());
        Log.i("QuestLeft", "key " + code + " -> " + target + " action " + event.getAction());
        activity.dispatchKeyEvent(mapped);
        return true;
    }

    public static void onMotion(Activity activity, MotionEvent event) {
        if ((event.getSource() & 0x10) == 0) return;
        if (event.getActionMasked() == MotionEvent.ACTION_CANCEL) {
            reset(activity);
        } else if (event.getActionMasked() == MotionEvent.ACTION_MOVE) {
            float trigger = Math.max(event.getAxisValue(MotionEvent.AXIS_LTRIGGER),
                                     event.getAxisValue(MotionEvent.AXIS_BRAKE));
            state.analog(trigger);
            syncTouch(activity);
        }
    }

    private static void syncTouch(Activity activity) {
        boolean down = state.down();
        if (down == touchSent) return;
        long now = SystemClock.uptimeMillis();
        if (down) touchStart = now;
        MotionEvent touch = MotionEvent.obtain(touchStart, now,
            down ? MotionEvent.ACTION_DOWN : MotionEvent.ACTION_UP, 0, 0, 0);
        try { activity.dispatchTouchEvent(touch); }
        finally { touch.recycle(); }
        touchSent = down;
        Log.i("QuestLeft", "left trigger touch " + (down ? "down" : "up"));
    }

    public static void reset(Activity activity) {
        VolumeNavigation.reset(activity);
        taps.reset();
        state.reset();
        syncTouch(activity);
    }
}
