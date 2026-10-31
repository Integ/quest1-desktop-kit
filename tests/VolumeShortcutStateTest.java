import java.util.Arrays;
import local.quest.cinema.VolumeKeyState;
import local.quest.cinema.VolumeShortcutState;

public final class VolumeShortcutStateTest {
    static void eq(int[] actual,int... expected) {
        if (!Arrays.equals(actual,expected))
            throw new AssertionError(Arrays.toString(actual)+" != "+Arrays.toString(expected));
    }
    static void check(boolean yes) { if (!yes) throw new AssertionError(); }
    public static void main(String[] ignored) {
        int back=VolumeKeyState.BACK, ok=VolumeKeyState.CONFIRM;
        VolumeShortcutState s=new VolumeShortcutState();
        eq(s.accept(ok,100),ok); check(!s.pending());
        eq(s.accept(back,200)); eq(s.expire(899)); eq(s.expire(900),back);
        check(!s.pending()); eq(s.expire(1000));
        eq(s.accept(back,1100)); eq(s.accept(ok,1300));
        eq(s.accept(back,1500)); eq(s.accept(ok,1700),VolumeShortcutState.OPEN_APP_LIST);
        check(!s.pending()); eq(s.expire(9999));
        // Interrupted patterns preserve ordinary taps exactly once and in order.
        eq(s.accept(back,2000)); eq(s.accept(ok,2200));
        eq(s.accept(ok,2300),back,ok,ok); check(!s.pending());
        eq(s.accept(back,3000)); eq(s.accept(back,3100),back);
        eq(s.expire(3800),back);
        // A hold cannot complete the shortcut and keeps the single-step mapping.
        eq(s.accept(back,4000)); eq(s.accept(VolumeKeyState.RIGHT,4300),back,VolumeKeyState.RIGHT);
        check(!s.pending());
        // Deadline is strict; slow presses cannot accidentally launch the list.
        eq(s.accept(back,5000)); eq(s.accept(ok,5700),back,ok);
        eq(s.accept(back,6000)); s.cancel(); eq(s.expire(9000));
        // Pending input is discarded on pause/cancellation.
        eq(s.accept(back,10000)); eq(s.accept(ok,10100));
        s.cancel(); eq(s.accept(ok,10200),ok);
        // A backwards clock flushes safely rather than retaining a stale prefix.
        eq(s.accept(back,11000)); eq(s.expire(10000),back);
        System.out.println("PASS: shortcut suppression, tap fallback, timing boundary, holds, mismatches, cancellation and repeated use");
    }
}
