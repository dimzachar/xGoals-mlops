export KINESIS_STREAM_INPUT="stg_shot_events-mlops-xgoals"
export KINESIS_STREAM_OUTPUT="stg_shot_predictions-mlops-xgoals"

SHARD_ID=$(aws kinesis put-record  \
        --stream-name ${KINESIS_STREAM_INPUT}   \
        --partition-key 1  --cli-binary-format raw-in-base64-out  \
        --data '{"shot": {
            "angle_to_goal": 1.2, 
            "distance_to_goal": 5.1
        },
        "shot_id": 123}'  \
        --query 'ShardId'
    )