# ⚡ PyTorch Deep Learning Neural Vector Reranker

## Overview
Owlbearag features a built-in neural vector similarity engine powered by PyTorch (`torch.nn.Module`). It uses CUDA float16 Automatic Mixed Precision (AMP) to compute cosine similarity matrices between query vectors and document chunk embeddings.

## Technical Architecture
- **Embedding Projection**: Projects document token IDs to a dense vector space (`embed_dim=128`).
- **Cosine Matrix Calculation**: Computes pairwise cosine similarity via `torch.nn.functional.cosine_similarity()`.
- **Hardware Acceleration**: Automatic fallback between `cuda` GPU acceleration and `cpu` execution.

```python
import torch
import torch.nn as nn
import torch.nn.functional as F

class PyTorchNeuralReranker(nn.Module):
    def __init__(self, vocab_size=5000, embed_dim=128):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, embed_dim, padding_idx=0)
        self.proj = nn.Linear(embed_dim, embed_dim)

    def forward(self, token_tensor):
        embeds = self.embedding(token_tensor)
        pooled = embeds.mean(dim=1)
        return F.normalize(self.proj(pooled), p=2, dim=1)
```
