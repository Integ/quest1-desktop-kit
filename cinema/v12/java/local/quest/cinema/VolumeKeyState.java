package local.quest.cinema;

/** One action per physical press; long presses never also confirm or go back. */
public final class VolumeKeyState {
    public static final int NONE=0, CONFIRM=1, BACK=2, LEFT=3, RIGHT=4;
    public static final long HOLD_MS=550;
    private int code;
    private long started;
    private boolean fired;

    public int activeCode() { return code; }
    public boolean press(int key, long now) {
        if (key != 24 && key != 25) return false;
        if (key == code) return false;
        code=key; started=now; fired=false;
        return true;
    }
    public int hold(long now) {
        if (code == 0 || fired || now-started < HOLD_MS) return NONE;
        fired=true;
        return code == 24 ? RIGHT : LEFT;
    }
    public int release(int key, long now) {
        if (key != code || code == 0) return NONE;
        int action=NONE;
        if (!fired && now >= started) {
            action=now-started >= HOLD_MS ? (code == 24 ? RIGHT : LEFT)
                                        : (code == 24 ? CONFIRM : BACK);
        }
        cancel();
        return action;
    }
    public void cancel() { code=0; started=0; fired=false; }
}
