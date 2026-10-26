package local.quest.cinema;

/** Combines digital and analog trigger reports without duplicate/stuck presses. */
public final class LeftControlState {
    private boolean digital;
    private boolean analog;

    public void digital(boolean down) { digital = down; }
    public void analog(float value) {
        if (Float.isNaN(value) || value <= 0.35f) analog = false;
        else if (value >= 0.55f) analog = true;
    }
    public boolean down() { return digital || analog; }
    public void reset() { digital = false; analog = false; }
}
