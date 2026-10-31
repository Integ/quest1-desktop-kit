package local.quest.adbkeeper;

import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.provider.Settings;

final class State {
    static SharedPreferences prefs(Context c) {
        return c.createDeviceProtectedStorageContext().getSharedPreferences("keeper",0);
    }
    static boolean enabled(Context c) {
        return prefs(c).getBoolean("enabled",false);
    }
    static boolean cinemaEnabled(Context c) { return prefs(c).getBoolean("cinema_auto",false); }
    static boolean usbEnabled(Context c) { return prefs(c).getBoolean("usb_enabled",false); }
    static boolean launcherShortcutEnabled(Context c) { return prefs(c).getBoolean("launcher_shortcut",false); }
    static boolean idleLauncherEnabled(Context c) { return prefs(c).getBoolean("idle_launcher",true); }
    static boolean needed(Context c) { return enabled(c) || usbEnabled(c) || cinemaEnabled(c) || launcherShortcutEnabled(c) || idleLauncherEnabled(c); }
    static void setLauncherShortcutEnabled(Context c, boolean enabled) {
        prefs(c).edit().putBoolean("launcher_shortcut",enabled).commit();
        updateService(c);
    }
    static void setIdleLauncherEnabled(Context c, boolean enabled) {
        prefs(c).edit().putBoolean("idle_launcher",enabled).commit();
        updateService(c);
    }
    static int boot(Context c) { return Settings.Global.getInt(c.getContentResolver(),Settings.Global.BOOT_COUNT,0); }
    static void setCinemaEnabled(Context c, boolean enabled) {
        prefs(c).edit().putBoolean("cinema_auto",enabled).putInt("cinema_boot",boot(c)).commit();
        updateService(c);
    }
    static void setUsbEnabled(Context c, boolean enabled) {
        if (c.checkSelfPermission("android.permission.WRITE_SECURE_SETTINGS") != android.content.pm.PackageManager.PERMISSION_GRANTED)
            throw new SecurityException("System settings permission is required");
        prefs(c).edit().putBoolean("usb_enabled",enabled).commit();
        updateService(c);
        if (!enabled) Settings.Global.putInt(c.getContentResolver(),"adb_enabled",0);
    }
    static void updateService(Context c) {
        Intent i = new Intent(c,KeepService.class);
        if (needed(c)) c.startForegroundService(i); else c.stopService(i);
    }
    static void setEnabled(Context c, boolean enabled) {
        if (c.checkSelfPermission("android.permission.WRITE_SECURE_SETTINGS") != android.content.pm.PackageManager.PERMISSION_GRANTED)
            throw new SecurityException("System settings permission is required");
        prefs(c).edit().putBoolean("enabled",enabled).commit();
        updateService(c);
        if (!enabled) {
            Settings.Global.putInt(c.getContentResolver(),"adb_wifi_enabled",0);
        }
    }
}
