package local.quest.cinema;

/** Detects two nearby short taps; never consumes the first tap or a drag. */
public final class LeftTapGesture {
    private long lastUp = -1;
    private long downTime;
    private float lastX, lastY, downX, downY;
    private boolean active, dragged, consuming;
    private static boolean near(float x, float y, float a, float b) {
        float dx = x - a, dy = y - b;
        return dx * dx + dy * dy <= 64 * 64;
    }
    public boolean down(long time, float x, float y) {
        consuming = lastUp >= 0 && time - lastUp >= 0 && time - lastUp <= 350 && near(x,y,lastX,lastY);
        lastUp = -1;
        downTime = time; downX = x; downY = y; active = true; dragged = false;
        return consuming;
    }
    public void move(float x, float y) { if (active && !near(x,y,downX,downY)) dragged = true; }
    public boolean consuming() { return consuming; }
    public boolean up(long time, float x, float y) {
        boolean tap = active && !dragged && time - downTime >= 0 && time - downTime <= 350 && near(x,y,downX,downY);
        boolean menu = consuming && tap;
        if (tap && !consuming) { lastUp = time; lastX = x; lastY = y; }
        else lastUp = -1;
        active = false; dragged = false; consuming = false;
        return menu;
    }
    public void reset() { lastUp = -1; active = false; dragged = false; consuming = false; }
}
