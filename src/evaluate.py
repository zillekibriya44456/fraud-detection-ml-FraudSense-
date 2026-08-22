import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import (
    classification_report, 
    confusion_matrix, 
    roc_auc_score, 
    average_precision_score,
    precision_recall_curve
)

def evaluate_model(y_true, y_pred, y_prob=None, model_name="Model"):
    """
    Evaluates a model using precision, recall, f1, and prints a classification report.
    Also plots the confusion matrix and PR Curve if probabilities are provided.
    """
    print(f"--- Evaluation for {model_name} ---")
    print(classification_report(y_true, y_pred))
    
    if y_prob is not None:
        roc_auc = roc_auc_score(y_true, y_prob)
        pr_auc = average_precision_score(y_true, y_prob)
        print(f"ROC-AUC: {roc_auc:.4f}")
        print(f"PR-AUC:  {pr_auc:.4f}")
        
    cm = confusion_matrix(y_true, y_pred)
    
    fig, axes = plt.subplots(1, 2 if y_prob is not None else 1, figsize=(12, 5))
    
    # Plot Confusion Matrix
    ax_cm = axes[0] if y_prob is not None else axes
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', ax=ax_cm)
    ax_cm.set_title(f"Confusion Matrix - {model_name}")
    ax_cm.set_xlabel("Predicted")
    ax_cm.set_ylabel("Actual")
    
    # Plot PR Curve
    if y_prob is not None:
        precision, recall, _ = precision_recall_curve(y_true, y_prob)
        ax_pr = axes[1]
        ax_pr.plot(recall, precision, marker='.', label=model_name)
        ax_pr.set_title(f"Precision-Recall Curve (PR-AUC: {pr_auc:.4f})")
        ax_pr.set_xlabel('Recall')
        ax_pr.set_ylabel('Precision')
        ax_pr.legend()
        
    plt.tight_layout()
    plt.show()
    
    return {
        "pr_auc": pr_auc if y_prob is not None else None,
        "roc_auc": roc_auc if y_prob is not None else None
    }
