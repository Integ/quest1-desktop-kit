import local.quest.cinema.LeftTapGesture;

public class LeftTapGestureTest {
    public static void main(String[] args) {
        LeftTapGesture g = new LeftTapGesture();
        check(!g.down(0,160,160), "first tap reaches UI");
        check(!g.up(50,160,160), "single tap keeps normal action");
        check(g.down(160,160,160), "second tap consumed");
        check(g.up(210,160,160), "double tap opens menu once");
        check(!g.down(240,160,160), "triple tap cannot toggle twice");
        g.move(500,500);check(!g.up(270,500,500), "drag is not a tap");
        check(!g.down(300,500,500), "drag cannot start a double tap");
        check(!g.up(900,500,500), "held drag is not a tap");
        check(!g.down(1000,160,160), "new single tap");g.up(1050,160,160);
        check(!g.down(1100,600,600), "different targets do not toggle menu");
        g.reset();check(!g.consuming(), "pause cancels gesture");
        System.out.println("PASS: single/double/triple taps, drag, hold, target separation and reset");
    }
    static void check(boolean ok,String reason) { if(!ok)throw new AssertionError(reason); }
}
