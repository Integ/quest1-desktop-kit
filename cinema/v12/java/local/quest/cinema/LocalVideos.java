package local.quest.cinema;

import android.content.Context;
import android.content.SharedPreferences;
import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.graphics.Rect;
import android.graphics.SurfaceTexture;
import android.media.AudioManager;
import android.media.MediaMetadataRetriever;
import android.media.MediaPlayer;
import android.os.Environment;
import android.os.Handler;
import android.os.Looper;
import android.text.Layout;
import android.text.StaticLayout;
import android.text.TextPaint;
import android.text.TextUtils;
import android.util.Log;
import android.view.KeyEvent;
import android.view.Surface;
import com.oculus.cinemasdk.MainActivity;
import java.io.File;
import java.io.FileOutputStream;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/**
 * Plays video files from the headset in the cinema. The native UI keeps one app list shared by every
 * computer and reads it only once when the list opens, so local videos stay in that list and are kept in
 * sync from the render thread; playback is routed by app id, not by computer. Real computers still stream.
 */
public final class LocalVideos {
    public static final String UUID = "00000000-0000-4000-8000-0000000f11e5";
    static final String TAG = "QuestLocalVideo";
    static final int SEEK_MS = 10000, POSTER_W = 456, POSTER_H = 688;
    private static final Handler main = new Handler(Looper.getMainLooper());
    private static final ExecutorService posters = Executors.newSingleThreadExecutor();
    private static final Map<Integer, LocalVideoCatalog.Entry> entries = new HashMap<Integer, LocalVideoCatalog.Entry>();
    private static final Set<Integer> listed = new HashSet<Integer>(), pending = new HashSet<Integer>();
    private static final Set<String> warmed = new HashSet<String>();
    private static MainActivity owner;
    private static Thread renderThread;
    private static String lastRemoteUuid;
    private static MediaPlayer player;
    private static Surface surface;
    private static String currentPath;
    private static volatile boolean active, prepared, finished, failed, pausedByLifecycle;

    public static boolean isLocal(String uuid) { return UUID.equals(uuid); }

    static File[] folders() {
        return new File[] {
            Environment.getExternalStoragePublicDirectory(Environment.DIRECTORY_MOVIES),
            Environment.getExternalStoragePublicDirectory(Environment.DIRECTORY_DOWNLOADS),
        };
    }

    /** Called from initPcSelector on the render thread. */
    public static void addLocalPc(final MainActivity activity) {
        owner = activity;
        renderThread = Thread.currentThread();
        main.post(new Runnable() { public void run() {
            MainActivity.nativeAddPc(activity.getAppPtr(), "Local Videos", UUID, 1, 0, "local", false);
        }});
        sync();
    }

    /**
     * Replaces PcSelector's nativeAddPc call. The native list is read only when it opens, so a paired
     * computer's cached apps are loaded right away; otherwise the first visit after launch shows none.
     */
    public static void addRemotePc(long app, String name, String uuid, int pairState, int reachability, String binding, boolean running) {
        MainActivity.nativeAddPc(app, name, uuid, pairState, reachability, binding, running);
        MainActivity a = owner;
        if (a != null && pairState == 1 && warmed.add(uuid)) a.initAppSelector(uuid);
    }

    /**
     * Rescans the folders and updates the native list. Only on the render thread, where the native list
     * lives and posters can be uploaded as GL textures. Missing posters are drawn in the background and
     * show up on the next sync (every time a list opens).
     */
    static void sync() {
        final MainActivity a = owner;
        if (a == null || Thread.currentThread() != renderThread) return;
        List<LocalVideoCatalog.Entry> found = LocalVideoCatalog.scan(folders());
        Map<Integer, LocalVideoCatalog.Entry> now = new HashMap<Integer, LocalVideoCatalog.Entry>();
        for (LocalVideoCatalog.Entry e : found) now.put(e.id, e);
        synchronized (entries) {
            for (Integer id : new HashSet<Integer>(listed)) {
                if (!now.containsKey(id)) { MainActivity.nativeRemoveApp(a.getAppPtr(), id); listed.remove(id); }
            }
            entries.clear();
            entries.putAll(now);
        }
        int waiting = 0;
        for (final LocalVideoCatalog.Entry e : found) {
            final File poster = posterFile(a, e.id);
            if (poster.isFile()) {
                if (listed.add(e.id)) MainActivity.nativeAddApp(a.getAppPtr(), e.title, poster.getAbsolutePath(), e.id, false);
            } else {
                boolean queue;
                synchronized (entries) { queue = pending.add(e.id); }
                if (queue) posters.execute(new Runnable() { public void run() { drawPoster(e, poster); } });
                waiting++;
            }
        }
        Log.i(TAG, "Sync: " + found.size() + " videos, " + listed.size() + " listed, " + waiting + " posters pending");
    }

    static File posterFile(Context c, int id) { return new File(c.getFilesDir(), "localposters/" + id + ".png"); }

    static LocalVideoCatalog.Entry entry(int id) {
        synchronized (entries) { return entries.get(id); }
    }

    private static Bitmap frame(MediaMetadataRetriever r, long[] durationMs) {
        String d = r.extractMetadata(MediaMetadataRetriever.METADATA_KEY_DURATION);
        durationMs[0] = d == null ? 0 : Long.parseLong(d);
        return r.getFrameAtTime(Math.min(10000000L, durationMs[0] * 100), MediaMetadataRetriever.OPTION_CLOSEST_SYNC);
    }

    /** Portrait card: a frame of the video, then the full file name (any language) and the duration. */
    static void drawPoster(LocalVideoCatalog.Entry e, File out) {
        MediaMetadataRetriever r = new MediaMetadataRetriever();
        try {
            r.setDataSource(e.file.getAbsolutePath());
            long[] duration = new long[1];
            Bitmap frame = frame(r, duration);
            Bitmap card = Bitmap.createBitmap(POSTER_W, POSTER_H, Bitmap.Config.ARGB_8888);
            Canvas canvas = new Canvas(card);
            canvas.drawColor(Color.rgb(18, 20, 26));
            int top = 96;
            if (frame != null) {
                int h = Math.min(POSTER_H / 2, Math.round(POSTER_W * frame.getHeight() / (float) frame.getWidth()));
                canvas.drawBitmap(frame, null, new Rect(0, top, POSTER_W, top + h), new Paint(Paint.FILTER_BITMAP_FLAG));
                top += h;
            }
            TextPaint text = new TextPaint(Paint.ANTI_ALIAS_FLAG);
            text.setColor(Color.WHITE);
            text.setTextSize(34);
            String name = e.file.getName();
            int dot = name.lastIndexOf('.');
            StaticLayout title = StaticLayout.Builder.obtain(dot > 0 ? name.substring(0, dot) : name, 0,
                    dot > 0 ? dot : name.length(), text, POSTER_W - 48)
                .setMaxLines(4).setEllipsize(TextUtils.TruncateAt.END).setAlignment(Layout.Alignment.ALIGN_NORMAL).build();
            canvas.save();
            canvas.translate(24, top + 28);
            title.draw(canvas);
            canvas.restore();
            text.setTextSize(28);
            text.setColor(Color.rgb(170, 176, 186));
            canvas.drawText(LocalVideoCatalog.duration(duration[0]), 24, POSTER_H - 32, text);
            canvas.drawText("Local Video", 24, 60, text);
            out.getParentFile().mkdirs();
            File tmp = new File(out.getPath() + ".tmp");
            FileOutputStream stream = new FileOutputStream(tmp);
            try { card.compress(Bitmap.CompressFormat.PNG, 100, stream); } finally { stream.close(); }
            if (!tmp.renameTo(out)) tmp.delete();
        } catch (Exception ex) {
            Log.w(TAG, "Poster failed for " + e.file, ex);
        } finally {
            try { r.release(); } catch (Exception ignored) { }
            synchronized (entries) { pending.remove(e.id); }
        }
    }

    /** Local Videos opens the shared list (already synced); real computers run the original selector. */
    public static boolean initApps(MainActivity activity, String uuid) {
        if (!isLocal(uuid)) { lastRemoteUuid = uuid; return false; }
        sync();
        return true;
    }

    public static boolean ownsApp(String uuid, int appId) { return isLocal(uuid) || entry(appId) != null; }

    /** -1: not a local video; 0: failed; 1: thumbnail written. */
    public static int thumbnail(MainActivity activity, String uuid, int appId, String output, int width, int height) {
        LocalVideoCatalog.Entry e = entry(appId);
        if (e == null) return isLocal(uuid) ? 0 : -1;
        if (width <= 0 || height <= 0) return 0;
        MediaMetadataRetriever r = new MediaMetadataRetriever();
        try {
            r.setDataSource(e.file.getAbsolutePath());
            Bitmap frame = frame(r, new long[1]);
            if (frame == null) return 0;
            float want = width / (float) height, have = frame.getWidth() / (float) frame.getHeight();
            int cw = frame.getWidth(), ch = frame.getHeight();
            if (have > want) cw = Math.round(ch * want); else ch = Math.round(cw / want);
            Bitmap cropped = Bitmap.createBitmap(frame, (frame.getWidth() - cw) / 2, (frame.getHeight() - ch) / 2, cw, ch);
            File out = new File(output);
            out.getParentFile().mkdirs();
            FileOutputStream stream = new FileOutputStream(out);
            try { Bitmap.createScaledBitmap(cropped, width, height, true).compress(Bitmap.CompressFormat.PNG, 100, stream); }
            finally { stream.close(); }
            return 1;
        } catch (Exception ex) {
            Log.w(TAG, "Thumbnail failed for " + e.file, ex);
            return 0;
        } finally {
            try { r.release(); } catch (Exception ignored) { }
        }
    }

    /**
     * Returns null when handled here, otherwise the computer to stream from: a Mac app picked from the
     * Local Videos entry streams from the last real computer that listed its apps.
     */
    public static String start(final MainActivity activity, String uuid, int appId) {
        final LocalVideoCatalog.Entry e = entry(appId);
        if (e == null) {
            if (!isLocal(uuid)) return uuid;
            if (lastRemoteUuid != null) return lastRemoteUuid;
            active = true; prepared = false; failed = true; finished = true;
            return null;
        }
        active = true; prepared = false; finished = false; failed = false; pausedByLifecycle = false;
        main.post(new Runnable() { public void run() { open(activity, e.file); } });
        return null;
    }

    private static void open(final MainActivity activity, File file) {
        release(false);
        currentPath = file.getAbsolutePath();
        try {
            SurfaceTexture texture = MainActivity.nativePrepareNewVideo(activity.getAppPtr());
            surface = new Surface(texture);
            final MediaPlayer mp = new MediaPlayer();
            player = mp;
            mp.setAudioStreamType(AudioManager.STREAM_MUSIC);
            mp.setSurface(surface);
            mp.setDataSource(currentPath);
            mp.setOnPreparedListener(new MediaPlayer.OnPreparedListener() { public void onPrepared(MediaPlayer p) {
                if (p != player) return;
                int duration = p.getDuration();
                prepared = true;
                MainActivity.nativeSetVideoSize(activity.getAppPtr(), p.getVideoWidth(), p.getVideoHeight(), 0, duration);
                int at = LocalVideoCatalog.startPosition(positions().getInt(currentPath, 0), duration);
                if (at > 0) p.seekTo(at);
                audio().requestAudioFocus(null, AudioManager.STREAM_MUSIC, AudioManager.AUDIOFOCUS_GAIN);
                p.start();
                Log.i(TAG, "Playing " + currentPath + " from " + at + " ms");
                main.postDelayed(savePosition, 5000);
            }});
            mp.setOnVideoSizeChangedListener(new MediaPlayer.OnVideoSizeChangedListener() {
                public void onVideoSizeChanged(MediaPlayer p, int w, int h) {
                    // getDuration() is only legal once prepared; calling it earlier makes MediaPlayer report error -38.
                    if (p == player && prepared && w > 0 && h > 0)
                        MainActivity.nativeSetVideoSize(activity.getAppPtr(), w, h, 0, p.getDuration());
                }});
            mp.setOnCompletionListener(new MediaPlayer.OnCompletionListener() { public void onCompletion(MediaPlayer p) {
                if (p != player) return;
                positions().edit().remove(currentPath).apply();
                finished = true;
            }});
            mp.setOnErrorListener(new MediaPlayer.OnErrorListener() { public boolean onError(MediaPlayer p, int what, int extra) {
                Log.e(TAG, "Playback error " + what + "/" + extra + " for " + currentPath);
                if (p == player && what != -38) { failed = true; finished = true; }
                return true;
            }});
            mp.prepareAsync();
        } catch (Exception ex) {
            Log.e(TAG, "Cannot open " + currentPath, ex);
            failed = true; finished = true;
        }
    }

    private static final Runnable savePosition = new Runnable() { public void run() {
        MediaPlayer p = player;
        if (p == null || !prepared) return;
        try { if (p.isPlaying()) positions().edit().putInt(currentPath, p.getCurrentPosition()).apply(); }
        catch (IllegalStateException ignored) { }
        main.postDelayed(this, 5000);
    }};

    private static SharedPreferences positions() {
        return owner.getSharedPreferences("local_video_positions", Context.MODE_PRIVATE);
    }

    private static AudioManager audio() {
        return (AudioManager) owner.getSystemService(Context.AUDIO_SERVICE);
    }

    /** Releases the player; called on the main thread. */
    private static void release(boolean keepPosition) {
        main.removeCallbacks(savePosition);
        MediaPlayer p = player;
        player = null;
        if (p != null) {
            try { if (keepPosition && prepared && !finished) positions().edit().putInt(currentPath, p.getCurrentPosition()).apply(); }
            catch (IllegalStateException ignored) { }
            p.release();
            audio().abandonAudioFocus(null);
        }
        if (surface != null) { surface.release(); surface = null; }
        prepared = false;
    }

    /** Called from stopMovie, which the native UI also calls right before any list opens. */
    public static void stop(MainActivity activity) {
        if (active) {
            active = false;
            main.post(new Runnable() { public void run() { if (!active) release(true); } });
        }
        sync();
    }

    public static int playingState() { return active ? (prepared && !finished ? 1 : 0) : -1; }
    public static int finishedState() { return active ? (finished ? 1 : 0) : -1; }
    public static int errorState() { return active ? (failed ? 1 : 0) : -1; }
    public static boolean isActive() { return active; }

    /** Gamepad: Menu (≡) or media play/pause toggles, LB/RB seek 10 s. */
    public static boolean onKey(KeyEvent event) {
        final MediaPlayer p = player;
        if (!active || p == null || !prepared) return false;
        int code = event.getKeyCode();
        int delta = code == KeyEvent.KEYCODE_BUTTON_L1 || code == KeyEvent.KEYCODE_MEDIA_REWIND ? -SEEK_MS
                  : code == KeyEvent.KEYCODE_BUTTON_R1 || code == KeyEvent.KEYCODE_MEDIA_FAST_FORWARD ? SEEK_MS : 0;
        boolean toggle = code == KeyEvent.KEYCODE_BUTTON_START || code == KeyEvent.KEYCODE_MEDIA_PLAY_PAUSE;
        if (delta == 0 && !toggle) return false;
        if (event.getAction() == KeyEvent.ACTION_DOWN && event.getRepeatCount() == 0) {
            try {
                if (toggle) { if (p.isPlaying()) p.pause(); else p.start(); }
                else p.seekTo(LocalVideoCatalog.seek(p.getCurrentPosition(), delta, p.getDuration()));
            } catch (IllegalStateException ignored) { }
        }
        return true;
    }

    public static void onPause() {
        MediaPlayer p = player;
        if (!active || p == null || !prepared) return;
        try {
            if (p.isPlaying()) {
                p.pause();
                pausedByLifecycle = true;
                positions().edit().putInt(currentPath, p.getCurrentPosition()).apply();
            }
        } catch (IllegalStateException ignored) { }
    }

    public static void onResume() {
        MediaPlayer p = player;
        if (!pausedByLifecycle || p == null) return;
        pausedByLifecycle = false;
        try { p.start(); } catch (IllegalStateException ignored) { }
    }
}
