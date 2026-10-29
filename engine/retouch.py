import cv2,numpy as np,sys
src,dst=sys.argv[1:3]
im=cv2.imread(src,cv2.IMREAD_UNCHANGED);rgb=im[:,:,:3].astype(np.float32);a=im[:,:,3]
# 1) skin smoothing: edge-preserving blur blended (keeps eyes/beard edges)
sm=cv2.bilateralFilter(im[:,:,:3],0,38,9).astype(np.float32)
sm=cv2.bilateralFilter(sm.astype(np.uint8),0,30,6).astype(np.float32)
# skin mask via YCrCb
ycc=cv2.cvtColor(im[:,:,:3],cv2.COLOR_BGR2YCrCb)
skin=cv2.inRange(ycc,(40,135,85),(255,180,135)).astype(np.float32)/255
skin=cv2.GaussianBlur(skin,(0,0),6)[...,None]
out=rgb*(1-.7*skin)+sm*(.7*skin)
# 2) lift shadows / soft light in LAB
lab=cv2.cvtColor(np.clip(out,0,255).astype(np.uint8),cv2.COLOR_BGR2LAB).astype(np.float32)
L=lab[:,:,0]/255;L=np.power(L,0.78);L=L+0.06*np.sin(np.pi*L)  # gamma + midtone boost
lab[:,:,0]=np.clip(L*255,0,255)
# 3) warmth & slight de-redden: a(red)-2, b(yellow)+4
lab[:,:,1]+=1.5;lab[:,:,2]+=3
out=cv2.cvtColor(np.clip(lab,0,255).astype(np.uint8),cv2.COLOR_LAB2BGR).astype(np.float32)
# 4) clarity/sharpen (unsharp) mainly outside skin
bl=cv2.GaussianBlur(out,(0,0),2.0);sh=out+0.6*(out-bl)
out=sh*(1-skin*.6)+out*(skin*.6)
# 5) gentle vibrance
hsv=cv2.cvtColor(np.clip(out,0,255).astype(np.uint8),cv2.COLOR_BGR2HSV).astype(np.float32)
hsv[:,:,1]=np.clip(hsv[:,:,1]*1.06,0,255)
out=cv2.cvtColor(hsv.astype(np.uint8),cv2.COLOR_HSV2BGR)
res=np.dstack([out,a]);cv2.imwrite(dst,res)
