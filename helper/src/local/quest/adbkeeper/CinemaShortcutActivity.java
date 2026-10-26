package local.quest.adbkeeper;

import android.app.Activity;
import android.content.ComponentName;
import android.content.Context;
import android.content.Intent;
import android.os.Bundle;

/** A visible launcher entry and notification target, always initiated by the user. */
public final class CinemaShortcutActivity extends Activity {
    static Intent cinemaIntent() {
        return new Intent(Intent.ACTION_MAIN)
            .addCategory(Intent.CATEGORY_LAUNCHER)
            .setComponent(new ComponentName("local.quest.cinema","com.oculus.cinemasdk.MainActivity"))
            .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK|Intent.FLAG_ACTIVITY_REORDER_TO_FRONT);
    }
    static void open(Context c) { c.startActivity(cinemaIntent()); }
    public void onCreate(Bundle state) {
        super.onCreate(state);
        try { open(this); } finally { finish(); }
    }
}
