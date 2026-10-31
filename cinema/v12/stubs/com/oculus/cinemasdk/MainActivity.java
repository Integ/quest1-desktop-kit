package com.oculus.cinemasdk;

import android.graphics.SurfaceTexture;

/** Compile-time stub matching the native methods of the real cinema MainActivity. */
public class MainActivity extends com.oculus.vrappframework.VrActivity {
    public static native void nativeAddApp(long app, String name, String poster, int appId, boolean running);
    public static native void nativeAddPc(long app, String name, String uuid, int pairState, int reachability, String binding, boolean running);
    public static native void nativeRemoveApp(long app, int appId);
    public static native SurfaceTexture nativePrepareNewVideo(long app);
    public void initAppSelector(String uuid) { }
    public static native void nativeSetVideoSize(long app, int width, int height, int rotation, int duration);
}
