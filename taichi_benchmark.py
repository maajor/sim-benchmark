# originate from https://github.com/taichi-dev/taichi/blob/master/examples/mpm3d.py
export_file = ''  # use '/tmp/mpm3d.ply' for exporting result to disk
import sys
import taichi as ti
import numpy as np

def mpm3d(arch=ti.gpu, n_grid=32, n_particles=8192):
    ti.init(arch=arch, kernel_profiler=True)

    dim, steps, dt = 3, 25, 4e-4

    dx = 1 / n_grid

    p_rho = 1
    p_vol = (dx * 0.5)**2
    p_mass = p_vol * p_rho
    gravity = 9.8
    bound = 3
    E = 1

    x = ti.Vector.field(dim, float, n_particles)
    v = ti.Vector.field(dim, float, n_particles)
    C = ti.Matrix.field(dim, dim, float, n_particles)
    J = ti.field(float, n_particles)

    grid_v = ti.Vector.field(dim, float, (n_grid, ) * dim)
    grid_m = ti.field(float, (n_grid, ) * dim)

    neighbour = (3, ) * dim


    @ti.kernel
    def substep():
        for I in ti.grouped(grid_m):
            grid_v[I] = ti.zero(grid_v[I])
            grid_m[I] = 0
        ti.block_dim(n_grid)
        for p in x:
            Xp = x[p] / dx
            base = int(Xp - 0.5)
            fx = Xp - base
            w = [0.5 * (1.5 - fx)**2, 0.75 - (fx - 1)**2, 0.5 * (fx - 0.5)**2]
            stress = -dt * 4 * E * p_vol * (J[p] - 1) / dx**2
            affine = ti.Matrix.identity(float, dim) * stress + p_mass * C[p]
            for offset in ti.static(ti.grouped(ti.ndrange(*neighbour))):
                dpos = (offset - fx) * dx
                weight = 1.0
                for i in ti.static(range(dim)):
                    weight *= w[offset[i]][i]
                grid_v[base + offset] += weight * (p_mass * v[p] + affine @ dpos)
                grid_m[base + offset] += weight * p_mass
        for I in ti.grouped(grid_m):
            if grid_m[I] > 0:
                grid_v[I] /= grid_m[I]
            grid_v[I][1] -= dt * gravity
            cond = I < bound and grid_v[I] < 0 or I > n_grid - bound and grid_v[
                I] > 0
            grid_v[I] = 0 if cond else grid_v[I]
        ti.block_dim(n_grid)
        for p in x:
            Xp = x[p] / dx
            base = int(Xp - 0.5)
            fx = Xp - base
            w = [0.5 * (1.5 - fx)**2, 0.75 - (fx - 1)**2, 0.5 * (fx - 0.5)**2]
            new_v = ti.zero(v[p])
            new_C = ti.zero(C[p])
            for offset in ti.static(ti.grouped(ti.ndrange(*neighbour))):
                dpos = (offset - fx) * dx
                weight = 1.0
                for i in ti.static(range(dim)):
                    weight *= w[offset[i]][i]
                g_v = grid_v[base + offset]
                new_v += weight * g_v
                new_C += 4 * weight * g_v.outer_product(dpos) / dx**2
            v[p] = new_v
            x[p] += dt * v[p]
            J[p] *= 1 + dt * new_C.trace()
            C[p] = new_C


    @ti.kernel
    def init():
        for i in range(n_particles):
            x[i] = ti.Vector([ti.random() for i in range(dim)]) * 0.1 + 0.5
            J[i] = 1


    def T(a):
        if dim == 2:
            return a

        phi, theta = np.radians(28), np.radians(32)

        a = a - 0.5
        x, y, z = a[:, 0], a[:, 1], a[:, 2]
        c, s = np.cos(phi), np.sin(phi)
        C, S = np.cos(theta), np.sin(theta)
        x, z = x * c + z * s, z * c - x * s
        u, v = x, y * C + z * S
        return np.array([u, v]).swapaxes(0, 1) + 0.5


    init()
    # gui = ti.GUI('MPM3D', background_color=0x112F41)
    for time in range(100):
        for s in range(steps):
            substep()
        # pos = x.to_numpy()
        # gui.circles(T(pos), radius=1.5, color=0x66ccff)
        # gui.show()
    ti.kernel_profiler_print()

if __name__ == '__main__':
    arch_str = sys.argv[1]
    if arch_str == 'cpu':
        arch = ti.cpu
    else:
        arch = ti.gpu
    n_grid = int(sys.argv[2])
    n_particle = int(sys.argv[3])
    mpm3d(arch, n_grid, n_particle)
