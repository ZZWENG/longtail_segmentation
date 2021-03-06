import torch.nn as nn
import torch.nn.functional as F
import torchvision.models as models


class ResNet(nn.Module):
    def __init__(self, base_model, out_dim, pretrained=False, freeze_base=False):
        super(ResNet, self).__init__()
        self.resnet_dict = {"resnet18": models.resnet18(pretrained=pretrained),
                            "resnet50": models.resnet50(pretrained=pretrained),
                            "resnet101": models.resnet101(pretrained=pretrained)}

        base_model = self._get_basemodel(base_model)
        num_ftrs = base_model.fc.in_features
        self.features = nn.Sequential(*list(base_model.children())[:-1])
        if freeze_base:
            for p in self.features.parameters():
                p.requires_grad = False
        # projection MLP
        self.l1 = nn.Linear(num_ftrs, num_ftrs)
        self.l2 = nn.Linear(num_ftrs, out_dim)

    def _get_basemodel(self, model_name):
        try:
            model = self.resnet_dict[model_name]
            print("Feature extractor:", model_name)
            return model
        except:
            raise ("Invalid model name. Check the config file and pass one of: resnet18 or resnet50")

    def forward(self, x):
        try:
            h = self.features(x)
        except:
            print(x.shape)
            h = self.features(x)
        h = h.squeeze()

        x = self.l1(h)
        x = F.relu(x)
        x = self.l2(x)
        return h, x
