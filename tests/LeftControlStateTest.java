import local.quest.cinema.LeftControlState;

public final class LeftControlStateTest {
    public static void main(String[] args) {
        LeftControlState s = new LeftControlState();
        check(!s.down(), "neutral");
        s.analog(0.60f); check(s.down(), "analog press");
        s.analog(0.45f); check(s.down(), "threshold jitter must not release");
        s.digital(true); s.analog(0); check(s.down(), "digital report holds after analog release");
        s.digital(false); check(!s.down(), "combined reports release");
        s.digital(true); s.analog(1); s.reset(); check(!s.down(), "pause releases every source");
        s.analog(Float.NaN); check(!s.down(), "invalid axis is neutral");
        System.out.println("PASS: trigger hysteresis, mixed reports, release and pause reset");
    }
    private static void check(boolean ok, String message) {
        if (!ok) throw new AssertionError(message);
    }
}
