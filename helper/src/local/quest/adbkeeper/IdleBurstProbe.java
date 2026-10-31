package local.quest.adbkeeper;

/** Public wrapper so the host-side test can exercise the package-private burst logic. */
public final class IdleBurstProbe {
    private final IdleBurst burst=new IdleBurst();
    public boolean hit(long now) { return burst.hit(now); }
}
