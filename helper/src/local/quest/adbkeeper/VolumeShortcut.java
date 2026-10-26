package local.quest.adbkeeper;

/** Recognizes down/up/down/up without reading controller or keyboard input. */
public final class VolumeShortcut {
    private int step;
    private long last;
    private long cooldownUntil;

    public boolean accept(int previous, int current, long now) {
        if (previous < 0 || current < 0 || current == previous) return false;
        if (now < cooldownUntil) return false;
        int delta = current - previous;
        if (Math.abs(delta) != 1) { step = 0; return false; }
        if (step > 0 && (now < last || now - last > 1500)) step = 0;
        int wanted = step % 2 == 0 ? -1 : 1;
        step = delta == wanted ? step + 1 : (delta == -1 ? 1 : 0);
        last = now;
        if (step == 4) {
            step = 0;
            cooldownUntil = now + 2000;
            return true;
        }
        return false;
    }

    public void reset() { step = 0; last = 0; cooldownUntil = 0; }
}
