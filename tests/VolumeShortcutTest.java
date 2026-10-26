import local.quest.adbkeeper.VolumeShortcut;
public final class VolumeShortcutTest {
  static void check(boolean ok,String text){if(!ok)throw new AssertionError(text);}
  public static void main(String[] args){
    VolumeShortcut s=new VolumeShortcut();
    check(!s.accept(8,7,0),"down alone");
    check(!s.accept(7,8,200),"up alone");
    check(!s.accept(8,7,400),"three events");
    check(s.accept(7,8,600),"full shortcut");
    check(!s.accept(8,7,700),"cooldown");
    s.reset();
    check(!s.accept(8,7,0),"start");
    check(!s.accept(7,8,2000),"slow pair rejected");
    check(!s.accept(8,7,2200),"new start");
    check(!s.accept(7,8,2400),"new second");
    check(!s.accept(8,7,2600),"new third");
    check(s.accept(7,8,2800),"restart after timeout");
    s.reset();
    for(int i=10;i>4;i--)check(!s.accept(i,i-1,100*(10-i)),"normal volume hold");
    s.reset();
    check(!s.accept(0,0,0),"zero unchanged");
    check(!s.accept(8,2,10),"software volume jump");
    check(!s.accept(-1,2,20),"bad extras");
    System.out.println("PASS: volume sequence, timeout, cooldown, hold, mute edge and invalid extras");
  }
}
