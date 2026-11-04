import local.quest.cinema.VolumeModeState;

public final class VolumeModeStateTest {
    static void eq(int actual,int expected) {
        if (actual != expected) throw new AssertionError(actual+" != "+expected);
    }
    static void check(boolean yes) { if (!yes) throw new AssertionError(); }
    public static void main(String[] ignored) {
        VolumeModeState s=new VolumeModeState();
        // Normal taps, long holds and a slow direction change retain the navigation path.
        eq(s.key(24,true,0,100,false),s.NAVIGATE);
        eq(s.key(24,true,1,700,false),s.NAVIGATE);
        eq(s.key(24,false,0,800,false),s.NAVIGATE);
        eq(s.key(25,true,0,900,false),s.NAVIGATE);
        eq(s.key(25,false,0,950,false),s.NAVIGATE);
        eq(s.key(24,true,0,1000,false),s.NAVIGATE);
        eq(s.key(25,true,0,1351,false),s.NAVIGATE);
        check(!s.volumeMode()); s.reset();
        // Both press orders work, and neither release is allowed to confirm/back.
        eq(s.key(25,true,0,2000,false),s.NAVIGATE);
        eq(s.key(24,true,0,2350,false),s.ENTER);
        eq(s.key(24,true,1,2500,false),s.CONSUMED);
        eq(s.key(25,false,0,2600,false),s.CONSUMED);
        eq(s.key(24,false,0,2700,false),s.CONSUMED);
        check(s.volumeMode());
        // Single presses change media volume; repeats are rate-limited and key-up never navigates.
        eq(s.key(25,true,0,3000,false),s.CONSUMED);
        eq(s.key(25,true,1,3100,false),s.CONSUMED);
        eq(s.key(25,true,2,3500,false),s.LOWER);
        eq(s.key(25,true,3,3600,false),s.CONSUMED);
        eq(s.key(25,true,4,3650,false),s.LOWER);
        eq(s.key(25,false,0,3700,false),s.CONSUMED);
        eq(s.key(24,true,0,4000,false),s.CONSUMED);
        eq(s.key(24,false,0,4050,false),s.RAISE);
        check(s.deadline()==10050); check(!s.expire(10049)); check(s.expire(10050));
        eq(s.key(24,true,0,10100,false),s.NAVIGATE);
        eq(s.key(24,false,0,10150,false),s.NAVIGATE);
        // Explicit exit suppresses all chord releases, including cancelled ones.
        eq(s.key(24,true,0,11000,false),s.NAVIGATE);
        eq(s.key(25,true,0,11100,false),s.ENTER);
        eq(s.key(24,false,0,11200,false),s.CONSUMED);
        eq(s.key(25,false,0,11300,false),s.CONSUMED);
        eq(s.key(24,true,0,12000,false),s.CONSUMED);
        eq(s.key(25,true,0,12100,false),s.EXIT);
        eq(s.key(25,false,0,12200,true),s.CONSUMED);
        eq(s.key(24,false,0,12300,false),s.CONSUMED);
        check(!s.volumeMode());
        // A held key cannot expire into navigation; pause/reset drops the mode and stale key state.
        s.key(24,true,0,14000,false); s.key(25,true,0,14100,false);
        s.key(24,false,0,14200,false); s.key(25,false,0,14300,false);
        eq(s.key(24,true,0,15000,false),s.CONSUMED);
        check(s.deadline()==0); check(!s.expire(30000));
        eq(s.key(24,false,0,30100,true),s.CONSUMED);
        eq(s.key(24,false,0,30200,false),s.CONSUMED);
        s.reset(); check(!s.volumeMode()); check(s.deadline()==0);
        eq(s.key(25,true,0,31000,false),s.NAVIGATE);
        eq(s.key(25,false,0,31100,false),s.NAVIGATE);
        System.out.println("PASS: navigation preserved, chord timing and release suppression, media-volume input, repeat throttle, idle exit and lifecycle reset");
    }
}
