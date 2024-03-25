from sklearn.metrics import confusion_matrix, roc_curve, auc, precision_recall_curve, accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
from typing import List, Dict, Any, Union
from abc import ABC, abstractmethod
from collections import namedtuple
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import pandas as pd
import numpy as np


class ModelEvaluator(ABC):
    @abstractmethod
    def evaluate_training(self, dataframe: Union[List[pd.DataFrame], pd.DataFrame]) -> Dict[str, Any]:
        pass

    @abstractmethod
    def evaluate(self, dataframe: Union[List[pd.DataFrame], pd.DataFrame]) -> Dict[str, Any]:
        pass


def get_labels_and_predictions(dataframe: pd.DataFrame, label_column: str, column_prefix: str = "predict_") -> pd.DataFrame:
    y_true = dataframe[label_column]
    y_pred = dataframe[f"{column_prefix}{label_column}"]
    return y_true, y_pred


def calculate_metrics(y_true, y_pred):
    # Calculate metrics
    accuracy = accuracy_score(y_true, y_pred)
    precision = precision_score(y_true, y_pred)
    recall = recall_score(y_true, y_pred)
    f1 = f1_score(y_true, y_pred)
    auc_roc = roc_auc_score(y_true, y_pred)

    return accuracy, precision, recall, f1, auc_roc


ConfusionMatrix = namedtuple('ConfusionMatrix', [
                             'true_positive', 'false_positive', 'true_negative', 'false_negative'])


def calculate_confusion_matrix_statistics(confusion_matrix: np.array) -> ConfusionMatrix:
    """ Takes a multi-class confusion matrix and returns the statistics for each class. 

    Parameters:
    -----------

    confusion_matrix: np.array
        A multi-class confusion matrix

    Returns:
    --------
    ConfusionMatrix
        A named tuple containing the statistics (TP, FP, TN, FN) for each class

    For more info see: https://stackoverflow.com/questions/48100173/how-to-get-precision-recall-and-f-measure-from-confusion-matrix-in-python
    """
    TP = np.diag(confusion_matrix)
    FP = np.sum(confusion_matrix, axis=0) - TP
    FN = np.sum(confusion_matrix, axis=1) - TP

    # True negatives
    num_classes = confusion_matrix.shape[0]
    TN = []
    for i in range(num_classes):
        temp = np.delete(confusion_matrix, i, axis=0)    # delete ith row
        temp = np.delete(temp, i, axis=1)
        TN.append(sum(sum(temp)))
    TN = np.array(TN)

    return ConfusionMatrix(TP, FP, TN, FN)


def precision_score(confusion_matrix: ConfusionMatrix) -> np.array:
    """ Calculate the precision score for each class. The precision is calculated
    as the number of true positives divided by the sum of true positives and false positives:

    precision = TP / (TP + FP)

    Parameters:
    -----------
    confusion_matrix: ConfusionMatrix
        A named tuple containing the statistics (TP, FP, TN, FN) for each class

    Returns:
    --------
    np.array
        An array of precision scores for each class. 
    """
    return confusion_matrix.true_positive / (confusion_matrix.true_positive + confusion_matrix.false_positive)


def recall_score(confusion_matrix: ConfusionMatrix) -> np.array:
    """ Calculate the recall score for each class. The recall
    is calculated as the number of true positives divided by the sum of true positives and false negatives:

    recall = TP / (TP + FN)

    Parameters:
    -----------
    confusion_matrix: ConfusionMatrix
        A named tuple containing the statistics (TP, FP, TN, FN) for each class

    Returns:
    --------
    np.array
        An array of recall scores for each class.   
    """
    return confusion_matrix.true_positive / (confusion_matrix.true_positive + confusion_matrix.false_negative)


def f1_score(confusion_matrix: ConfusionMatrix) -> np.array:
    """ Calculate the F1 score for each class. The F1 score is the harmonic mean of the precision and recall:

    F1 = 2 * (precision * recall) / (precision + recall)

    Parameters:
    -----------
    confusion_matrix: ConfusionMatrix
        A named tuple containing the statistics (TP, FP, TN, FN) for each class

    Returns:
    --------
    np.array
        An array of F1 scores for each class.
    """
    precision = precision_score(confusion_matrix)
    recall = recall_score(confusion_matrix)
    return 2 * (precision * recall) / (precision + recall)


def accuracy_score(confusion_matrix: ConfusionMatrix) -> np.array:
    """ Calculate the accuracy score for each class. The accuracy score is calculated as the sum of true positives and true negatives divided by the sum of true positives, true negatives, false positives, and false negatives:

    accuracy = (TP + TN) / (TP + TN + FP + FN)

    Parameters:
    -----------
    confusion_matrix: ConfusionMatrix
        A named tuple containing the statistics (TP, FP, TN, FN) for each class

    Returns:
    --------
    np.array
        An array of accuracy scores for each class.
    """
    return (confusion_matrix.true_positive + confusion_matrix.true_negative) / (confusion_matrix.true_positive + confusion_matrix.true_negative + confusion_matrix.false_positive + confusion_matrix.false_negative)


def save_metrics(accuracy, precision, recall, f1, auc_roc, output_path):
    # Save metrics to disk
    with open(os.path.join(output_path, 'evaluation_metrics.txt'), 'w') as f:
        f.write(
            f'Accuracy: {accuracy}\nPrecision: {precision}\nRecall: {recall}\nF1-score: {f1}\nAUC-ROC: {auc_roc}')


def plot_confusion_matrix(y_true, y_pred, output_path):
    # Plot and save confusion matrix
    cm = confusion_matrix(y_true, y_pred)
    plt.figure(figsize=(10, 7))
    sns.heatmap(cm, annot=True, fmt='d')
    plt.title('Confusion Matrix')
    plt.xlabel('Predicted')
    plt.ylabel('Actual')
    plt.savefig(os.path.join(output_path, 'confusion_matrix.png'))


def plot_roc_curve(y_true, y_pred, output_path):
    # Plot and save ROC curve
    fpr, tpr, _ = roc_curve(y_true, y_pred)
    auc_roc = auc(fpr, tpr)
    plt.figure(figsize=(10, 7))
    plt.plot(fpr, tpr, label='ROC curve (area = %0.2f)' % auc_roc)
    plt.plot([0, 1], [0, 1], 'k--')
    plt.xlim([0.0, 1.0])
    plt.ylim([0.0, 1.05])
    plt.xlabel('False Positive Rate')
    plt.ylabel('True Positive Rate')
    plt.title('Receiver Operating Characteristic')
    plt.legend(loc="lower right")
    plt.savefig(os.path.join(output_path, 'roc_curve.png'))


def plot_precision_recall_curve(y_true, y_pred, output_path):
    # Plot and save Precision-Recall curve
    precision, recall, _ = precision_recall_curve(y_true, y_pred)
    auc_score = auc(recall, precision)
    plt.figure(figsize=(10, 7))
    plt.plot(recall, precision,
             label='Precision-Recall curve (area = %0.2f)' % auc_score)
    plt.xlabel('Recall')
    plt.ylabel('Precision')
    plt.title('Precision-Recall Curve')
    plt.legend(loc="lower right")
    plt.savefig(os.path.join(output_path, 'precision_recall_curve.png'))


def evaluate(dataframe: pd.DataFrame, label_column: str, output_path: str, column_prefix: str = "predict_"):
    y_true, y_pred = get_labels_and_predictions(
        dataframe, label_column, column_prefix)
    accuracy, precision, recall, f1, auc_roc = calculate_metrics(
        y_true, y_pred)
    save_metrics(accuracy, precision, recall, f1, auc_roc, output_path)
    plot_confusion_matrix(y_true, y_pred, output_path)
    plot_roc_curve(y_true, y_pred, output_path)
    plot_precision_recall_curve(y_true, y_pred, output_path)
