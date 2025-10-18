import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, Dataset
from torchvision import transforms
from PIL import Image
import timm
import os
import argparse
import json
from sklearn.model_selection import train_test_split

# --- Configuration ---
CONFIG = {
    "model_name": "xception",
    "image_size": 224,
    "batch_size": 32,
    "epochs": 10,
    "learning_rate": 1e-4,
    "num_workers": 4,
    "device": "cuda" if torch.cuda.is_available() else "cpu"
}

# --- Dataset Class ---
class DeepfakeDataset(Dataset):
    def __init__(self, file_paths, labels, transform=None):
        self.file_paths = file_paths
        self.labels = labels
        self.transform = transform

    def __len__(self):
        return len(self.file_paths)

    def __getitem__(self, idx):
        img_path = self.file_paths[idx]
        image = Image.open(img_path).convert("RGB")
        label = self.labels[idx]

        if self.transform:
            image = self.transform(image)

        return image, torch.tensor(label, dtype=torch.long)

# --- Data Preparation ---
def prepare_data(dataset_path):
    """Prepare file paths and labels from the dataset directory."""
    print(f"📁 Loading data from: {dataset_path}")
    # This is a placeholder. You need to adapt this to your dataset's structure.
    # Example for a simple structure:
    # dataset/
    #   real/
    #     img1.png, ...
    #   fake/
    #     img1.png, ...
    real_path = os.path.join(dataset_path, 'real')
    fake_path = os.path.join(dataset_path, 'fake')

    if not os.path.exists(real_path) or not os.path.exists(fake_path):
        raise FileNotFoundError(
            f"Dataset structure not found. Expected 'real' and 'fake' subdirectories in {dataset_path}"
        )

    real_files = [os.path.join(real_path, f) for f in os.listdir(real_path)]
    fake_files = [os.path.join(fake_path, f) for f in os.listdir(fake_path)]

    files = real_files + fake_files
    # 1 for REAL, 0 for FAKE
    labels = [1] * len(real_files) + [0] * len(fake_files)

    # Create train/validation split
    train_files, val_files, train_labels, val_labels = train_test_split(
        files, labels, test_size=0.2, random_state=42, stratify=labels
    )
    print(f"Found {len(files)} images. Split: {len(train_files)} train, {len(val_files)} validation.")
    return train_files, val_files, train_labels, val_labels

# --- Training Loop ---
def train_model(args):
    print("🚀 Starting Fine-Tuning Process...")
    print(f"Configuration: {json.dumps(CONFIG, indent=2)}")

    # Data transformations
    data_transforms = {
        'train': transforms.Compose([
            transforms.Resize((CONFIG['image_size'], CONFIG['image_size'])),
            transforms.RandomHorizontalFlip(),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
        ]),
        'val': transforms.Compose([
            transforms.Resize((CONFIG['image_size'], CONFIG['image_size'])),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
        ]),
    }

    # Prepare datasets and dataloaders
    train_files, val_files, train_labels, val_labels = prepare_data(args.dataset_path)
    train_dataset = DeepfakeDataset(train_files, train_labels, transform=data_transforms['train'])
    val_dataset = DeepfakeDataset(val_files, val_labels, transform=data_transforms['val'])

    train_loader = DataLoader(train_dataset, batch_size=CONFIG['batch_size'], shuffle=True, num_workers=CONFIG['num_workers'])
    val_loader = DataLoader(val_dataset, batch_size=CONFIG['batch_size'], shuffle=False, num_workers=CONFIG['num_workers'])

    # Load model
    model = timm.create_model(CONFIG['model_name'], pretrained=True, num_classes=2)
    model.to(CONFIG['device'])

    # Loss function and optimizer
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.AdamW(model.parameters(), lr=CONFIG['learning_rate'])
    scheduler = optim.lr_scheduler.StepLR(optimizer, step_size=5, gamma=0.1)

    best_acc = 0.0

    # Training and validation loop
    for epoch in range(CONFIG['epochs']):
        print(f"\n--- Epoch {epoch + 1}/{CONFIG['epochs']} ---")

        # Training phase
        model.train()
        running_loss = 0.0
        running_corrects = 0
        for inputs, labels in train_loader:
            inputs = inputs.to(CONFIG['device'])
            labels = labels.to(CONFIG['device'])

            optimizer.zero_grad()
            outputs = model(inputs)
            _, preds = torch.max(outputs, 1)
            loss = criterion(outputs, labels)

            loss.backward()
            optimizer.step()

            running_loss += loss.item() * inputs.size(0)
            running_corrects += torch.sum(preds == labels.data)
        
        epoch_loss = running_loss / len(train_dataset)
        epoch_acc = running_corrects.double() / len(train_dataset)
        print(f"Train Loss: {epoch_loss:.4f} Acc: {epoch_acc:.4f}")

        # Validation phase
        model.eval()
        val_loss = 0.0
        val_corrects = 0
        with torch.no_grad():
            for inputs, labels in val_loader:
                inputs = inputs.to(CONFIG['device'])
                labels = labels.to(CONFIG['device'])

                outputs = model(inputs)
                _, preds = torch.max(outputs, 1)
                loss = criterion(outputs, labels)

                val_loss += loss.item() * inputs.size(0)
                val_corrects += torch.sum(preds == labels.data)

        val_epoch_loss = val_loss / len(val_dataset)
        val_epoch_acc = val_corrects.double() / len(val_dataset)
        print(f"Val Loss: {val_epoch_loss:.4f} Acc: {val_epoch_acc:.4f}")

        # Save the best model
        if val_epoch_acc > best_acc:
            best_acc = val_epoch_acc
            print(f"✅ New best model found! Saving to best_model.pth")
            torch.save(model.state_dict(), 'best_model.pth')
        
        scheduler.step()

    print("\n🎉 Training complete!")
    print(f"Best Validation Accuracy: {best_acc:.4f}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Fine-tune a deepfake detection model.')
    parser.add_argument('--dataset_path', type=str, required=True, help='Path to the dataset directory.')
    args = parser.parse_args()
    train_model(args)
