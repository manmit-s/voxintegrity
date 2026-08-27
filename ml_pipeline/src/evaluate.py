import torch
from sklearn.metrics import accuracy_score, confusion_matrix, classification_report

def evaluate(model, dataloader, device='cpu'):
    model.eval()
    preds, labels = [], []
    with torch.no_grad():
        for x, y in dataloader:
            x, y = x.to(device), y.to(device)
            out = model(x)
            pred = out.argmax(dim=1)
            preds.extend(pred.cpu().numpy())
            labels.extend(y.cpu().numpy())
    acc = accuracy_score(labels, preds)
    print(f"Accuracy: {acc:.4f}")
    print(classification_report(labels, preds))
    print(confusion_matrix(labels, preds))
    return acc
