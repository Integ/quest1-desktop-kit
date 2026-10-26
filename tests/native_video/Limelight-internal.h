#pragma once
/* Minimal host test context, GPL-3.0-or-later. No network or decoder APIs. */
#include <assert.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include "Video.h"
#define LC_ASSERT(x) assert(x)
#define U16(x) ((uint16_t)(x))
#define isBefore16(x,y) ((uint16_t)((x)-(y)) > UINT16_MAX/2)
#define isBefore32(x,y) ((uint32_t)((x)-(y)) > UINT32_MAX/2)
#define APP_VERSION_AT_LEAST(a,b,c) (AppVersionQuad[0]>(a)||(AppVersionQuad[0]==(a)&&(AppVersionQuad[1]>(b)||(AppVersionQuad[1]==(b)&&AppVersionQuad[2]>=(c)))))
#if __BYTE_ORDER__ == __ORDER_LITTLE_ENDIAN__
#define LE32(x) (x)
#else
#define LE32(x) __builtin_bswap32(x)
#endif
#define Limelog(...) ((void)0)
extern int AppVersionQuad[4];
extern struct TestConfig {int packetSize;} StreamConfig;
uint64_t PltGetMillis(void);
void connectionSawFrame(int);
