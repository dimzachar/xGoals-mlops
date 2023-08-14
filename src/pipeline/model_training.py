import mlflow
import xgboost as xgb
from prefect import task
from hyperopt import STATUS_OK, Trials, hp, tpe, fmin, space_eval
from hyperopt.pyll import scope
from sklearn.metrics import roc_auc_score


@task(log_prints=True)
def hyperopt_train(dtrain, dval):
    """Use Hyperopt to optimize XGBoost hyperparameters."""

    def objective(params):
        """Objective function for Hyperopt's fmin function."""
        print(f"Training with params: {params}")

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

            # Predict on validation data and calculate the AUC
            y_val_pred = booster.predict(dval)
            auc = roc_auc_score(dval.get_label(), y_val_pred)
            print(f"Evaluation AUC: {auc}")

            # Log AUC as a metric in MLflow
            mlflow.log_metric("auc", auc)

            # Log the trained model to MLflow
            mlflow.xgboost.log_model(booster, artifact_path="model")

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
        max_evals=5,
        trials=trials,
    )
    best_auc = max(trial['result']['auc_value'] for trial in trials.trials)

    # Log the best AUC achieved during hyperparameter optimization
    print(f"Best AUC achieved during optimization: {best_auc}")

    # Extract the optimal parameters and the run_id of the best model
    optimal_params = space_eval(search_space, best_result)

    # After the hyperparameter optimization
    client = mlflow.tracking.MlflowClient()
    experiment_id = client.get_experiment_by_name("xgoals-experiment").experiment_id
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

    return optimal_params, best_run_id
