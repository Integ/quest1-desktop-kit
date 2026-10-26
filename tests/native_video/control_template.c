/* GPL-3.0-or-later. Actual production functions are inserted by test_native.py. */
#include <assert.h>
#include <stdlib.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
int AppVersionQuad[4]={7,1,431,0};
#define APP_VERSION_AT_LEAST(a,b,c) (AppVersionQuad[0]>(a)||(AppVersionQuad[0]==(a)&&(AppVersionQuad[1]>(b)||(AppVersionQuad[1]==(b)&&AppVersionQuad[2]>=(c)))))
#define Limelog(...) ((void)0)
#define LastSocketError() -1
#define IDX_INVALIDATE_REF_FRAMES 2
#define IDX_REQUEST_IDR_FRAME 0
static long lastSeenFrame=100;
static short packetTypes[3]={0x305,0x307,0x301};
static short payloadLengths[3]={2,1,24};
static char* preconstructedPayloads[3]={0};
static int sentType,sentLength,transportOk=1,terminated;
static void termination(int e){terminated=1;}
static struct {void(*connectionTerminated)(int);} ListenerCallbacks={termination};
static int sendMessageAndForget(short t,short n,const void* p){sentType=t;sentLength=n;return transportOk;}
static int sendMessageAndDiscardReply(short t,short n,const void* p){sentType=t;sentLength=n;return transportOk;}

/* @RTSP_SESSION_FUNCTION@ */
/* @IDR_REQUEST_FUNCTION@ */

int main(void){
 char out[256];
 assert(parseRtspSessionId(out,sizeof(out),"DEADBEEFCAFE;timeout=90000"));
 assert(!strcmp(out,"DEADBEEFCAFE"));
 assert(parseRtspSessionId(out,sizeof(out)," \tDEADBEEFCAFE;timeout=90000"));
 assert(!strcmp(out,"DEADBEEFCAFE"));
 assert(parseRtspSessionId(out,sizeof(out),"plain-token"));
 assert(!parseRtspSessionId(out,sizeof(out),";timeout=90"));
 assert(!parseRtspSessionId(out,sizeof(out),NULL));
 assert(!parseRtspSessionId(out,sizeof(out)," \t"));
 char longToken[400];memset(longToken,'A',399);longToken[399]=0;
 assert(!parseRtspSessionId(out,sizeof(out),longToken));
 assert(!parseRtspSessionId(out,0,"token"));
 char boundary[256];memset(boundary,'B',255);boundary[255]=0;
 assert(parseRtspSessionId(out,sizeof(out),boundary));assert(strlen(out)==255);
 requestIdrFrame();assert(sentType==0x302&&sentLength==2&&!terminated);
 AppVersionQuad[2]=430;requestIdrFrame();assert(sentType==0x301&&sentLength==24);
 AppVersionQuad[2]=431;transportOk=0;requestIdrFrame();assert(terminated);
 puts("PASS: bounded RTSP tokens, whitespace/timeout/long/empty input, explicit IDR packet, legacy fallback and transport failure");
}
