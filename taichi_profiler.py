import subprocess
import matplotlib.pyplot as plt

def get_param_cost(arch='gpu', n_grid=32, n_particle=8192):
    p = subprocess.check_output(['python', 'taichi_benchmark.py', str(arch), str(n_grid), str(n_particle)], shell=False)
    output = p.decode()
    lines = output.split('\n')
    # extract lines
    profiler_info = lines[7:16]
    profiler_info[0].split()
    kernel_lines = [(line.split()[7],line.split()[8]) for line in profiler_info if line.split()[4]=='2500x']
    avg_substep = 0
    max_substep = 0
    for kernel_avg, kernel_max in kernel_lines:
        avg_substep += float(kernel_avg)
        max_substep += float(kernel_max)
    return (avg_substep, max_substep)

def profile_particle():
    avg_costs = []
    max_costs = []
    n_particle_range = [2000 + 3000 * i for i in range(10)]
    for i in n_particle_range:
        avg_cost, max_cost = get_param_cost('gpu', 32, i)
        avg_costs.append(avg_cost)
        max_costs.append(max_cost)
        print("avg cost at particle {0} is {1}".format(i, avg_cost))

    plt.style.use('ggplot')
    plt.plot(n_particle_range, avg_costs)
    plt.title("Substep cost for mpm3d at ngrid=32")
    plt.xlabel("particle count")
    plt.ylabel("time(ms)")
    plt.show()

def profile_ngrid():
    avg_costs = []
    max_costs = []
    n_grid = [ pow(2, i)*16 for i in range(5)]
    for i in n_grid:
        avg_cost, max_cost = get_param_cost('gpu', i, 8192)
        avg_costs.append(avg_cost)
        max_costs.append(max_cost)
        print("avg cost at grid {0} is {1}".format(i, avg_cost))

    plt.style.use('ggplot')
    plt.plot(n_grid, avg_costs)
    plt.title("Substep cost for mpm3d at nparticle=8192")
    plt.xlabel("n grid")
    plt.ylabel("time(ms)")
    plt.show()

profile_particle()
profile_ngrid()