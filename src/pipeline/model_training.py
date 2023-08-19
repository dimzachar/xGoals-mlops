import os
from datetime import date

import mlflow
import pandas as pd
import xgboost as xgb
from prefect import task
from hyperopt import STATUS_OK, Trials, hp, tpe, fmin, space_eval
from hyperopt.pyll import scope
from sklearn.metrics import roc_auc_score
from prefect.artifacts import create_markdown_artifact


@task(log_prints=True)
def hyperopt_train(dtrain, dval):
    """Use Hyperopt to optimize XGBoost hyperparameters."""

    def objective(params):
        """Objective function for Hyperopt's fmin function."""
        print(f"Training with params: {params}")

        print(f"Number of rows in training data: {dtrain.num_row()}")
        print(f"Number of rows in validation data: {dval.num_row()}")

        # Start an MLflow run to keep track of experiments
        with mlflow.start_run():
            # Set metadata for the current run
            mlflow.set_tag("model", "xgboost")
            mlflow.log_params(params)

            # Train an XGBoost model
            booster = xgb.train(
                params=params,
                dtrain=dtrain,
                num_boost_round=1000,
                evals=[(dval, 'validation')],
                early_stopping_rounds=50,
                verbose_eval=False,
            )
            print(f"Number of boosting rounds: {booster.best_iteration}")

            y_train_pred = booster.predict(dtrain)
            print(f"First 10 predictions for training: {y_train_pred[:10]}")

            # Predict on validation data and calculate the AUC
            y_val_pred = booster.predict(dval)
            print(f"First 10 predictions for validation: {y_val_pred[:10]}")

            auc = roc_auc_score(dval.get_label(), y_val_pred)
            print(f"Evaluation AUC: {auc}")

            # Log AUC as a metric in MLflow
            mlflow.log_metric("auc", auc)

            # Log the trained model to MLflow
            mlflow.xgboost.log_model(booster, artifact_path="model")

            # Save the reference data (training data) as a Parquet file
            reference_data_path = "reference_data.parquet"
            dtrain_df = pd.DataFrame(dtrain.get_label(), columns=["label"])
            dtrain_df.to_parquet(reference_data_path)

            # Log the reference data to MLflow
            mlflow.log_artifact(reference_data_path, artifact_path="model")

            markdown__auc_report = f"""# AUC Report

            ## Summary

            XGoals Prediction

            ## AUC XGBoost Model

            | Region    | AUC |
            |:----------|-------:|
            | {date.today()} | {auc:.2f} |
            """

            create_markdown_artifact(
                key="xgoals-model-report", markdown=markdown__auc_report
            )

            # Return negative AUC as the objective function is minimized
        return {'loss': -auc, 'status': STATUS_OK, 'auc_value': auc}

    # Define the search space for the hyperparameters
    print("Setting up hyperparameter search space...")

    search_space = {
        'max_depth': scope.int(hp.quniform('max_depth', 4, 100, 1)),
        'learning_rate': hp.loguniform('learning_rate', -3, -1),
        'reg_alpha': hp.loguniform('reg_alpha', -6, -2),
        'reg_lambda': hp.loguniform('reg_lambda', -7, -2),
        'min_child_weight': hp.loguniform('min_child_weight', -1, 3),
        'objective': 'binary:logistic',
        'seed': 42,
    }

    # Use fmin function from Hyperopt to find the best hyperparameters
    print("Starting hyperparameter optimization...")
    trials = Trials()
    best_result = fmin(
        fn=objective,
        space=search_space,
        algo=tpe.suggest,
        max_evals=20,
        trials=trials,
    )
    best_auc = max(trial['result']['auc_value'] for trial in trials.trials)

    # Log the best AUC achieved during hyperparameter optimization
    print(f"Best AUC achieved during optimization: {best_auc}")

    # Extract the optimal parameters and the run_id of the best model
    optimal_params = space_eval(search_space, best_result)

    # After the hyperparameter optimization
    client = mlflow.tracking.MlflowClient()
    MLFLOW_EXPERIMENT_NAME = os.environ.get("MLFLOW_EXPERIMENT_NAME")
    if not MLFLOW_EXPERIMENT_NAME:
        raise ValueError("MLFLOW_EXPERIMENT_NAME environment variable is not set!")
    experiment_id = client.get_experiment_by_name(MLFLOW_EXPERIMENT_NAME).experiment_id

    best_run = client.search_runs(
        experiment_ids=[experiment_id],
        filter_string="",
        order_by=["metric.auc DESC"],
        max_results=1,
    )[0]
    best_run_id = best_run.info.run_id

    # Log the best run ID
    print(f"Best run ID: {best_run_id}")

    print(
        "Hyperparameter Optimization Complete. Optimal Parameters: "
        f"{optimal_params} with AUC: {best_auc}"
    )
    # Load the best model using the run ID
    # booster = load_model_from_mlflow(best_run_id)

    # print(f"Boosting rounds of loaded model: {booster.best_iteration}")

    return optimal_params, best_run_id


# def load_model_from_mlflow(run_id):
#     model_uri = f"runs:/{run_id}/model"
#     print(f"Loading model from: {model_uri}")
#     booster = mlflow.xgboost.load_model(model_uri)
#     return booster
