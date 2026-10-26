#pragma once
#include <assert.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#define LC_ASSERT(x) assert(x)
#define isBefore16(x,y) ((uint16_t)((x)-(y)) > (UINT16_MAX/2))
#define Limelog(...) ((void)0)
uint64_t PltGetMillis(void);
