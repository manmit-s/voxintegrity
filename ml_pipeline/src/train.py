import yaml
import torch
from torch.utils.data import DataLoader
from src.data_loader import VoiceDataset
from src.architecture import VaaniKavachNet

def train(config_path='configs/hyperparams.yaml'):
    with open(config_path) as f:
        cfg = yaml.safe_load(f)
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model = VaaniKavachNet().to(device)
    print(f"Training on {device} with config {cfg}")
    # TODO: training loop
    return model

if __name__ == '__main__':
    train()
