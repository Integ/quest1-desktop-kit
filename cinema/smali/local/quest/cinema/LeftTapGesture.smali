.class public final Llocal/quest/cinema/LeftTapGesture;
.super Ljava/lang/Object;
.source "LeftTapGesture.java"


# instance fields
.field private active:Z

.field private consuming:Z

.field private downTime:J

.field private downX:F

.field private downY:F

.field private dragged:Z

.field private lastUp:J

.field private lastX:F

.field private lastY:F


# direct methods
.method public constructor <init>()V
    .locals 2

    .line 4
    invoke-direct {p0}, Ljava/lang/Object;-><init>()V

    .line 5
    const-wide/16 v0, -0x1

    iput-wide v0, p0, Llocal/quest/cinema/LeftTapGesture;->lastUp:J

    return-void
.end method

.method private static near(FFFF)Z
    .locals 0

    .line 10
    sub-float/2addr p0, p2

    sub-float/2addr p1, p3

    .line 11
    mul-float/2addr p0, p0

    mul-float/2addr p1, p1

    add-float/2addr p0, p1

    const/high16 p1, 0x45800000    # 4096.0f

    cmpg-float p0, p0, p1

    if-gtz p0, :cond_0

    const/4 p0, 0x1

    goto :goto_0

    :cond_0
    const/4 p0, 0x0

    :goto_0
    return p0
.end method


# virtual methods
.method public consuming()Z
    .locals 1

    .line 20
    iget-boolean v0, p0, Llocal/quest/cinema/LeftTapGesture;->consuming:Z

    return v0
.end method

.method public down(JFF)Z
    .locals 7

    .line 14
    iget-wide v0, p0, Llocal/quest/cinema/LeftTapGesture;->lastUp:J

    const-wide/16 v2, 0x0

    cmp-long v0, v0, v2

    const/4 v1, 0x1

    const/4 v4, 0x0

    if-ltz v0, :cond_0

    iget-wide v5, p0, Llocal/quest/cinema/LeftTapGesture;->lastUp:J

    sub-long v5, p1, v5

    cmp-long v0, v5, v2

    if-ltz v0, :cond_0

    iget-wide v2, p0, Llocal/quest/cinema/LeftTapGesture;->lastUp:J

    sub-long v2, p1, v2

    const-wide/16 v5, 0x15e

    cmp-long v0, v2, v5

    if-gtz v0, :cond_0

    iget v0, p0, Llocal/quest/cinema/LeftTapGesture;->lastX:F

    iget v2, p0, Llocal/quest/cinema/LeftTapGesture;->lastY:F

    invoke-static {p3, p4, v0, v2}, Llocal/quest/cinema/LeftTapGesture;->near(FFFF)Z

    move-result v0

    if-eqz v0, :cond_0

    move v0, v1

    goto :goto_0

    :cond_0
    move v0, v4

    :goto_0
    iput-boolean v0, p0, Llocal/quest/cinema/LeftTapGesture;->consuming:Z

    .line 15
    const-wide/16 v2, -0x1

    iput-wide v2, p0, Llocal/quest/cinema/LeftTapGesture;->lastUp:J

    .line 16
    iput-wide p1, p0, Llocal/quest/cinema/LeftTapGesture;->downTime:J

    iput p3, p0, Llocal/quest/cinema/LeftTapGesture;->downX:F

    iput p4, p0, Llocal/quest/cinema/LeftTapGesture;->downY:F

    iput-boolean v1, p0, Llocal/quest/cinema/LeftTapGesture;->active:Z

    iput-boolean v4, p0, Llocal/quest/cinema/LeftTapGesture;->dragged:Z

    .line 17
    iget-boolean p1, p0, Llocal/quest/cinema/LeftTapGesture;->consuming:Z

    return p1
.end method

.method public move(FF)V
    .locals 2

    .line 19
    iget-boolean v0, p0, Llocal/quest/cinema/LeftTapGesture;->active:Z

    if-eqz v0, :cond_0

    iget v0, p0, Llocal/quest/cinema/LeftTapGesture;->downX:F

    iget v1, p0, Llocal/quest/cinema/LeftTapGesture;->downY:F

    invoke-static {p1, p2, v0, v1}, Llocal/quest/cinema/LeftTapGesture;->near(FFFF)Z

    move-result p1

    if-nez p1, :cond_0

    const/4 p1, 0x1

    iput-boolean p1, p0, Llocal/quest/cinema/LeftTapGesture;->dragged:Z

    :cond_0
    return-void
.end method

.method public reset()V
    .locals 2

    .line 29
    const-wide/16 v0, -0x1

    iput-wide v0, p0, Llocal/quest/cinema/LeftTapGesture;->lastUp:J

    const/4 v0, 0x0

    iput-boolean v0, p0, Llocal/quest/cinema/LeftTapGesture;->active:Z

    iput-boolean v0, p0, Llocal/quest/cinema/LeftTapGesture;->dragged:Z

    iput-boolean v0, p0, Llocal/quest/cinema/LeftTapGesture;->consuming:Z

    return-void
.end method

.method public up(JFF)Z
    .locals 7

    .line 22
    iget-boolean v0, p0, Llocal/quest/cinema/LeftTapGesture;->active:Z

    const/4 v1, 0x1

    const/4 v2, 0x0

    if-eqz v0, :cond_0

    iget-boolean v0, p0, Llocal/quest/cinema/LeftTapGesture;->dragged:Z

    if-nez v0, :cond_0

    iget-wide v3, p0, Llocal/quest/cinema/LeftTapGesture;->downTime:J

    sub-long v3, p1, v3

    const-wide/16 v5, 0x0

    cmp-long v0, v3, v5

    if-ltz v0, :cond_0

    iget-wide v3, p0, Llocal/quest/cinema/LeftTapGesture;->downTime:J

    sub-long v3, p1, v3

    const-wide/16 v5, 0x15e

    cmp-long v0, v3, v5

    if-gtz v0, :cond_0

    iget v0, p0, Llocal/quest/cinema/LeftTapGesture;->downX:F

    iget v3, p0, Llocal/quest/cinema/LeftTapGesture;->downY:F

    invoke-static {p3, p4, v0, v3}, Llocal/quest/cinema/LeftTapGesture;->near(FFFF)Z

    move-result v0

    if-eqz v0, :cond_0

    move v0, v1

    goto :goto_0

    :cond_0
    move v0, v2

    .line 23
    :goto_0
    iget-boolean v3, p0, Llocal/quest/cinema/LeftTapGesture;->consuming:Z

    if-eqz v3, :cond_1

    if-eqz v0, :cond_1

    goto :goto_1

    :cond_1
    move v1, v2

    .line 24
    :goto_1
    if-eqz v0, :cond_2

    iget-boolean v0, p0, Llocal/quest/cinema/LeftTapGesture;->consuming:Z

    if-nez v0, :cond_2

    iput-wide p1, p0, Llocal/quest/cinema/LeftTapGesture;->lastUp:J

    iput p3, p0, Llocal/quest/cinema/LeftTapGesture;->lastX:F

    iput p4, p0, Llocal/quest/cinema/LeftTapGesture;->lastY:F

    goto :goto_2

    .line 25
    :cond_2
    const-wide/16 p1, -0x1

    iput-wide p1, p0, Llocal/quest/cinema/LeftTapGesture;->lastUp:J

    .line 26
    :goto_2
    iput-boolean v2, p0, Llocal/quest/cinema/LeftTapGesture;->active:Z

    iput-boolean v2, p0, Llocal/quest/cinema/LeftTapGesture;->dragged:Z

    iput-boolean v2, p0, Llocal/quest/cinema/LeftTapGesture;->consuming:Z

    .line 27
    return v1
.end method
