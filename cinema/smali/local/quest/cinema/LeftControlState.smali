.class public final Llocal/quest/cinema/LeftControlState;
.super Ljava/lang/Object;
.source "LeftControlState.java"


# instance fields
.field private analog:Z

.field private digital:Z


# direct methods
.method public constructor <init>()V
    .locals 0

    .line 4
    invoke-direct {p0}, Ljava/lang/Object;-><init>()V

    return-void
.end method


# virtual methods
.method public analog(F)V
    .locals 1

    .line 10
    invoke-static {p1}, Ljava/lang/Float;->isNaN(F)Z

    move-result v0

    if-nez v0, :cond_1

    const v0, 0x3eb33333    # 0.35f

    cmpg-float v0, p1, v0

    if-gtz v0, :cond_0

    goto :goto_0

    .line 11
    :cond_0
    const v0, 0x3f0ccccd    # 0.55f

    cmpl-float p1, p1, v0

    if-ltz p1, :cond_2

    const/4 p1, 0x1

    iput-boolean p1, p0, Llocal/quest/cinema/LeftControlState;->analog:Z

    goto :goto_1

    .line 10
    :cond_1
    :goto_0
    const/4 p1, 0x0

    iput-boolean p1, p0, Llocal/quest/cinema/LeftControlState;->analog:Z

    .line 12
    :cond_2
    :goto_1
    return-void
.end method

.method public digital(Z)V
    .locals 0

    .line 8
    iput-boolean p1, p0, Llocal/quest/cinema/LeftControlState;->digital:Z

    return-void
.end method

.method public down()Z
    .locals 1

    .line 13
    iget-boolean v0, p0, Llocal/quest/cinema/LeftControlState;->digital:Z

    if-nez v0, :cond_1

    iget-boolean v0, p0, Llocal/quest/cinema/LeftControlState;->analog:Z

    if-eqz v0, :cond_0

    goto :goto_0

    :cond_0
    const/4 v0, 0x0

    goto :goto_1

    :cond_1
    :goto_0
    const/4 v0, 0x1

    :goto_1
    return v0
.end method

.method public reset()V
    .locals 1

    .line 14
    const/4 v0, 0x0

    iput-boolean v0, p0, Llocal/quest/cinema/LeftControlState;->digital:Z

    iput-boolean v0, p0, Llocal/quest/cinema/LeftControlState;->analog:Z

    return-void
.end method
