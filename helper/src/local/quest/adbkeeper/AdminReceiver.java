package local.quest.adbkeeper;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;

/** Protected by WRITE_SECURE_SETTINGS: only the shell/system/admin can send it. */
public final class AdminReceiver extends BroadcastReceiver {
    public void onReceive(Context context,Intent intent) {
        if ("local.quest.adbkeeper.STATUS".equals(intent.getAction())) {
            setResultData("version=10;launcher="+State.launcherShortcutEnabled(context)
                +";idle="+State.idleLauncherEnabled(context)+";idle_permitted="+HomeIdleWatcher.permitted(context)
                +";cinema="+State.cinemaEnabled(context)+";usb="+State.usbEnabled(context)+";wifi="+State.enabled(context)
                +";shortcut="+State.launcherShortcutEnabled(context)
                +";"+KeepService.shortcutStatus()
                +";opens="+AppListShortcut.opens+";result="+AppListShortcut.result);
            return;
        }
        if ("local.quest.adbkeeper.ENABLE".equals(intent.getAction())) State.setEnabled(context,true);
        else if ("local.quest.adbkeeper.DISABLE".equals(intent.getAction())) State.setEnabled(context,false);
        else if ("local.quest.adbkeeper.CINEMA_ENABLE".equals(intent.getAction())) State.setCinemaEnabled(context,true);
        else if ("local.quest.adbkeeper.CINEMA_DISABLE".equals(intent.getAction())) State.setCinemaEnabled(context,false);
        else if ("local.quest.adbkeeper.USB_ENABLE".equals(intent.getAction())) State.setUsbEnabled(context,true);
        else if ("local.quest.adbkeeper.USB_DISABLE".equals(intent.getAction())) State.setUsbEnabled(context,false);
        else if ("local.quest.adbkeeper.LAUNCHER_ENABLE".equals(intent.getAction())) State.setLauncherShortcutEnabled(context,true);
        else if ("local.quest.adbkeeper.LAUNCHER_DISABLE".equals(intent.getAction())) State.setLauncherShortcutEnabled(context,false);
        else if ("local.quest.adbkeeper.IDLE_ENABLE".equals(intent.getAction())) State.setIdleLauncherEnabled(context,true);
        else if ("local.quest.adbkeeper.IDLE_DISABLE".equals(intent.getAction())) State.setIdleLauncherEnabled(context,false);
    }
}
