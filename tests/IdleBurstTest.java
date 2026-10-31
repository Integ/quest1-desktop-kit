package local.quest.adbkeeper;

/** Host regression for the empty-VR-Home detector; same package to reach the package-private class. */
public final class IdleBurstTest {
    static void check(boolean ok, String what) { if (!ok) throw new AssertionError(what); }
    public static void main(String[] args) {
        IdleBurst b = new IdleBurst();
        for (int i = 0; i < 4; i++) check(!b.hit(1000 + i * 100), "fewer than five hits stays quiet");
        check(b.hit(1400), "five hits within two seconds fires");
        for (int i = 0; i < 10; i++) check(!b.hit(1500 + i * 100), "cooldown suppresses repeats");
        IdleBurst slow = new IdleBurst();
        for (int i = 0; i < 10; i++) check(!slow.hit(i * 1000L), "one hit per second never fires");
        IdleBurst again = new IdleBurst();
        for (int i = 0; i < 5; i++) again.hit(i * 10);
        boolean fired = false;
        for (int i = 0; i < 5; i++) fired |= again.hit(21000 + i * 10);
        check(fired, "fires again after the cooldown");
        System.out.println("IdleBurstTest passed");
    }
}
