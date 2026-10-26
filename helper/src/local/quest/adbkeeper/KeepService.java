package local.quest.adbkeeper;

import android.Manifest;
import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.app.Service;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.net.ConnectivityManager;
import android.net.NetworkInfo;
import android.os.Handler;
import android.os.IBinder;
import android.os.PowerManager;
import android.os.SystemClock;
import android.os.UserManager;
import android.provider.Settings;
import android.util.Log;

public final class KeepService extends Service {
    private final Handler handler = new Handler();
    private final Runnable check = new Runnable() {
        public void run() {
            if (!State.needed(KeepService.this)) { stopSelf(); return; }
            try {
                // USB recovery is independent of Wi-Fi, including during boot.
                if (State.usbEnabled(KeepService.this) && checkSelfPermission(Manifest.permission.WRITE_SECURE_SETTINGS) == PackageManager.PERMISSION_GRANTED) {
                    if (Settings.Global.getInt(getContentResolver(),"development_settings_enabled",0) != 1)
                        Settings.Global.putInt(getContentResolver(),"development_settings_enabled",1);
                    if (Settings.Global.getInt(getContentResolver(),"adb_enabled",0) != 1) {
                        Settings.Global.putInt(getContentResolver(),"adb_enabled",1);
                        Log.i("QuestAdbKeeper","Restored USB ADB");
                    }
                    if (Settings.Global.getLong(getContentResolver(),"adb_allowed_connection_time",-1) != 0)
                        Settings.Global.putLong(getContentResolver(),"adb_allowed_connection_time",0);
                }
                ConnectivityManager cm = (ConnectivityManager)getSystemService(CONNECTIVITY_SERVICE);
                NetworkInfo network = cm.getActiveNetworkInfo();
                if (State.enabled(KeepService.this) && checkSelfPermission(Manifest.permission.WRITE_SECURE_SETTINGS) == PackageManager.PERMISSION_GRANTED
                        && network != null && network.isConnected() && network.getType() == ConnectivityManager.TYPE_WIFI) {
                    if (Settings.Global.getInt(getContentResolver(),"adb_wifi_enabled",0) != 1) {
                        Settings.Global.putInt(getContentResolver(),"adb_wifi_enabled",1);
                        Log.i("QuestAdbKeeper","Restored wireless ADB while Wi-Fi is connected");
                    }
                    if (Settings.Global.getLong(getContentResolver(),"adb_allowed_connection_time",-1) != 0)
                        Settings.Global.putLong(getContentResolver(),"adb_allowed_connection_time",0);
                }
            } catch (SecurityException e) {
                Log.w("QuestAdbKeeper","ADB settings permission unavailable",e);
            }
            maybeStartCinema();
            handler.postDelayed(this,15000);
        }
    };
    private void maybeStartCinema() {
        if (!State.cinemaEnabled(this)) return;
        int boot = State.boot(this);
        if (State.prefs(this).getInt("cinema_boot",-1) == boot) return;
        if (SystemClock.elapsedRealtime() < 60000) return;
        UserManager users = (UserManager)getSystemService(USER_SERVICE);
        PowerManager power = (PowerManager)getSystemService(POWER_SERVICE);
        if (!users.isUserUnlocked() || !power.isInteractive() || !Settings.canDrawOverlays(this)) return;
        try {
            CinemaShortcutActivity.open(this);
            State.prefs(this).edit().putInt("cinema_boot",boot).commit();
            Log.i("QuestCinemaStartup","Opened Quest Cinema Fix once for boot "+boot);
        } catch (RuntimeException e) {
            Log.w("QuestCinemaStartup","Cinema launch unavailable; will retry",e);
        }
    }
    public void onCreate() {
        super.onCreate();
        NotificationManager nm = (NotificationManager)getSystemService(NOTIFICATION_SERVICE);
        nm.createNotificationChannel(new NotificationChannel("adb_keeper","Quest 启动助手",NotificationManager.IMPORTANCE_LOW));
        startForeground(1,notification());
    }
    private Notification notification() {
        PendingIntent open = PendingIntent.getActivity(this,0,new Intent(this,CinemaShortcutActivity.class),PendingIntent.FLAG_UPDATE_CURRENT|PendingIntent.FLAG_IMMUTABLE);
        PendingIntent settings = PendingIntent.getActivity(this,1,new Intent(this,MainActivity.class),PendingIntent.FLAG_UPDATE_CURRENT|PendingIntent.FLAG_IMMUTABLE);
        return new Notification.Builder(this,"adb_keeper")
            .setSmallIcon(android.R.drawable.stat_notify_sync)
            .setContentTitle("打开 Quest Cinema Fix")
            .setContentText("影院："+(State.cinemaEnabled(this)?"自启":"手动")+" · USB："+(State.usbEnabled(this)?"常驻":"关")+" · Wi-Fi："+(State.enabled(this)?"常驻":"关"))
            .setContentIntent(open)
            .addAction(new Notification.Action.Builder(android.R.drawable.ic_media_play,"打开影院",open).build())
            .addAction(new Notification.Action.Builder(android.R.drawable.ic_menu_preferences,"设置",settings).build())
            .setOngoing(true).build();
    }
    public int onStartCommand(Intent intent,int flags,int startId) {
        ((NotificationManager)getSystemService(NOTIFICATION_SERVICE)).notify(1,notification());
        handler.removeCallbacks(check);handler.post(check);return START_STICKY;
    }
    public void onDestroy() { handler.removeCallbacks(check);stopForeground(true);super.onDestroy(); }
    public IBinder onBind(Intent intent) { return null; }
}
