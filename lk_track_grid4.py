#!/usr/bin/env python

'''
Lucas-Kanade tracker
====================

Lucas-Kanade sparse optical flow demo. Uses goodFeaturesToTrack
for track initialization and back-tracking for match verification
between frames.

Revised to calculate positions and velocities for a grid of points JAB 2015

Usage
-----
lk_track.py [<video_source>]


Keys
----
ESC - exit
'''

import numpy as np
import cv2
import video
from common import anorm2, draw_str
from time import clock

lk_params = dict( winSize  = (15, 15),
                  maxLevel = 2,
                  criteria = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 0.03))

feature_params = dict( maxCorners = 500,
                       qualityLevel = 0.3,
                       minDistance = 7,
                       blockSize = 7 )

class App:
    def __init__(self, video_src):
        self.track_len = 10
        self.detect_interval = 5
        self.tracks = []
        self.cam = video.create_capture(video_src)
        self.frame_idx = 0
        self.screenx=700
        self.screeny=550

    def run(self):
        #Make the grid
        nptsx=10; nptsy=10;
        xgrid=np.linspace(10,self.screenx-10,nptsx)
        ygrid=np.linspace(10,self.screeny-10,nptsy)
        #Set up initial grid points for moving objects
        circlex,circley=np.meshgrid(xgrid,ygrid)
        circlex=np.reshape(circlex,-1)
        circley=np.reshape(circley,-1)
        self.p=np.reshape(zip(circlex,circley),[-1,1,2])
        circlevx=circlex*0.0;circlevy=circley*0.0;
        scale=0.5
        k=0.3
        damp=0.4
        maxv=20
        self.tracks=np.float32(self.p) #shape is N,1,2
        ret, frame = self.cam.read()
        frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        self.prev_gray = frame_gray #switch to the next image

        while True:
            ret, frame = self.cam.read()
            frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            vis = frame.copy()

            #Track current points
            img0, img1 = self.prev_gray, frame_gray #previous,current frames
            #Save old xy
            old_tracks=self.tracks.reshape(-1,2) #save old tracks
            #track positions
            p0 = np.float32([tr[-1] for tr in self.tracks]).reshape(-1, 1, 2) #latest points from current tracks recast for cv2
            p1, st, err = cv2.calcOpticalFlowPyrLK(img0, img1, p0, None, **lk_params) #track
            #Check if the detection is reversible
            p0r, st, err = cv2.calcOpticalFlowPyrLK(img1, img0, p1, None, **lk_params) #track current backwords
            d = abs(p0-p0r).reshape(-1, 2).max(-1) #
            good = d < 1 #reversibility flag

            #Initialize variables
            new_tracks = []
            new_veloc = []
            new_circles=[]
            new_circlevx=[]; new_circlevy=[]
                
            #Calculate velocities and store new coordinates
            for (xold, yold), (xnew, ynew),good_flag in zip(self.tracks.reshape(-1,2), p1.reshape(-1, 2),good): #tracks,new po  
                if good_flag: #reversibility flag, doesn't seem to do much
                    vex=xnew-xold; vey=ynew-yold
                    #maximum values
                    if vex>maxv:
                        vex=maxv
                    if vey>maxv:
                        vey=maxv
                    ve=(vex,vey) #velocity

                else:
                    ve=(0.0,0.0)
                            
                #tr=(xnew,ynew) #position 
                #new_tracks.append(tr) #add the updated track to the tracks (for deleting irreversible ones)
                new_veloc.append(ve) #add the updated velocity

            #self.tracks = np.reshape(new_tracks,[-1,1,2])
                
            #UPDATE CIRCLE POSITION
            for cvx,cvy,(cx,cy),(ox,oy),(nvx,nvy) in zip(circlevx,circlevy,self.tracks.reshape(-1,2),self.p.reshape(-1,2),new_veloc):
                #(cvx,cvy)=(cvx+(nvx+np.sign(ox-cx)*(ox-cx)**2)*scale,cvy+(nvy+np.sign(oy-cy)*(oy-cy)**2)*scale) #FIXME
                (svx,svy)=((ox-cx)*k,(oy-cy)*k) #spring acceleration
                print svx,svy
                #(cvx,cvy)=(cvx+(nvx)*scale-svx,cvy+(nvy)*scale-svy) #spring acceleration and image force
                (cvx,cvy)=(cvx+nvx*scale-cvx*damp+svx,cvy+nvy*scale-cvy*damp+svy) #spring acceleration and image force
                #(cvx,cvy)=(0.0,0.0)
                #(cvx,cvy)=(cvx-cvx*damp,cvy-cvy*damp) #damping force
                (cx,cy)=(cx+cvx,cy+cvy)
                nc=(cx,cy)
                #add values to the list
                new_circles.append(nc) 
                new_circlevx=np.append(new_circlevx,cvx); new_circlevy=np.append(new_circlevy,cvy)                    #(cx,cy)=(np.mod(cx+np.sign(cx)*cvx**2,self.screenx),np.mod(cy+np.sign(cy)*cvy**2,self.screeny))
                cv2.circle(vis, (np.int32(cx), np.int32(cy)), 10, (0, 255, 0), 0)#-1)
            self.tracks = np.reshape(new_circles,[-1,1,2])
            circlevy=new_circlevy; circlevx=new_circlevx;
            print self.p[34],new_circles[34],circlevx[34]
            #draw_str(vis, (20, 20), 'velocity x,y: %f %f, position x,y: %f %f' % (circlex[55], circley[55],circlevx[55],circlevy[55])) #write average velocity #NEWs
            cv2.imshow('lk_track', vis) #show the overlay of lines/circles
            self.prev_gray = frame_gray #switch to the next image

	       #Break key
            ch = 0xFF & cv2.waitKey(1)
            if ch == 27:
                break

def main():
    import sys
    try:
        video_src = sys.argv[1]
    except:
        video_src = 0

    print __doc__
    App(video_src).run()
    cv2.destroyAllWindows()

if __name__ == '__main__':
    main()
