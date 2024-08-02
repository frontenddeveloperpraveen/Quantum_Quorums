import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.metrics import accuracy_score, mean_squared_error
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor
from sklearn.ensemble import BaggingClassifier, RandomForestClassifier, AdaBoostClassifier, StackingClassifier, RandomForestRegressor
from xgboost import XGBClassifier, XGBRegressor
from sklearn.neural_network import MLPClassifier, MLPRegressor
from sklearn.linear_model import LogisticRegression, LinearRegression
import pickle
import math
import random,os
from django.conf import settings
def load_dataset(file_path):
    if file_path.endswith('.csv'):
        df = pd.read_csv(file_path)
    elif file_path.endswith(('.xls', '.xlsx')):
        df = pd.read_excel(file_path)
    else:
        raise ValueError("Unsupported file type")
    return df

def cleanse_data(df, target_column):
    df = df.iloc[:5000, :10]
    
    if df[target_column].dtype == 'object':
        df[target_column].fillna(df[target_column].mode()[0], inplace=True)
    else:
        df[target_column].fillna(df[target_column].mean(), inplace=True)
    
    
    for column in df.columns:
        if df[column].dtype == 'object':
            df[column].fillna(df[column].mode()[0], inplace=True)
        else:
            df[column].fillna(df[column].mean(), inplace=True)
    
    for column in df.select_dtypes(include=['object']).columns:
        le = LabelEncoder()
        df[column] = le.fit_transform(df[column])
    
    scaler = StandardScaler()
    df[df.columns] = scaler.fit_transform(df[df.columns])
    
    return df

def bin_continuous_target(df, target_column, bins):
    df[target_column], bin_edges = pd.cut(df[target_column], bins=bins, labels=False, retbins=True)
    return df, bin_edges

def train_classification_models(X_train, X_test, y_train, y_test):
    models = {
        'SVM': SVC(),
        'Decision Tree': DecisionTreeClassifier(),
        'Bagging': BaggingClassifier(estimator=DecisionTreeClassifier(), n_estimators=10, random_state=42),
        'Random Forest': RandomForestClassifier(),
        'ADA Boost': AdaBoostClassifier(),
        'XGBoost': XGBClassifier(eval_metric='logloss'),
        'Stacking': StackingClassifier(estimators=[
            ('dt', DecisionTreeClassifier()),
            ('rf', RandomForestClassifier()),
            ('svm', SVC(probability=True))
        ], final_estimator=LogisticRegression()),
        'Neural Network': MLPClassifier(hidden_layer_sizes=(128, 64, 32), max_iter=500)
    }
    
    best_model = None
    best_accuracy = 0
    best_rmse = float('inf')
    best_model_name = None
    
    for name, model in models.items():
        try:
            model.fit(X_train, y_train)
            y_pred = model.predict(X_test)
            
            accuracy = accuracy_score(y_test, y_pred)
            rmse = math.sqrt(mean_squared_error(y_test, y_pred))
            
            print(f'{name} Accuracy: {accuracy}, RMSE: {rmse}')
            
            if accuracy > best_accuracy:
                best_accuracy = accuracy
                best_rmse = rmse
                best_model = model
                best_model_name = name
        except Exception as e:
            print(f'Error with {name}: {e}')
    
    return best_model, best_model_name, best_accuracy, best_rmse

def train_regression_models(X_train, X_test, y_train, y_test):
    models = {
        'Linear Regression': LinearRegression(),
        'Decision Tree Regressor': DecisionTreeRegressor(),
        'Random Forest Regressor': RandomForestRegressor(),
        'XGBoost Regressor': XGBRegressor(),
        'Neural Network Regressor': MLPRegressor(hidden_layer_sizes=(128, 64, 32), max_iter=500)
    } 
    
    best_model = None
    best_rmse = float('inf')
    best_model_name = None
    
    for name, model in models.items():
        try:
            model.fit(X_train, y_train)
            y_pred = model.predict(X_test)
            rmse = math.sqrt(mean_squared_error(y_test, y_pred))
            print(f'{name} RMSE: {rmse}')
            
            if rmse < best_rmse:
                best_rmse = rmse
                best_model = model
                best_model_name = name
        except Exception as e:
            print(f'Error with {name}: {e}')
    
    return best_model, best_model_name, best_rmse

def save_best_model(model):
    if not os.path.exists(settings.MEDIA_ROOT):
        os.makedirs(settings.MEDIA_ROOT)
    file_name = "Model-"+ str(random.randint(11111111111,999999999999)) +".pkl"
    file_path = os.path.join(settings.MEDIA_ROOT, file_name)
    with open(file_path, 'wb+') as f:
        pickle.dump(model, f)
    return settings.MEDIA_URL + file_name

def automl_tool(file_path, target_column, bins=10):
    df = load_dataset(file_path)
    df = cleanse_data(df, target_column)
    
    print("Cleansed Data:")
    print(df.head())
    
    if df[target_column].nunique() > 20: 
        is_classification = False
    else:
        is_classification = True

    if is_classification:
        df, bin_edges = bin_continuous_target(df, target_column, bins)
        
        X = df.drop(target_column, axis=1)
        y = df[target_column]
        
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        best_model, best_model_name, best_accuracy, best_rmse = train_classification_models(X_train, X_test, y_train, y_test)
    else:
        X = df.drop(target_column, axis=1)
        y = df[target_column]
        
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        best_model, best_model_name, best_rmse = train_regression_models(X_train, X_test, y_train, y_test)
        best_accuracy = None 
    
    fileloc = save_best_model(best_model)
    
    print(f"Best model: {best_model_name}")
    if best_accuracy is not None:
        print(f"Best model accuracy: {best_accuracy}")
    print(f"Best model RMSE: {best_rmse}")
    
    print("Best model saved as 'best_model.pkl'")
    return (best_model_name,best_accuracy,best_rmse,fileloc)

