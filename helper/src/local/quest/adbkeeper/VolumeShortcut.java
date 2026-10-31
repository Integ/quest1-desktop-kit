package local.quest.adbkeeper;

/** Recognizes down/up/down/up, grouping repeat steps from a held volume button. */
public final class VolumeShortcut {
    private int step;
    private int direction;
    private long last;
    private long cooldownUntil;

    public boolean accept(int previous, int current, long now) {
        if (previous < 0 || current < 0 || current == previous) return false;
        if (now < cooldownUntil) return false;
        int delta = current - previous;
        if (Math.abs(delta) > 3) { step = 0; direction=0; return false; }
        if (step > 0 && (now < last || now - last > 1500)) { step = 0; direction=0; }
        int next = delta < 0 ? -1 : 1;
        if (step == 0) step = next == -1 ? 1 : 0;
        else if (next != direction) step++;
        direction=next;
        last = now;
        if (step == 4) {
            step = 0;
            cooldownUntil = now + 2000;
            return true;
        }
        return false;
    }

    public int step() { return step; }
    public void reset() { step = 0; direction=0; last = 0; cooldownUntil = 0; }
}
