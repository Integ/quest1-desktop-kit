package local.quest.cinema;

/** Separates navigation from media-volume input; Android-free for host regression tests. */
public final class VolumeModeState {
    public static final int NAVIGATE=0, CONSUMED=1, ENTER=2, EXIT=3, RAISE=4, LOWER=5;
    public static final long CHORD_MS=350, IDLE_MS=6000, REPEAT_MS=150;
    private int pressed, adjusted;
    private boolean volume, suppressChord;
    private long firstDown, lastActivity, lastAdjustment;

    public boolean volumeMode() { return volume; }
    public long deadline() { return volume && pressed == 0 ? lastActivity+IDLE_MS : 0; }

    public int key(int code, boolean down, int repeat, long now, boolean cancelled) {
        int bit=code == 24 ? 1 : code == 25 ? 2 : 0;
        if (bit == 0) return NAVIGATE;
        if (down) {
            boolean fresh=(pressed & bit) == 0;
            if (fresh) {
                adjusted &= ~bit;
                if (pressed == 0) firstDown=now;
                pressed |= bit;
                if (pressed == 3 && !suppressChord && now >= firstDown && now-firstDown <= CHORD_MS) {
                    volume=!volume;
                    suppressChord=true;
                    lastActivity=now;
                    return volume ? ENTER : EXIT;
                }
            }
            if (suppressChord) return CONSUMED;
            if (!volume) return NAVIGATE;
            lastActivity=now;
            // Wait for release/repeat: the first half of an exit chord must not change volume.
            if (!fresh && repeat > 0 && now-firstDown > CHORD_MS && now-lastAdjustment >= REPEAT_MS) {
                lastAdjustment=now;
                adjusted |= bit;
                return code == 24 ? RAISE : LOWER;
            }
            return CONSUMED;
        }
        boolean held=(pressed & bit) != 0;
        boolean changed=(adjusted & bit) != 0;
        pressed &= ~bit;
        adjusted &= ~bit;
        if (volume) lastActivity=now;
        if (suppressChord) {
            if (pressed == 0) suppressChord=false;
            return CONSUMED;
        }
        if (volume) return !held || cancelled || changed ? CONSUMED : code == 24 ? RAISE : LOWER;
        return NAVIGATE;
    }

    public boolean expire(long now) {
        if (!volume || pressed != 0 || now >= lastActivity && now < lastActivity+IDLE_MS) return false;
        volume=false;
        return true;
    }

    public void reset() {
        pressed=0; adjusted=0; volume=false; suppressChord=false;
        firstDown=0; lastActivity=0; lastAdjustment=0;
    }
}
