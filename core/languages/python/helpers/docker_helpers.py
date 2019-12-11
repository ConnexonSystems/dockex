import docker
import os


def print_docker_logs(logs):
    for line in logs:
        if "stream" in line:
            print(line["stream"])
        elif "error" in line:
            print(line["error"])
        else:
            print(line)


def safe_remove_container(docker_client, container_name, force=False):
    matching_container_list = docker_client.containers.list(
        all=True, filters={"name": f"^/{container_name}$"}
    )
    if len(matching_container_list) > 0:
        matching_container_list[0].remove(force=force)


def build_image(docker_client, build_kwargs_dict, print_build_logs=False):
    try:
        image, logs = docker_client.images.build(**build_kwargs_dict)

        if print_build_logs:
            print_docker_logs(logs)

    except docker.errors.BuildError as e:
        print_docker_logs(e.build_log)
        raise


def safe_run_container(docker_client, run_kwargs_dict):
    if "name" in run_kwargs_dict.keys():
        safe_remove_container(docker_client, run_kwargs_dict["name"], force=True)

    docker_client.containers.run(**run_kwargs_dict)


def native_safe_run_container(run_kwargs_dict):
    if "name" in run_kwargs_dict.keys():
        command = f"docker rm -f {run_kwargs_dict['name']} > /dev/null 2>&1; "

    else:
        command = ""

    command += f"docker run "
    # command += f"(docker run "

    if "detach" in run_kwargs_dict.keys():
        if run_kwargs_dict["detach"]:
            command += "-d "

    if "network_mode" in run_kwargs_dict.keys():
        if run_kwargs_dict["network_mode"] is not None:
            command += f"--network {run_kwargs_dict['network_mode']} "

    if "volumes" in run_kwargs_dict.keys():
        if run_kwargs_dict["volumes"] is not None:
            for volume_key in run_kwargs_dict["volumes"].keys():
                command += (
                    f"-v {volume_key}:{run_kwargs_dict['volumes'][volume_key]['bind']} "
                )

    if "enable_gpus" in run_kwargs_dict.keys():
        if run_kwargs_dict["enable_gpus"]:
            command += f"--gpus all "

    if "environment" in run_kwargs_dict.keys():
        if run_kwargs_dict["environment"] is not None:
            for env_key in run_kwargs_dict["environment"].keys():
                command += f"--env {env_key}={run_kwargs_dict['environment'][env_key]} "

    if "name" in run_kwargs_dict.keys():
        if run_kwargs_dict["name"] is not None:
            command += f"--name {run_kwargs_dict['name']} "

    command += f"{run_kwargs_dict['image']} "

    if "command" in run_kwargs_dict.keys():
        if run_kwargs_dict["command"] is not None and run_kwargs_dict["command"] != "":
            command += f"{run_kwargs_dict['command']} "

    # command += "> /dev/null 2>&1 &)"

    print(command)

    # run docker natively
    os.system(command)


def build_image_run_container(
    docker_client,
    build_kwargs_dict,
    run_kwargs_dict,
    print_build_logs=False,
    skip_build=False,
    native_run=False,
):
    if skip_build is not True:
        print("BUILDING IMAGE")
        build_image(docker_client, build_kwargs_dict, print_build_logs=print_build_logs)

    print("RUNNING CONTAINER")
    if native_run:
        native_safe_run_container(run_kwargs_dict)
    else:
        safe_run_container(docker_client, run_kwargs_dict)


def module_path_to_image_tag(module_path):
    return f"{module_path.replace('/', '_')}_image"


def build_project_modules(
    docker_client, module_paths_list, print_build_logs=False, redis_client=None
):
    PROJECT_ROOT_PATH = "/tmp/dockex/project"

    print("BUILDING PROJECT MODULES")
    if redis_client is not None:
        redis_client.set("status", "BUILDING PROJECT MODULES")

    for module_path in module_paths_list:
        print(f"BUILDING PROJECT MODULE: {module_path}")
        if redis_client is not None:
            redis_client.set("status", f"BUILDING PROJECT MODULE: {module_path}")

        build_image(
            docker_client,
            dict(
                path=PROJECT_ROOT_PATH,
                dockerfile=f"{PROJECT_ROOT_PATH}/{module_path}/Dockerfile",
                tag=module_path_to_image_tag(module_path),
            ),
            print_build_logs=print_build_logs,
        )

    print("PROJECT BUILD COMPLETE")
    if redis_client is not None:
        redis_client.set("status", "PROJECT BUILD COMPLETE")
