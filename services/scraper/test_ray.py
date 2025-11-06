import ray

ray.init()

@ray.remote
def hello():
    return "Ray is working!"

print(ray.get(hello.remote()))
