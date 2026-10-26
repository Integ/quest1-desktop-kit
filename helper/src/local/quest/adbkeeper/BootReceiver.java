package local.quest.adbkeeper;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;

public final class BootReceiver extends BroadcastReceiver {
    public void onReceive(Context context, Intent intent) {
        String action = intent.getAction();
        if ((Intent.ACTION_BOOT_COMPLETED.equals(action)||Intent.ACTION_LOCKED_BOOT_COMPLETED.equals(action)) && State.needed(context))
            context.startForegroundService(new Intent(context,KeepService.class));
    }
}
