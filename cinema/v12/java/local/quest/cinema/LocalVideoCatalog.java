package local.quest.cinema;

import java.io.File;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.List;
import java.util.Locale;

/** Plain-Java rules for the "Local Videos" entry; no Android APIs so they can be tested on the Mac. */
public final class LocalVideoCatalog {
    public static final String[] EXTENSIONS = {".mp4", ".m4v", ".mkv", ".webm", ".mov", ".3gp", ".ts"};
    static final long RESUME_MIN_MS = 30000, RESUME_TAIL_MS = 30000;

    public static final class Entry {
        public final File file;
        public final int id;
        public final String title;
        Entry(File file, int id, String title) { this.file = file; this.id = id; this.title = title; }
    }

    public static boolean isVideo(String name) {
        String lower = name.toLowerCase(Locale.ROOT);
        if (lower.startsWith(".")) return false;
        for (String ext : EXTENSIONS) if (lower.endsWith(ext)) return true;
        return false;
    }

    /** Stable, positive, non-zero id that changes when the file is replaced. */
    public static int idFor(String path, long size, long modified) {
        int id = (path + "|" + size + "|" + modified).hashCode() & 0x7fffffff;
        return id == 0 ? 1 : id;
    }

    /** Short stable code used when a file name has nothing the cinema font can draw. */
    public static String code(int id) {
        return Integer.toString(id % 1679616, 36).toUpperCase(Locale.ROOT);
    }

    /** The cinema font only has Latin glyphs: keep printable Latin-1, otherwise fall back to "Video <code>". */
    public static String title(String fileName, String fallback) {
        int dot = fileName.lastIndexOf('.');
        String base = dot > 0 ? fileName.substring(0, dot) : fileName;
        StringBuilder out = new StringBuilder();
        boolean dropped = false;
        for (int i = 0; i < base.length(); i++) {
            char c = base.charAt(i);
            if (c == '_') c = ' ';
            if (c >= 0x20 && c < 0x7f || c >= 0xa0 && c <= 0xff) out.append(c);
            else dropped = true;
        }
        String clean = out.toString().replaceAll("\\s+", " ").trim();
        if (clean.isEmpty() || dropped && clean.replaceAll("[^A-Za-z0-9]", "").length() < 3)
            return "Video " + fallback;
        return clean.length() > 40 ? clean.substring(0, 37) + "..." : clean;
    }

    public static List<Entry> scan(File[] folders) {
        List<File> files = new ArrayList<File>();
        for (File folder : folders) {
            File[] list = folder == null ? null : folder.listFiles();
            if (list == null) continue;
            for (File f : list) if (f.isFile() && f.length() > 0 && isVideo(f.getName())) files.add(f);
        }
        Collections.sort(files, new Comparator<File>() {
            public int compare(File a, File b) {
                return a.lastModified() == b.lastModified() ? a.getName().compareTo(b.getName())
                    : a.lastModified() > b.lastModified() ? -1 : 1;
            }
        });
        // The native list merges entries with the same name, so titles must be unique.
        List<Entry> entries = new ArrayList<Entry>();
        java.util.Set<String> used = new java.util.HashSet<String>();
        for (File f : files) {
            int id = idFor(f.getAbsolutePath(), f.length(), f.lastModified());
            String base = title(f.getName(), code(id)), title = base;
            for (int n = 2; !used.add(title.toLowerCase(Locale.ROOT)); n++) title = base + " " + n;
            entries.add(new Entry(f, id, title));
        }
        return entries;
    }

    /** Where to start: resume a saved position unless it is near the beginning or the end. */
    public static int startPosition(int saved, int duration) {
        if (saved < RESUME_MIN_MS) return 0;
        if (duration > 0 && saved > duration - RESUME_TAIL_MS) return 0;
        return saved;
    }

    public static String duration(long ms) {
        long s = Math.max(0, ms / 1000);
        return s >= 3600 ? String.format(Locale.ROOT, "%d:%02d:%02d", s / 3600, s / 60 % 60, s % 60)
                         : String.format(Locale.ROOT, "%d:%02d", s / 60, s % 60);
    }

    public static int seek(int position, int delta, int duration) {
        int target = Math.max(0, position + delta);
        return duration > 0 ? Math.min(target, Math.max(0, duration - 1000)) : target;
    }
}
