#pragma once
#include <stdint.h>
typedef struct {uint8_t flags, packetType; uint16_t sequenceNumber;} RTP_PACKET, *PRTP_PACKET;
