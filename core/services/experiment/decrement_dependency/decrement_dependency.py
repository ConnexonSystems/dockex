import sys
import redis
import json

from core.languages.python.base.ListPopService import ListPopService
from core.experiment.helpers.ready_jobs_dict_to_key import ready_jobs_dict_to_key
from core.experiment.helpers.get_module_stats_keys import get_module_stats_keys


class DecrementDependency(ListPopService):
    def __init__(self, input_args):
        super().__init__(input_args, "decrement_dependency")

        self.ip_address = self.redis_client.get("ip_address")
        self.redis_port = self.redis_client.get("redis_port")

        self.dependency_counts_db = redis.StrictRedis(
            host=self.ip_address, port=self.redis_port, db=2
        )
        self.job_lookup_db = redis.StrictRedis(
            host=self.ip_address, port=self.redis_port, db=3
        )

    def pop_callback(self, dependent_job_name):

        # check the dependent job dependency count
        if (
            json.loads(
                self.dependency_counts_db.get(dependent_job_name).decode("utf-8")
            )
            > 1
        ):
            # if more than one dependency left, decrement the count
            print("DECREMENTING DEPENDENCY")
            self.dependency_counts_db.decr(dependent_job_name)

        # if it's 1, time to launch the job
        else:
            print("PUSHING TO READY")
            # get the job config
            temp_job_params = json.loads(
                self.job_lookup_db.get(dependent_job_name).decode("utf-8")
            )
            temp_stats_keys = get_module_stats_keys(temp_job_params["module_name"])

            # update the progress counts on ExperimentStager
            # this is pending to ready
            # if not self.job_config['skip_input_pathnames_check']:
            self.redis_client.strict_redis.decr("num_pending_jobs")
            self.redis_client.strict_redis.decr(temp_stats_keys["num_pending_jobs"])
            self.redis_client.strict_redis.incr("num_ready_jobs")
            self.redis_client.strict_redis.incr(temp_stats_keys["num_ready_jobs"])

            # update_pipeline = self.experiment_manager.strict_redis.pipeline()
            # update_pipeline.decr('num_pending_jobs')
            # update_pipeline.decr((job_command + '_num_pending_jobs'))
            # update_pipeline.incr('num_ready_jobs')
            # update_pipeline.incr((job_command + '_num_ready_jobs'))
            # update_pipeline.execute()

            # add it to the ready list
            self.redis_client.rpush(
                ready_jobs_dict_to_key(temp_job_params), temp_job_params
            )


if __name__ == "__main__":
    DecrementDependency(sys.argv).run()
