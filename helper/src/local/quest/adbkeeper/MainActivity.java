package local.quest.adbkeeper;
import android.app.Activity;
import android.os.Bundle;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.TextView;
import android.widget.ScrollView;
import android.view.View;
import android.provider.Settings;
import android.net.Uri;
import android.content.Intent;

public final class MainActivity extends Activity {
    private TextView status;
    public void onCreate(Bundle b) {
        super.onCreate(b);
        LinearLayout body = new LinearLayout(this);body.setOrientation(LinearLayout.VERTICAL);body.setPadding(36,30,36,24);
        status = new TextView(this);status.setTextSize(24);body.addView(status);
        TextView info = new TextView(this);info.setTextSize(18);
        info.setText("开机后自动打开影院，并保留 USB 和无线 ADB 连接。\n影院每次开机只自动打开一次，退出后可随时手动重开。\n点击通知中的“打开影院”可快速返回。\n不读取用户文件，不访问互联网。");body.addView(info);
        Button cinema = new Button(this);cinema.setText("▶ 打开 Quest Cinema Fix");body.addView(cinema);
        cinema.setOnClickListener(new View.OnClickListener(){public void onClick(View v){CinemaShortcutActivity.open(MainActivity.this);}});
        Button autoOn = new Button(this);autoOn.setText("启用影院开机自启动");body.addView(autoOn);
        autoOn.setOnClickListener(new View.OnClickListener(){public void onClick(View v){State.setCinemaEnabled(MainActivity.this,true);refresh();}});
        Button autoOff = new Button(this);autoOff.setText("关闭影院开机自启动");body.addView(autoOff);
        autoOff.setOnClickListener(new View.OnClickListener(){public void onClick(View v){State.setCinemaEnabled(MainActivity.this,false);refresh();}});
        Button permission = new Button(this);permission.setText("设置开机后台启动权限");body.addView(permission);
        permission.setOnClickListener(new View.OnClickListener(){public void onClick(View v){startActivity(new Intent(Settings.ACTION_MANAGE_OVERLAY_PERMISSION,Uri.parse("package:"+getPackageName())));}});
        Button usbOn = new Button(this);usbOn.setText("启用 USB ADB 常驻");body.addView(usbOn);
        usbOn.setOnClickListener(new View.OnClickListener(){public void onClick(View v){changeUsb(true);}});
        Button usbOff = new Button(this);usbOff.setText("关闭 USB 常驻与调试");body.addView(usbOff);
        usbOff.setOnClickListener(new View.OnClickListener(){public void onClick(View v){changeUsb(false);}});
        Button enable = new Button(this);enable.setText("启用无线 ADB 常驻");body.addView(enable);
        Button disable = new Button(this);disable.setText("关闭常驻与无线 ADB");body.addView(disable);
        enable.setOnClickListener(new View.OnClickListener(){public void onClick(View v){change(true);}});
        disable.setOnClickListener(new View.OnClickListener(){public void onClick(View v){change(false);}});
        ScrollView scroll = new ScrollView(this);scroll.addView(body);setContentView(scroll);refresh();
    }
    public void onResume(){super.onResume();if(status!=null)refresh();}
    private void refresh(){status.setText("影院开机自启："+(State.cinemaEnabled(this)?"开":"关")+"\nUSB ADB 常驻："+(State.usbEnabled(this)?"开":"关")+"\n无线 ADB 常驻："+(State.enabled(this)?"开":"关")+"\n后台启动权限："+(Settings.canDrawOverlays(this)?"已允许":"待授权"));}
    private void changeUsb(boolean enabled){
        try {State.setUsbEnabled(this,enabled);refresh();}
        catch(SecurityException e){status.setText("需要电脑完成系统设置授权后才能启用。");}
    }
    private void change(boolean enabled){
        try {State.setEnabled(this,enabled);refresh();}
        catch(SecurityException e){status.setText("需要电脑完成系统设置授权后才能启用。");}
    }
}
