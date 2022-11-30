import os
import cv2
import glob
import numpy as np
from utils.func import *


def compute_global_errors(gt, pred):
    gt=gt[gt!=0]
    pred=pred[pred!=0]
    
    mask2 = gt > 1e-8
    mask3 = pred > 1e-8
    mask2 = mask2 & mask3
    
    gt = gt[mask2]
    pred = pred[mask2]
    
    #compute global relative errors
    thresh = np.maximum((gt / pred), (pred / gt))
    thr1 = (thresh < 1.25   ).mean()
    thr2 = (thresh < 1.25 ** 2).mean()
    rmse = (gt - pred) ** 2
    rmse = np.sqrt(rmse.mean())
    log10 = np.mean(np.abs(np.log10(gt) - np.log10(pred)))
    sq_rel = np.mean(((gt - pred)**2) / gt)

    return sq_rel, rmse, log10, thr1, thr2


class multiscopic():
    def __init__(self, path= './datasets/multiscopic/test_b'):
        self.input_path = path
        self.num = 500
        self.rms     = np.zeros(self.num, np.float32)
        self.log10   = np.zeros(self.num, np.float32)
        self.sq_rel  = np.zeros(self.num, np.float32)
        self.thr1    = np.zeros(self.num, np.float32)
        self.thr2    = np.zeros(self.num, np.float32)
        self.d3r_rel    = np.zeros(self.num, np.float32)
        self.ord_rel    = np.zeros(self.num, np.float32)
        self.img_names = glob.glob(os.path.join(self.input_path, "*"))
        self.img_names.sort()
        self.index = -1
        self.dex = 0
        

    def getitem(self):
        if self.dex == 0:
            self.img_loc = self.img_names.pop()
        img = cv2.imread(self.img_loc+f'/view{self.dex}.png')[:, :, ::-1]
        dep_loc = self.img_loc + f'/disp{self.dex}.png'
        depth = cv2.imread(dep_loc)[:, :, 0]
        
        val_mask = np.ones_like(depth)
        val_mask[depth==0]=0
        depth = depth.max() - depth
        
        self.dex = (self.dex + 1) % 5
        self.index += 1
        return img, depth, val_mask

    def compute_error(self, target, depth, val_mask):
        target = target.cpu().numpy().squeeze()
        h, w = depth.shape
        val_mask = cv2.resize(val_mask, (w, h))
        target = cv2.resize(target, (w, h))
        target = shift_scale(target.astype('float64'), depth.astype('float64'), val_mask)

        pred = target.copy()
        pred_org = pred.copy()
        pred_invalid = pred.copy()
        pred_invalid[pred_invalid!=0]=1
        mask_missing = depth.copy() # Mask for further missing depth values in depth map
        mask_missing[mask_missing!=0]=1
        mask_valid = mask_missing*pred_invalid # Combine masks
        depth_valid = depth*mask_valid 
        gt = depth_valid
        gt_vec = gt.flatten()
        pred = pred*mask_valid 
        pred_vec = pred.flatten()
        self.sq_rel[self.index], self.rms[self.index], self.log10[self.index], self.thr1[self.index], self.thr2[self.index] = compute_global_errors(gt_vec,pred_vec)
