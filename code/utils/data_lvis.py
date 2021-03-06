import os
from functools import partial

import numpy as np
import torch
from detectron2.data.build import build_detection_test_loader, build_detection_train_loader
from detectron2.data.dataset_mapper import DatasetMapper
from detectron2.structures.masks import BitMasks

if 'DETECTRON2_DATASETS' not in os.environ:
    print('Need to set DETECTRON2_DATASETS...')


# a callable which takes a sample (dict) from dataset and
# returns the format to be consumed by the model
def wrapper(d, default_m):
    d = default_m(d)
    """
    d has keys: file_name, height, width, image, instances, etc.
    """
    img = d['image'].cpu().numpy().transpose(1, 2, 0)
    img = torch.tensor(img).type(torch.float)
    if 'instances' not in d:
        d['image'] = img
        return d
    #img = cv2.resize(img, (h, w))  # .transpose(2, 0, 1)
    h, w = d['instances'].image_size
   
    raw_h, raw_w = d['instances'].image_size
    masks = BitMasks.from_polygon_masks(d['instances'].gt_masks, raw_h, raw_w).tensor.type(torch.uint8)
    masks_resized = np.zeros((masks.shape[0], h, w))
    for i in range(masks.shape[0]):
        masks_resized[i] = masks[i].cpu().numpy()
        #masks_resized[i] = cv2.resize(masks[i].cpu().numpy(), (w, h))
    gt_masks = torch.tensor(masks_resized).type(torch.bool)

    """
    num_gt_masks = gt_masks.shape[0]
    ground = np.zeros_like(gt_masks[0], dtype=np.uint8)

    for j in range(num_gt_masks):
        ground[gt_masks[j]] = j + 1
    print(gt_masks.shape, np.unique(ground))
    """
    foreground = gt_masks[0]
    for i in range(1, gt_masks.shape[0]):
        foreground |= gt_masks[i]
    d['image'] = img
    d['labels'] = gt_masks
    d['background'] = ~foreground
    return d


def get_lvis_train_dataloader(cfg):
    default_mapper = DatasetMapper(cfg, is_train=True)
    mapper = partial(wrapper, default_m=default_mapper)
    dl = build_detection_train_loader(cfg, mapper=mapper)
    return dl


def get_lvis_test_dataloader(cfg):
    default_mapper = DatasetMapper(cfg, is_train=False)
    mapper = partial(wrapper, default_m=default_mapper)
    dl = build_detection_test_loader(cfg, 'lvis_v0.5_val', mapper=mapper)
    return dl


class DataSetWrapper(object):
    def __init__(self,  batch_size, cfg, num_workers=6, **kwargs):
        self.cfg = cfg
        self.cfg.SOLVER.IMS_PER_BATCH = batch_size
        self.cfg.DATALOADER.NUM_WORKERS = num_workers

    def get_train_loader(self):
        return get_lvis_train_dataloader(self.cfg)
    
    def get_test_loader(self):
        return get_lvis_test_dataloader(self.cfg)

    def get_data_loaders(self):
        train_loader = get_lvis_train_dataloader(self.cfg)
        #valid_loader = None
        valid_loader = get_lvis_test_dataloader(self.cfg)
        return train_loader, valid_loader
