import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score, accuracy_score, f1_score, roc_auc_score
import xgboost as xgb
from sklearn.linear_model import Ridge

def train_test_split_data(X, y, test_size=0.2, random_state=42):
    """데이터 분할"""
    return train_test_split(X, y, test_size=test_size, random_state=random_state)

def apply_smote(X_train, y_train):
    """
    SMOTE 적용 (훈련 세트만)
    ⚠️ 문제점 수정 필요: 원본은 전체 데이터에 적용 후 분할했음
    """
    from imblearn.over_sampling import SMOTE
    X_resampled, y_resampled = SMOTE(random_state=42).fit_resample(X_train, y_train)
    return X_resampled, y_resampled

def train_xgboost(X_train, y_train):
    """
    XGBoost 학습 (강력한 정규화)
    📌 향후: 정규화 파라미터 조정해 79~80% 정확도 달성
    """
    model = xgb.XGBRegressor(
        n_estimators=10,
        learning_rate=0.01,
        max_depth=2,
        subsample=0.5,
        colsample_bytree=0.5,
        reg_alpha=10.0,
        reg_lambda=10.0,
        random_state=42
    )
    model.fit(X_train, y_train)
    return model

def train_baseline(X_train, y_train):
    """베이스라인 (Ridge)"""
    baseline = Ridge(alpha=10.0, random_state=42)
    baseline.fit(X_train, y_train)
    return baseline

def evaluate_model(model, X_test, y_test):
    """모델 평가"""
    y_pred = model.predict(X_test)
    y_pred_class = (y_pred >= 0.5).astype(int)
    y_test_class = (y_test >= 0.5).astype(int)
    
    return {
        'R2': r2_score(y_test, y_pred),
        'MSE': mean_squared_error(y_test, y_pred),
        'Accuracy': accuracy_score(y_test_class, y_pred_class),
        'F1': f1_score(y_test_class, y_pred_class),
        'AUC': roc_auc_score(y_test_class, y_pred)
    }
