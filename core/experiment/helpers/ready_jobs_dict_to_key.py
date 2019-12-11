def ready_jobs_dict_to_key(ready_jobs_list_dict):
    ready_jobs_list_key = (
        "ready_jobs"
        + "_cpu_credits_"
        + str(ready_jobs_list_dict["cpu_credits"])
        + "_gpu_credits_"
        + str(ready_jobs_list_dict["gpu_credits"])
    )
    return ready_jobs_list_key
