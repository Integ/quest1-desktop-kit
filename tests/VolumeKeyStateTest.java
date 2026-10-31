import local.quest.cinema.VolumeKeyState;
public final class VolumeKeyStateTest {
    static void check(boolean value) { if (!value) throw new AssertionError(); }
    public static void main(String[] ignored) {
        VolumeKeyState s=new VolumeKeyState();
        check(s.press(24,100)); check(s.hold(200)==0);
        check(s.release(24,230)==VolumeKeyState.CONFIRM); check(s.release(24,240)==0);
        check(s.press(25,1000)); check(s.release(25,1100)==VolumeKeyState.BACK);
        check(s.press(24,2000)); check(!s.press(24,2100));
        check(s.hold(2549)==0); check(s.hold(2550)==VolumeKeyState.RIGHT);
        check(s.hold(3000)==0); check(s.release(24,3100)==0);
        check(s.press(25,4000)); check(s.hold(4550)==VolumeKeyState.LEFT);
        check(s.release(25,4600)==0);
        check(s.press(24,5000)); check(s.release(24,5550)==VolumeKeyState.RIGHT);
        check(s.press(24,6000)); check(s.press(25,6100));
        check(s.release(24,6200)==0); check(s.hold(6650)==VolumeKeyState.LEFT);
        s.cancel(); check(s.hold(9000)==0); check(s.release(25,9100)==0);
        check(s.press(24,10000)); s.cancel(); check(s.release(24,10001)==0);
        check(!s.press(42,0)); check(s.activeCode()==0);
        check(s.press(24,100)); check(s.release(24,99)==0);
        System.out.println("PASS: tap/hold boundary, one action per hold, no confirm/back after holds, repeats, overlap, cancellation and stale releases");
    }
}
