.class public final Llocal/quest/cinema/LeftHandControls;
.super Ljava/lang/Object;
.source "LeftHandControls.java"


# static fields
.field private static final main:Landroid/os/Handler;

.field private static final state:Llocal/quest/cinema/LeftControlState;

.field private static final taps:Llocal/quest/cinema/LeftTapGesture;

.field private static touchSent:Z

.field private static touchStart:J


# direct methods
.method static constructor <clinit>()V
    .locals 2

    .line 13
    new-instance v0, Llocal/quest/cinema/LeftControlState;

    invoke-direct {v0}, Llocal/quest/cinema/LeftControlState;-><init>()V

    sput-object v0, Llocal/quest/cinema/LeftHandControls;->state:Llocal/quest/cinema/LeftControlState;

    .line 16
    new-instance v0, Llocal/quest/cinema/LeftTapGesture;

    invoke-direct {v0}, Llocal/quest/cinema/LeftTapGesture;-><init>()V

    sput-object v0, Llocal/quest/cinema/LeftHandControls;->taps:Llocal/quest/cinema/LeftTapGesture;

    .line 17
    new-instance v0, Landroid/os/Handler;

    invoke-static {}, Landroid/os/Looper;->getMainLooper()Landroid/os/Looper;

    move-result-object v1

    invoke-direct {v0, v1}, Landroid/os/Handler;-><init>(Landroid/os/Looper;)V

    sput-object v0, Llocal/quest/cinema/LeftHandControls;->main:Landroid/os/Handler;

    return-void
.end method

.method public constructor <init>()V
    .locals 0

    .line 12
    invoke-direct {p0}, Ljava/lang/Object;-><init>()V

    return-void
.end method

.method public static onKey(Landroid/app/Activity;Landroid/view/KeyEvent;)Z
    .locals 17

    .line 49
    invoke-virtual/range {p1 .. p1}, Landroid/view/KeyEvent;->getKeyCode()I

    move-result v0

    .line 50
    invoke-virtual/range {p1 .. p1}, Landroid/view/KeyEvent;->getAction()I

    move-result v1

    const/4 v2, 0x0

    const/4 v3, 0x1

    if-nez v1, :cond_0

    move v1, v3

    goto :goto_0

    :cond_0
    move v1, v2

    .line 51
    :goto_0
    if-nez v1, :cond_1

    invoke-virtual/range {p1 .. p1}, Landroid/view/KeyEvent;->getAction()I

    move-result v4

    if-eq v4, v3, :cond_1

    return v2

    .line 52
    :cond_1
    const/16 v4, 0x68

    if-ne v0, v4, :cond_2

    .line 53
    sget-object v0, Llocal/quest/cinema/LeftHandControls;->state:Llocal/quest/cinema/LeftControlState;

    invoke-virtual {v0, v1}, Llocal/quest/cinema/LeftControlState;->digital(Z)V

    .line 54
    invoke-static/range {p0 .. p0}, Llocal/quest/cinema/LeftHandControls;->syncTouch(Landroid/app/Activity;)V

    .line 55
    return v3

    .line 58
    :cond_2
    const/16 v1, 0x63

    if-ne v0, v1, :cond_3

    const/16 v1, 0x60

    move v10, v1

    goto :goto_2

    .line 59
    :cond_3
    const/16 v1, 0x64

    if-eq v0, v1, :cond_5

    const/16 v1, 0x52

    if-eq v0, v1, :cond_5

    const/16 v1, 0x7d

    if-eq v0, v1, :cond_5

    const/16 v1, 0x6a

    if-ne v0, v1, :cond_4

    goto :goto_1

    .line 62
    :cond_4
    return v2

    .line 61
    :cond_5
    :goto_1
    const/4 v1, 0x4

    move v10, v1

    .line 63
    :goto_2
    new-instance v4, Landroid/view/KeyEvent;

    invoke-virtual/range {p1 .. p1}, Landroid/view/KeyEvent;->getDownTime()J

    move-result-wide v5

    invoke-virtual/range {p1 .. p1}, Landroid/view/KeyEvent;->getEventTime()J

    move-result-wide v7

    .line 64
    invoke-virtual/range {p1 .. p1}, Landroid/view/KeyEvent;->getAction()I

    move-result v9

    invoke-virtual/range {p1 .. p1}, Landroid/view/KeyEvent;->getRepeatCount()I

    move-result v11

    invoke-virtual/range {p1 .. p1}, Landroid/view/KeyEvent;->getMetaState()I

    move-result v12

    .line 65
    invoke-virtual/range {p1 .. p1}, Landroid/view/KeyEvent;->getDeviceId()I

    move-result v13

    invoke-virtual/range {p1 .. p1}, Landroid/view/KeyEvent;->getScanCode()I

    move-result v14

    invoke-virtual/range {p1 .. p1}, Landroid/view/KeyEvent;->getFlags()I

    move-result v15

    invoke-virtual/range {p1 .. p1}, Landroid/view/KeyEvent;->getSource()I

    move-result v16

    invoke-direct/range {v4 .. v16}, Landroid/view/KeyEvent;-><init>(JJIIIIIIII)V

    .line 66
    new-instance v1, Ljava/lang/StringBuilder;

    invoke-direct {v1}, Ljava/lang/StringBuilder;-><init>()V

    const-string v2, "key "

    invoke-virtual {v1, v2}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v1

    invoke-virtual {v1, v0}, Ljava/lang/StringBuilder;->append(I)Ljava/lang/StringBuilder;

    move-result-object v0

    const-string v1, " -> "

    invoke-virtual {v0, v1}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v0

    invoke-virtual {v0, v10}, Ljava/lang/StringBuilder;->append(I)Ljava/lang/StringBuilder;

    move-result-object v0

    const-string v1, " action "

    invoke-virtual {v0, v1}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v0

    invoke-virtual/range {p1 .. p1}, Landroid/view/KeyEvent;->getAction()I

    move-result v1

    invoke-virtual {v0, v1}, Ljava/lang/StringBuilder;->append(I)Ljava/lang/StringBuilder;

    move-result-object v0

    invoke-virtual {v0}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object v0

    const-string v1, "QuestLeft"

    invoke-static {v1, v0}, Landroid/util/Log;->i(Ljava/lang/String;Ljava/lang/String;)I

    .line 67
    move-object/from16 v0, p0

    invoke-virtual {v0, v4}, Landroid/app/Activity;->dispatchKeyEvent(Landroid/view/KeyEvent;)Z

    .line 68
    return v3
.end method

.method public static onMotion(Landroid/app/Activity;Landroid/view/MotionEvent;)V
    .locals 2

    .line 72
    invoke-virtual {p1}, Landroid/view/MotionEvent;->getSource()I

    move-result v0

    and-int/lit8 v0, v0, 0x10

    if-nez v0, :cond_0

    return-void

    .line 73
    :cond_0
    invoke-virtual {p1}, Landroid/view/MotionEvent;->getActionMasked()I

    move-result v0

    const/4 v1, 0x3

    if-ne v0, v1, :cond_1

    .line 74
    invoke-static {p0}, Llocal/quest/cinema/LeftHandControls;->reset(Landroid/app/Activity;)V

    goto :goto_0

    .line 75
    :cond_1
    invoke-virtual {p1}, Landroid/view/MotionEvent;->getActionMasked()I

    move-result v0

    const/4 v1, 0x2

    if-ne v0, v1, :cond_2

    .line 76
    const/16 v0, 0x11

    invoke-virtual {p1, v0}, Landroid/view/MotionEvent;->getAxisValue(I)F

    move-result v0

    .line 77
    const/16 v1, 0x17

    invoke-virtual {p1, v1}, Landroid/view/MotionEvent;->getAxisValue(I)F

    move-result p1

    .line 76
    invoke-static {v0, p1}, Ljava/lang/Math;->max(FF)F

    move-result p1

    .line 78
    sget-object v0, Llocal/quest/cinema/LeftHandControls;->state:Llocal/quest/cinema/LeftControlState;

    invoke-virtual {v0, p1}, Llocal/quest/cinema/LeftControlState;->analog(F)V

    .line 79
    invoke-static {p0}, Llocal/quest/cinema/LeftHandControls;->syncTouch(Landroid/app/Activity;)V

    .line 81
    :cond_2
    :goto_0
    return-void
.end method

.method public static onTouch(Landroid/app/Activity;Landroid/view/MotionEvent;)Z
    .locals 6

    .line 20
    invoke-virtual {p1}, Landroid/view/MotionEvent;->getEventTime()J

    move-result-wide v0

    .line 21
    invoke-virtual {p1}, Landroid/view/MotionEvent;->getActionMasked()I

    move-result v2

    const/4 v3, 0x0

    packed-switch v2, :pswitch_data_0

    .line 44
    return v3

    .line 40
    :pswitch_0
    sget-object p0, Llocal/quest/cinema/LeftHandControls;->taps:Llocal/quest/cinema/LeftTapGesture;

    invoke-virtual {p0}, Llocal/quest/cinema/LeftTapGesture;->consuming()Z

    move-result p0

    .line 41
    sget-object p1, Llocal/quest/cinema/LeftHandControls;->taps:Llocal/quest/cinema/LeftTapGesture;

    invoke-virtual {p1}, Llocal/quest/cinema/LeftTapGesture;->reset()V

    .line 42
    return p0

    .line 25
    :pswitch_1
    sget-object p0, Llocal/quest/cinema/LeftHandControls;->taps:Llocal/quest/cinema/LeftTapGesture;

    invoke-virtual {p1}, Landroid/view/MotionEvent;->getX()F

    move-result v0

    invoke-virtual {p1}, Landroid/view/MotionEvent;->getY()F

    move-result p1

    invoke-virtual {p0, v0, p1}, Llocal/quest/cinema/LeftTapGesture;->move(FF)V

    .line 26
    sget-object p0, Llocal/quest/cinema/LeftHandControls;->taps:Llocal/quest/cinema/LeftTapGesture;

    invoke-virtual {p0}, Llocal/quest/cinema/LeftTapGesture;->consuming()Z

    move-result p0

    return p0

    .line 28
    :pswitch_2
    sget-object v2, Llocal/quest/cinema/LeftHandControls;->taps:Llocal/quest/cinema/LeftTapGesture;

    invoke-virtual {v2}, Llocal/quest/cinema/LeftTapGesture;->consuming()Z

    move-result v2

    .line 29
    sget-object v4, Llocal/quest/cinema/LeftHandControls;->taps:Llocal/quest/cinema/LeftTapGesture;

    invoke-virtual {p1}, Landroid/view/MotionEvent;->getX()F

    move-result v5

    invoke-virtual {p1}, Landroid/view/MotionEvent;->getY()F

    move-result p1

    invoke-virtual {v4, v0, v1, v5, p1}, Llocal/quest/cinema/LeftTapGesture;->up(JFF)Z

    move-result p1

    if-eqz p1, :cond_0

    .line 30
    const-string p1, "QuestLeft"

    const-string v0, "double tap: toggle cinema menu"

    invoke-static {p1, v0}, Landroid/util/Log;->i(Ljava/lang/String;Ljava/lang/String;)I

    .line 31
    new-instance p1, Landroid/view/KeyEvent;

    const/4 v0, 0x4

    invoke-direct {p1, v3, v0}, Landroid/view/KeyEvent;-><init>(II)V

    invoke-virtual {p0, p1}, Landroid/app/Activity;->dispatchKeyEvent(Landroid/view/KeyEvent;)Z

    .line 32
    sget-object p1, Llocal/quest/cinema/LeftHandControls;->main:Landroid/os/Handler;

    new-instance v0, Llocal/quest/cinema/LeftHandControls$1;

    invoke-direct {v0, p0}, Llocal/quest/cinema/LeftHandControls$1;-><init>(Landroid/app/Activity;)V

    const-wide/16 v3, 0x50

    invoke-virtual {p1, v0, v3, v4}, Landroid/os/Handler;->postDelayed(Ljava/lang/Runnable;J)Z

    .line 38
    :cond_0
    return v2

    .line 23
    :pswitch_3
    sget-object p0, Llocal/quest/cinema/LeftHandControls;->taps:Llocal/quest/cinema/LeftTapGesture;

    invoke-virtual {p1}, Landroid/view/MotionEvent;->getX()F

    move-result v2

    invoke-virtual {p1}, Landroid/view/MotionEvent;->getY()F

    move-result p1

    invoke-virtual {p0, v0, v1, v2, p1}, Llocal/quest/cinema/LeftTapGesture;->down(JFF)Z

    move-result p0

    return p0

    nop

    :pswitch_data_0
    .packed-switch 0x0
        :pswitch_3
        :pswitch_2
        :pswitch_1
        :pswitch_0
    .end packed-switch
.end method

.method public static reset(Landroid/app/Activity;)V
    .locals 1

    .line 97
    sget-object v0, Llocal/quest/cinema/LeftHandControls;->taps:Llocal/quest/cinema/LeftTapGesture;

    invoke-virtual {v0}, Llocal/quest/cinema/LeftTapGesture;->reset()V

    .line 98
    sget-object v0, Llocal/quest/cinema/LeftHandControls;->state:Llocal/quest/cinema/LeftControlState;

    invoke-virtual {v0}, Llocal/quest/cinema/LeftControlState;->reset()V

    .line 99
    invoke-static {p0}, Llocal/quest/cinema/LeftHandControls;->syncTouch(Landroid/app/Activity;)V

    .line 100
    return-void
.end method

.method private static syncTouch(Landroid/app/Activity;)V
    .locals 10

    .line 84
    sget-object v0, Llocal/quest/cinema/LeftHandControls;->state:Llocal/quest/cinema/LeftControlState;

    invoke-virtual {v0}, Llocal/quest/cinema/LeftControlState;->down()Z

    move-result v0

    .line 85
    sget-boolean v1, Llocal/quest/cinema/LeftHandControls;->touchSent:Z

    if-ne v0, v1, :cond_0

    return-void

    .line 86
    :cond_0
    invoke-static {}, Landroid/os/SystemClock;->uptimeMillis()J

    move-result-wide v4

    .line 87
    if-eqz v0, :cond_1

    sput-wide v4, Llocal/quest/cinema/LeftHandControls;->touchStart:J

    .line 88
    :cond_1
    sget-wide v2, Llocal/quest/cinema/LeftHandControls;->touchStart:J

    .line 89
    xor-int/lit8 v6, v0, 0x1

    .line 88
    const/4 v7, 0x0

    const/4 v8, 0x0

    const/4 v9, 0x0

    invoke-static/range {v2 .. v9}, Landroid/view/MotionEvent;->obtain(JJIFFI)Landroid/view/MotionEvent;

    move-result-object v1

    .line 90
    :try_start_0
    invoke-virtual {p0, v1}, Landroid/app/Activity;->dispatchTouchEvent(Landroid/view/MotionEvent;)Z
    :try_end_0
    .catchall {:try_start_0 .. :try_end_0} :catchall_0

    .line 91
    invoke-virtual {v1}, Landroid/view/MotionEvent;->recycle()V

    .line 92
    sput-boolean v0, Llocal/quest/cinema/LeftHandControls;->touchSent:Z

    .line 93
    new-instance p0, Ljava/lang/StringBuilder;

    invoke-direct {p0}, Ljava/lang/StringBuilder;-><init>()V

    const-string v1, "left trigger touch "

    invoke-virtual {p0, v1}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object p0

    if-eqz v0, :cond_2

    const-string v0, "down"

    goto :goto_0

    :cond_2
    const-string v0, "up"

    :goto_0
    invoke-virtual {p0, v0}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object p0

    invoke-virtual {p0}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object p0

    const-string v0, "QuestLeft"

    invoke-static {v0, p0}, Landroid/util/Log;->i(Ljava/lang/String;Ljava/lang/String;)I

    .line 94
    return-void

    .line 91
    :catchall_0
    move-exception v0

    move-object p0, v0

    invoke-virtual {v1}, Landroid/view/MotionEvent;->recycle()V

    throw p0
.end method
