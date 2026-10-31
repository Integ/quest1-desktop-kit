import local.quest.cinema.LocalVideoCatalog;
import java.io.File;
import java.nio.file.Files;
import java.util.List;

public final class LocalVideoCatalogTest {
    static void check(boolean ok, String what) { if (!ok) throw new AssertionError(what); }
    public static void main(String[] args) throws Exception {
        check(LocalVideoCatalog.isVideo("a.MP4") && LocalVideoCatalog.isVideo("b.mkv"), "video extensions");
        check(!LocalVideoCatalog.isVideo("notes.txt") && !LocalVideoCatalog.isVideo(".hidden.mp4"), "non-videos skipped");
        check(LocalVideoCatalog.title("Sample-Clip-1080p60.mp4", "A1").equals("Sample-Clip-1080p60"), "latin title kept");
        check(LocalVideoCatalog.title("my_trip_2024.mov", "A2").equals("my trip 2024"), "underscores become spaces");
        check(LocalVideoCatalog.title("我的视频.mp4", "K3Z").equals("Video K3Z"), "CJK-only title falls back");
        check(LocalVideoCatalog.title("旅行 Vlog 01.mp4", "A4").equals("Vlog 01"), "keeps readable Latin part");
        check(LocalVideoCatalog.title("x".repeat(60) + ".mp4", "A5").length() == 40, "long titles trimmed");
        check(LocalVideoCatalog.idFor("/a", 1, 2) > 0 && LocalVideoCatalog.idFor("/a", 1, 2) == LocalVideoCatalog.idFor("/a", 1, 2), "ids stable and positive");
        check(LocalVideoCatalog.idFor("/a", 1, 2) != LocalVideoCatalog.idFor("/a", 1, 3), "replaced file gets new id");
        check(LocalVideoCatalog.startPosition(10000, 600000) == 0, "short progress starts over");
        check(LocalVideoCatalog.startPosition(120000, 600000) == 120000, "resumes in the middle");
        check(LocalVideoCatalog.startPosition(590000, 600000) == 0, "near the end starts over");
        check(LocalVideoCatalog.duration(141598).equals("2:21") && LocalVideoCatalog.duration(3725000).equals("1:02:05"), "duration labels");
        check(LocalVideoCatalog.seek(5000, -10000, 600000) == 0, "seek clamps at start");
        check(LocalVideoCatalog.seek(595000, 10000, 600000) == 599000, "seek clamps before end");
        File dir = Files.createTempDirectory("lv").toFile();
        File older = new File(dir, "older.mp4"), newer = new File(dir, "newer.mkv"), text = new File(dir, "x.txt"), empty = new File(dir, "empty.mp4");
        Files.write(older.toPath(), new byte[]{1}); Files.write(newer.toPath(), new byte[]{1}); Files.write(text.toPath(), new byte[]{1}); empty.createNewFile();
        older.setLastModified(1000000000000L); newer.setLastModified(1700000000000L);
        List<LocalVideoCatalog.Entry> found = LocalVideoCatalog.scan(new File[]{dir, new File(dir, "missing"), null});
        check(found.size() == 2 && found.get(0).file.equals(newer) && found.get(1).file.equals(older), "newest first, skips text/empty/missing");
        File dir2 = Files.createTempDirectory("lv2").toFile(), sub = new File(dir2, "b");
        sub.mkdir();
        File cjk1 = new File(dir2, "第一集.mp4"), cjk2 = new File(dir2, "第二集.mp4"), same1 = new File(dir2, "clip.mp4"), same2 = new File(sub, "clip.mp4");
        for (File f : new File[]{cjk1, cjk2, same1, same2}) Files.write(f.toPath(), new byte[]{1, 2});
        List<LocalVideoCatalog.Entry> dup = LocalVideoCatalog.scan(new File[]{dir2, sub});
        java.util.Set<String> titles = new java.util.HashSet<String>();
        for (LocalVideoCatalog.Entry e : dup) titles.add(e.title.toLowerCase());
        check(dup.size() == 4 && titles.size() == 4, "titles unique even for CJK names and same file names: " + titles);
        check(LocalVideoCatalog.code(1679616 + 35).equals("Z"), "fallback code is base-36");
        System.out.println("LocalVideoCatalogTest passed");
    }
}
