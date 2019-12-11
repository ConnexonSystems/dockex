def get_module_stats_keys(module_name):
    return dict(
        num_total_jobs=f"{module_name}_num_total_jobs",
        num_pending_jobs=f"{module_name}_num_pending_jobs",
        num_ready_jobs=f"{module_name}_num_ready_jobs",
        num_running_jobs=f"{module_name}_num_running_jobs",
        num_complete_jobs=f"{module_name}_num_complete_jobs",
        num_error_jobs=f"{module_name}_num_error_jobs",
    )
