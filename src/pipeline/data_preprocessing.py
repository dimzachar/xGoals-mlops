import numpy as np
import xgboost as xgb
from prefect import task
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction import DictVectorizer


@task
def filter_and_transform_shot_data(data):
    """
    Filter the data to retain only shot events and perform necessary transformations.
    """

    print("Filtering and transforming shot data...")

    shot_df = data[data['subEventName'] == 'Shot'].copy()
    shot_df["X"] = shot_df['positions'].apply(
        lambda cell: (100 - cell[0]['x']) * 105 / 100
    )
    shot_df["Y"] = shot_df['positions'].apply(lambda cell: cell[0]['y'] * 68 / 100)
    shot_df["C"] = shot_df['positions'].apply(
        lambda cell: abs(cell[0]['y'] - 50) * 68 / 100
    )
    shot_df['distance_to_goal'] = np.sqrt(shot_df['X'] ** 2 + shot_df['C'] ** 2)
    shot_df['angle_to_goal'] = np.where(
        np.arctan(
            7.32
            * shot_df['X']
            / (shot_df['X'] ** 2 + shot_df['C'] ** 2 - (7.32 / 2) ** 2)
        )
        > 0,
        np.arctan(
            7.32
            * shot_df['X']
            / (shot_df['X'] ** 2 + shot_df['C'] ** 2 - (7.32 / 2) ** 2)
        ),
        np.arctan(
            7.32
            * shot_df['X']
            / (shot_df['X'] ** 2 + shot_df['C'] ** 2 - (7.32 / 2) ** 2)
        )
        + np.pi,
    )
    shot_df['is_goal'] = (
        shot_df['tags']
        .apply(lambda tags: any(tag['id'] == 101 for tag in tags))
        .astype(int)
    )

    print("Finished filtering and transforming shot data.")
    return shot_df[['distance_to_goal', 'angle_to_goal', 'is_goal']]


@task
def split_data(df):
    """Split the data into train, validation, and test sets."""

    print("Splitting data into train, validation, and test sets...")
    df_train_full, df_test = train_test_split(df, test_size=0.2, random_state=11)
    df_train, df_val = train_test_split(df_train_full, test_size=0.25, random_state=11)

    print("Data split successfully.")
    return df_train, df_val, df_test


@task
def preprocess_data(df_train, df_val, df_test):
    """Preprocess data by separating the target variable and converting to DMatrix."""

    print("Preprocessing data...")
    y_train, y_val, y_test = (
        df_train['is_goal'].values,
        df_val['is_goal'].values,
        df_test['is_goal'].values,
    )
    X_train, X_val, X_test = (
        df_train.drop(columns='is_goal'),
        df_val.drop(columns='is_goal'),
        df_test.drop(columns='is_goal'),
    )

    print("Vectorizing data...")

    dv = DictVectorizer(sparse=False)
    X_train, X_val, X_test = (
        dv.fit_transform(X_train.to_dict(orient='records')),
        dv.transform(X_val.to_dict(orient='records')),
        dv.transform(X_test.to_dict(orient='records')),
    )

    print("Data preprocessing completed.")
    return (
        xgb.DMatrix(X_train, label=y_train, feature_names=dv.feature_names_),
        xgb.DMatrix(X_val, label=y_val, feature_names=dv.feature_names_),
        xgb.DMatrix(X_test, label=y_test, feature_names=dv.feature_names_),
    )
