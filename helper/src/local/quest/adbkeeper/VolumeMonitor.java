package local.quest.adbkeeper;

/** Shares a baseline between broadcasts and polling, without observing input keys. */
public final class VolumeMonitor {
    private final VolumeShortcut shortcut=new VolumeShortcut();
    private int previous=-1;
    public int previous() { return previous; }
    public int step() { return shortcut.step(); }
    public void reset() { previous=-1; shortcut.reset(); }
    public boolean sample(int volume,long now) {
        if (volume < 0) { reset(); return false; }
        int old=previous;
        previous=volume;
        return shortcut.accept(old,volume,now);
    }
}
