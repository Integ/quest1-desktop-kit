package local.quest.cinema;

import java.util.ArrayList;

/** Buffers a possible down/up/down/up shortcut so it cannot also select or exit. */
public final class VolumeShortcutState {
    public static final int OPEN_APP_LIST=5;
    public static final long GAP_MS=700;
    private final int[] pending=new int[3];
    private int size;
    private long last;

    public boolean pending() { return size != 0; }
    public long deadline() { return last+GAP_MS; }
    public void cancel() { size=0; last=0; }
    private void flush(ArrayList<Integer> out) {
        for (int i=0;i<size;i++) out.add(pending[i]);
        cancel();
    }
    private static int[] result(ArrayList<Integer> out) {
        int[] values=new int[out.size()];
        for (int i=0;i<values.length;i++) values[i]=out.get(i);
        return values;
    }
    public int[] expire(long now) {
        ArrayList<Integer> out=new ArrayList<Integer>();
        if (size != 0 && (now < last || now >= deadline())) flush(out);
        return result(out);
    }
    public int[] accept(int action,long now) {
        ArrayList<Integer> out=new ArrayList<Integer>();
        if (size != 0 && (now < last || now >= deadline())) flush(out);
        if (action == VolumeKeyState.NONE) return result(out);
        if (action != VolumeKeyState.CONFIRM && action != VolumeKeyState.BACK) {
            flush(out); out.add(action); return result(out);
        }
        int expected=size%2 == 0 ? VolumeKeyState.BACK : VolumeKeyState.CONFIRM;
        if (action != expected) flush(out);
        if (size == 0 && action != VolumeKeyState.BACK) out.add(action);
        else if (size == 3) { cancel(); out.add(OPEN_APP_LIST); }
        else { pending[size++]=action; last=now; }
        return result(out);
    }
}
