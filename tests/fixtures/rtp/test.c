#include "Limelight-internal.h"
#include "RtpReorderQueue.h"
#include <stdio.h>
static uint64_t now;
uint64_t PltGetMillis(void) { return now; }
typedef struct {RTP_PACKET rtp; RTP_QUEUE_ENTRY entry;} Pkt;
static Pkt* packet(unsigned seq) {Pkt* p=calloc(1,sizeof(*p)); assert(p); p->rtp.sequenceNumber=seq; return p;}
static void add(PRTP_REORDER_QUEUE q,unsigned seq,int expected) {Pkt* p=packet(seq); int r=RtpqAddPacket(q,&p->rtp,&p->entry);assert(r==expected);if(r==RTPQ_RET_REJECTED||r==RTPQ_RET_HANDLE_IMMEDIATELY)free(p);}
static void take(PRTP_REORDER_QUEUE q,unsigned seq) {PRTP_PACKET p=RtpqGetQueuedPacket(q);assert(p&&p->sequenceNumber==seq);free(p);}
static void baseline(void) {RTP_REORDER_QUEUE q;now=0;RtpqInitializeQueue(&q,16,40);add(&q,100,0);add(&q,102,1);add(&q,102,3);add(&q,101,2);take(&q,101);take(&q,102);assert(!RtpqGetQueuedPacket(&q));add(&q,100,3);assert(q.queueSize==0);RtpqCleanupQueue(&q);}
static void timeout_reorder(void) {RTP_REORDER_QUEUE q;now=0;RtpqInitializeQueue(&q,16,40);add(&q,100,0);add(&q,103,1);now=41;add(&q,101,3);assert(q.queueSize==1);add(&q,104,2);take(&q,103);take(&q,104);assert(!RtpqGetQueuedPacket(&q));RtpqCleanupQueue(&q);}
static void size_reorder(void) {RTP_REORDER_QUEUE q;now=0;RtpqInitializeQueue(&q,3,40);add(&q,100,0);add(&q,103,1);add(&q,104,1);add(&q,101,3);assert(q.queueSize==2);add(&q,105,2);take(&q,103);take(&q,104);take(&q,105);assert(!RtpqGetQueuedPacket(&q));RtpqCleanupQueue(&q);}
static void wrap(void) {RTP_REORDER_QUEUE q;now=0;RtpqInitializeQueue(&q,16,40);add(&q,65534,0);add(&q,65535,0);add(&q,1,1);add(&q,0,2);take(&q,0);take(&q,1);assert(!RtpqGetQueuedPacket(&q));RtpqCleanupQueue(&q);}
int main(int argc,char**argv) {baseline();wrap();if(argc>1){timeout_reorder();size_reorder();}puts("PASS: normal order, duplicates, wrap, and requested late-packet cases");return 0;}
