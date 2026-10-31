import local.quest.adbkeeper.VolumeMonitor;

public final class VolumeMonitorTest {
    static void check(boolean yes,String why) { if (!yes) throw new AssertionError(why); }
    public static void main(String[] ignored) {
        VolumeMonitor s=new VolumeMonitor();
        check(!s.sample(12,0),"baseline");
        check(!s.sample(11,100),"first down"); check(!s.sample(11,150),"duplicate source");
        check(!s.sample(12,500),"up"); check(!s.sample(11,900),"down");
        check(s.sample(12,1300),"polling-only shortcut");
        check(!s.sample(11,1400),"cooldown"); check(!s.sample(12,1500),"cooldown");
        s.reset(); check(!s.sample(12,5000),"new baseline");
        check(!s.sample(11,5100),"held down first step");
        check(!s.sample(10,5500),"held down repeat does not reset progress");
        check(!s.sample(9,5900),"held down repeat");
        check(!s.sample(10,6500),"held up first step");
        check(!s.sample(11,6900),"held up repeat ignored");
        check(!s.sample(10,7500),"held down third direction");
        check(!s.sample(9,7900),"held down repeat ignored");
        check(s.sample(10,8500),"four held directions launch once");
        check(!s.sample(11,8900),"continued final hold does not launch again");
        s.reset(); check(!s.sample(10,10000),"baseline");
        check(!s.sample(8,10100),"quantized down by two");
        check(!s.sample(10,10500),"quantized up by two");
        check(!s.sample(8,10900),"down by two");
        check(s.sample(10,11300),"quantized sequence");
        s.reset(); check(!s.sample(12,14000),"baseline");
        check(!s.sample(2,14100),"large software jump resets");
        check(!s.sample(3,14200),"up alone"); check(!s.sample(2,14300),"first down");
        check(!s.sample(3,14400),"second direction only");
        check(!s.sample(2,17000),"timeout restarts");
        check(!s.sample(3,17100),"second"); check(!s.sample(2,17200),"third");
        check(s.sample(3,17300),"timeout recovery");
        s.reset(); check(!s.sample(0,20000),"mute baseline");
        check(!s.sample(0,20100),"no imaginary down at mute");
        check(!s.sample(1,20200),"up does not start");
        check(!s.sample(-1,20300),"invalid read"); check(s.previous()==-1,"invalid read resets baseline");
        System.out.println("PASS: polling without broadcasts, duplicate sources, held-direction grouping, quantization, cooldown, timeouts, volume bounds and software jumps");
    }
}
