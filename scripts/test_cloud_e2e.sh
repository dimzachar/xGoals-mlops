export KINESIS_STREAM_INPUT="prod_shot_events-mlops-xgoals"
export KINESIS_STREAM_OUTPUT="prod_shot_predictions-mlops-xgoals"

SHARD_ID=$(aws kinesis put-record  \
        --stream-name ${KINESIS_STREAM_INPUT}   \
        --data '{"shot": {
            "angle_to_goal": 1.2, 
            "distance_to_goal": 5.1
        },
        "shot_id": 123}'  \
        --query 'ShardId'
    )