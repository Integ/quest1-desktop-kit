/* GPL-3.0-or-later. Actual production functions are inserted by test_native.py. */
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "Video.h"
#define LC_ASSERT(x) assert(x)
#define Limelog(...) ((void)0)
#define U24(x) ((unsigned int)(x)&0xFFFFFF)
#define isBefore24(x,y) (U24((x)-(y))>0x7FFFFF)
#define isBefore32(x,y) ((uint32_t)((x)-(y))>UINT32_MAX/2)
typedef struct {char* data;int offset;int length;} BUFFER_DESC;
int AppVersionQuad[4]={7,1,431,0};
static int nextFrameNumber=1,lastPacketInStream=0xFFFFFF,decodingFrame;
static int waitingForNextSuccessfulFrame,waitingForIdrFrame,startFrameNumber=1;
static unsigned long long firstPacketReceiveTime;
static int assembled,dropped,refreshRequests,bytes;
static void dropFrameState(void){dropped++;bytes=0;}
static void requestIdrOnDemand(void){refreshRequests++;}
static void connectionSawFrame(int f){}
static void connectionDetectedFrameLoss(int a,int b){refreshRequests++;}
static int isIdrFrameStart(BUFFER_DESC* b){return 0;}
static void processRtpPayloadSlow(PNV_VIDEO_PACKET p,BUFFER_DESC* b){assert(0);}
static void processRtpPayloadFast(BUFFER_DESC b){assert(b.length>=0);bytes+=b.length;}
static void reassembleFrame(int f){assembled++;}

/* @FIRST_PACKET_FUNCTION@ */
/* @PROCESS_PAYLOAD_FUNCTION@ */

static void packet(int frame,int block,int last,unsigned seq,unsigned flags){
 unsigned char data[sizeof(NV_VIDEO_PACKET)+32]={0};
 PNV_VIDEO_PACKET p=(PNV_VIDEO_PACKET)data;p->frameIndex=frame;p->streamPacketIndex=seq<<8;
 p->multiFecBlocks=(last<<6)|(block<<4);p->flags=flags|FLAG_CONTAINS_PIC_DATA;
 processRtpPayload(p,sizeof(data),1000);
}
int main(void){
 for(int block=0;block<3;block++)for(int i=0;i<4;i++){
  packet(1,block,2,10+block*5+i,(i==0?FLAG_SOF:0)|(i==3?FLAG_EOF:0));
  assert(assembled==(block==2&&i==3));
 }
 assert(bytes==12*32-8&&nextFrameNumber==2&&decodingFrame==0&&dropped==0);
 packet(2,0,0,30,FLAG_SOF);packet(2,0,0,35,0);
 assert(dropped==1&&refreshRequests==1&&nextFrameNumber==3&&decodingFrame==0);
 packet(2,0,0,36,FLAG_EOF);assert(assembled==1);
 packet(3,0,0,40,FLAG_SOF);packet(3,0,0,41,FLAG_EOF);
 assert(assembled==2&&decodingFrame==0&&nextFrameNumber==4);
 puts("PASS: actual depacketizer stages one complete multi-block frame, accepts parity gaps, drops corruption and resumes next frame");
}
