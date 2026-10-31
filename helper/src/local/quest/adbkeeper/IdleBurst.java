package local.quest.adbkeeper;

/** Decides when repeated empty-home retries mean Meta VR Home has no open panel. */
final class IdleBurst {
    static final int HITS=5;
    static final long WINDOW_MS=2000,COOLDOWN_MS=20000;
    private final long[] times=new long[HITS];
    private int count,next;
    private long lastFired=-COOLDOWN_MS;

    boolean hit(long now) {
        times[next]=now; next=(next+1)%HITS; if (count<HITS) count++;
        if (count<HITS || now-times[next] > WINDOW_MS || now-lastFired < COOLDOWN_MS) return false;
        lastFired=now; count=0;
        return true;
    }
    void reset() { count=0; }
}
