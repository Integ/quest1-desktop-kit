#include "Limelight-internal.h"
#include "RtpFecQueue.h"
#include "rs.h"
#include <stdio.h>

int AppVersionQuad[4] = {7,1,431,0};
struct TestConfig StreamConfig = {64};
static uint64_t clockNow = 100;
static int failRecovery;
uint64_t PltGetMillis(void) { return ++clockNow; }
void connectionSawFrame(int frame) { (void)frame; }
int real_reed_solomon_reconstruct(reed_solomon*, unsigned char**, unsigned char*, int, int);
int reed_solomon_reconstruct(reed_solomon* rs,unsigned char** p,unsigned char* m,int n,int size) {
    return failRecovery ? -99 : real_reed_solomon_reconstruct(rs,p,m,n,size);
}

#define DATA 4
#define PARITY 1
#define TOTAL 5
#define SIZE 80
typedef struct { unsigned char* p[TOTAL]; } Block;

static Block block(uint32_t frame,unsigned blockNumber,unsigned lastBlock,unsigned firstSequence) {
    Block b;
    for (unsigned i=0;i<TOTAL;i++) {
        b.p[i]=calloc(1,SIZE+sizeof(RTPFEC_QUEUE_ENTRY)); assert(b.p[i]);
        if(i<DATA) {
            PNV_VIDEO_PACKET v=(PNV_VIDEO_PACKET)(b.p[i]+16);
            v->streamPacketIndex=(uint32_t)((firstSequence+i)&65535)<<8;
            v->frameIndex=frame;
            v->flags=FLAG_CONTAINS_PIC_DATA | (i==0?FLAG_SOF:0) | (i==DATA-1?FLAG_EOF:0);
            v->multiFecFlags=0x10;
            v->multiFecBlocks=(lastBlock<<6)|(blockNumber<<4);
            memset(b.p[i]+32,(unsigned char)(frame+blockNumber*16+i),SIZE-32);
        }
    }
    reed_solomon* rs=reed_solomon_new(DATA,PARITY);assert(rs);
    assert(reed_solomon_encode(rs,b.p,TOTAL,SIZE)==0);
    reed_solomon_release(rs);
    // Sunshine sets transport/FEC metadata after encoding the parity shards.
    for (unsigned i=0;i<TOTAL;i++) {
        PRTP_PACKET r=(PRTP_PACKET)b.p[i];
        r->header=0x90;r->sequenceNumber=(firstSequence+i)&65535;r->timestamp=9000;r->ssrc=123;
        PNV_VIDEO_PACKET v=(PNV_VIDEO_PACKET)(b.p[i]+16);
        v->frameIndex=frame;v->multiFecBlocks=(lastBlock<<6)|(blockNumber<<4);
        v->fecInfo=(i<<12)|(DATA<<22)|(25<<4);
    }
    return b;
}
static void discard(Block* b) {
    for(unsigned i=0;i<TOTAL;i++) {free(b->p[i]);b->p[i]=NULL;}
}
static int feed(RTP_FEC_QUEUE* q,Block* b,unsigned i) {
    unsigned char* p=b->p[i];assert(p);b->p[i]=NULL;
    int result=RtpfAddPacket(q,(PRTP_PACKET)p,SIZE,(PRTPFEC_QUEUE_ENTRY)(p+SIZE));
    if(result==RTPF_RET_REJECTED)free(p);
    return result;
}
static void duplicate(RTP_FEC_QUEUE* q,Block* b,unsigned i) {
    unsigned char* copy=malloc(SIZE+sizeof(RTPFEC_QUEUE_ENTRY));assert(copy);
    memcpy(copy,b->p[i],SIZE);
    int first=RtpfAddPacket(q,(PRTP_PACKET)copy,SIZE,(PRTPFEC_QUEUE_ENTRY)(copy+SIZE));
    assert(first!=RTPF_RET_REJECTED);
    assert(feed(q,b,i)==RTPF_RET_REJECTED);
}
static void drain(RTP_FEC_QUEUE* q,uint32_t frame,unsigned blocks,unsigned firstSeq) {
    for(unsigned blockNumber=0;blockNumber<blocks;blockNumber++) {
        for(unsigned i=0;i<DATA;i++) {
            PRTPFEC_QUEUE_ENTRY e=RtpfGetQueuedPacket(q);assert(e && !e->isParity);
            assert(e->packet->sequenceNumber==((firstSeq+blockNumber*TOTAL+i)&65535));
            PNV_VIDEO_PACKET v=(PNV_VIDEO_PACKET)((unsigned char*)e->packet+16);
            assert(v->frameIndex==frame);
            assert(v->streamPacketIndex==((uint32_t)((firstSeq+blockNumber*TOTAL+i)&65535)<<8));
            assert(v->flags==(FLAG_CONTAINS_PIC_DATA|(i==0?FLAG_SOF:0)|(i==DATA-1?FLAG_EOF:0)));
            assert(((v->multiFecBlocks>>4)&3)==blockNumber);
            for(unsigned j=32;j<SIZE;j++)assert(((unsigned char*)e->packet)[j]==(unsigned char)(frame+blockNumber*16+i));
            free(e->packet);
        }
    }
    assert(!RtpfGetQueuedPacket(q));
}
static void single(void) {
    RTP_FEC_QUEUE q;RtpfInitializeQueue(&q);
    Block b=block(10,0,0,10);
    for(unsigned i=0;i<DATA;i++)assert(feed(&q,&b,i)==(i==3?RTPF_RET_QUEUED_PACKETS_READY:RTPF_RET_QUEUED_NOTHING_READY));
    assert(feed(&q,&b,4)==RTPF_RET_REJECTED);
    drain(&q,10,1,10);discard(&b);RtpfCleanupQueue(&q);
}
static void multi_loss(void) {
    RTP_FEC_QUEUE q;RtpfInitializeQueue(&q);
    for(unsigned j=0;j<3;j++) {
        Block b=block(30,j,2,100+j*TOTAL);
        assert(feed(&q,&b,2)==RTPF_RET_QUEUED_NOTHING_READY);
        duplicate(&q,&b,0);
        assert(feed(&q,&b,3)==RTPF_RET_QUEUED_NOTHING_READY);
        int r=feed(&q,&b,4); // Reconstruct missing data packet 1 using real parity.
        assert(r==(j==2?RTPF_RET_QUEUED_PACKETS_READY:RTPF_RET_QUEUED_NOTHING_READY));
        if(j<2)assert(!RtpfGetQueuedPacket(&q));
        discard(&b);
    }
    drain(&q,30,3,100);RtpfCleanupQueue(&q);
}
static void missing_block(void) {
    RTP_FEC_QUEUE q;RtpfInitializeQueue(&q);
    Block a=block(40,0,2,200),c=block(40,2,2,210);
    for(unsigned i=0;i<DATA;i++)feed(&q,&a,i);
    for(unsigned i=0;i<TOTAL;i++)assert(feed(&q,&c,i)==RTPF_RET_REJECTED);
    assert(!RtpfGetQueuedPacket(&q));
    Block next=block(41,0,0,220);
    for(unsigned i=0;i<DATA;i++)feed(&q,&next,i);
    drain(&q,41,1,220);discard(&a);discard(&c);discard(&next);RtpfCleanupQueue(&q);
}
static void failed_recovery(void) {
    RTP_FEC_QUEUE q;RtpfInitializeQueue(&q);
    Block a=block(50,0,0,300);
    feed(&q,&a,0);feed(&q,&a,2);feed(&q,&a,3);
    failRecovery=1;assert(feed(&q,&a,4)==RTPF_RET_QUEUED_NOTHING_READY);failRecovery=0;
    assert(!RtpfGetQueuedPacket(&q));
    Block next=block(51,0,0,310);
    for(unsigned i=0;i<DATA;i++)feed(&q,&next,i);
    drain(&q,51,1,310);discard(&a);discard(&next);RtpfCleanupQueue(&q);
}
static void wrap(void) {
    RTP_FEC_QUEUE q;RtpfInitializeQueue(&q);
    Block a=block(UINT32_MAX,0,0,65533);
    for(unsigned i=0;i<DATA;i++)feed(&q,&a,i);
    drain(&q,UINT32_MAX,1,65533);
    Block b=block(0,0,0,3);
    for(unsigned i=0;i<DATA;i++)feed(&q,&b,i);
    drain(&q,0,1,3);discard(&a);discard(&b);RtpfCleanupQueue(&q);
}
static void malformed(void) {
    RTP_FEC_QUEUE q;RtpfInitializeQueue(&q);Block a=block(60,0,0,400);
    PRTP_PACKET r=(PRTP_PACKET)a.p[0];
    assert(RtpfAddPacket(&q,r,8,(PRTPFEC_QUEUE_ENTRY)(a.p[0]+SIZE))==RTPF_RET_REJECTED);
    PNV_VIDEO_PACKET v=(PNV_VIDEO_PACKET)(a.p[0]+16);v->fecInfo=0;
    assert(feed(&q,&a,0)==RTPF_RET_REJECTED);
    discard(&a);RtpfCleanupQueue(&q);
}
int main(void) {
    single();multi_loss();missing_block();failed_recovery();wrap();malformed();
    puts("PASS: real FEC recovery, 3-block frames, reordering, duplicates, lost blocks, recovery failure, RTP/frame wrap, malformed input");
}
