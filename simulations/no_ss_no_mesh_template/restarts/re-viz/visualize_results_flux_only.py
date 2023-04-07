import openmc
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import ScalarFormatter
import pandas as pd
# TODO cleanup

# list mesh element sizes that will be used to iterate through all cases
# n_elems = [50,100,250,500,1000]
# n_elems = [50,100,250,500,1000]
n_elems = [1000]
log_N = np.log(n_elems)
L = 106.47 # equilibrium length from paper
P = 1.0e22 # eV/s
T0 = 293 # K
phi0 = 2.5e14 # n/cm^2-s
q = 1e8 # ev/s
k0= 1.25e19 # eV/(s-cm-K^2) k(T) = k0 T(x)
lam = 0.5*(1+np.sqrt(1+(16*q*q*phi0*phi0)/(P*P)))
Sig_t0 = np.sqrt(P/((lam-1)*k0*L))/(T0)

# read in x coordinates from CSV
xx = {} # key is number of elements, value is numpy array of mesh center points
for n in n_elems:
    xx[n] = pd.read_csv(f"openmc_{n}_temp.csv").loc[:,"x"]

# dictionaries of statepoint filenames and voxel volumes
# key in each case is n (the number of mesh elements).
# convention applies to rest of dictionaries unless otherwise noted
sp_filenames = {}
voxel_volumes = {}

# generate filenames and compute voxel volumes
for n in n_elems:
    sp_filenames[n] = f'statepoint_{n}.h5'
    voxel_volumes[n] = L/n # implied division by 1 x 1 (y by z) cross sectional are

# dictionaries of raw tally data for each mesh size
raw_flux_mesh_tallies = {} # units of n-cm/sp
tallied_global_system_powers = {} # units of eV-cm/sp
raw_kappa_fission_mesh_tallies = {} # units of eV-cm/sp
nu_fission_rates = {} # units of particles/sp - INTEGRAL QUANTITY, store foat
fission_rates = {} # units of fissions/sp - INTEGRAL QUANTITY, store foat
eigs = {} # k effective - one data point per mesh size, store float

# populate flux, system tallied power, and local kappa fission rates with
# openmc.Tally objects from each simulation (openmc units)
for n in n_elems:
    sp = openmc.StatePoint(sp_filenames[n])
    raw_flux_mesh_tallies[n] = sp.get_tally(id=1).get_slice(scores=['flux'])
    tallied_global_system_powers[n] = sp.get_tally(id=2).get_slice(scores=['kappa-fission'])
    raw_kappa_fission_mesh_tallies[n] = sp.get_tally(id=1).get_slice(scores=['kappa-fission'])
    nu_fission_rates[n] = float(openmc.StatePoint(sp_filenames[n]).get_tally(id=2).get_slice(scores=['nu-fission']).mean[0])
    fission_rates[n] = float(openmc.StatePoint(sp_filenames[n]).get_tally(id=2).get_slice(scores=['fission']).mean[0])
    eigs[n] = [float(sp.keff.n),float(sp.keff.s)]

print(eigs)

source_strengths = {}
# compute source strengths and convert flux to proper n/cm^2-s unit
# P [=] ev/s, nu_fission_rates [=] n/sp, voxel_volume [=] cm^3, eigs [=] n/sp, voxel_volumes [=] cm^3, tallied_global_system_powers.mean[0], ev/sp
for n in n_elems:
    # source_strengths_old[n] = P*nu_fission_rates[n]/(eigs[n][0]*voxel_volumes[n]*float(tallied_global_system_powers[n].mean[0])) # units of sp/cm^3-s
    source_strengths[n] = P/(voxel_volumes[n]*float(tallied_global_system_powers[n].mean[0])) # units of sp/cm^3-s


flux_mesh_tallies = {} # proper flux units n/cm^2-s
kappa_fission_mesh_tallies = {} # proper power units ev/cm^3-s
# convert to correct units for flux and kappa fission
for n in n_elems:
    flux_mesh_tallies[n] = raw_flux_mesh_tallies[n] * source_strengths[n]
    kappa_fission_mesh_tallies[n] = raw_kappa_fission_mesh_tallies[n] * source_strengths[n]


# dictioinaries for flux results and comparisons to temp and analytical solution key is number of elements
analytical_phi = {}
ratios_flux_num_to_analy = {}
# compute T/phi for each case
for n in n_elems:
    ratios_flux_num_to_analy[n] = [] # empty list to store ratios numerical to analytical flux
    analytical_phi[n] = phi0*np.sqrt(1- ((lam - 1)*P*P*np.multiply(xx[n],xx[n]))/(L*L*q*q*phi0*phi0))
    for i in range(n):
        ratios_flux_num_to_analy[n].append(float(flux_mesh_tallies[n].mean[i]/analytical_phi[n][i])) # openmc flux tally way
        ratios_T_to_phi[n].append(float(temps[n][i]/flux_mesh_tallies[n].mean[i]))


# numerical to analytical ratio
for n in n_elems:
    plt.plot(xx[n],ratios_flux_num_to_analy[n],'-go',label=f"{n} x-elem")
plt.xticks([-60,-40,-20,0,20,40,60])
plt.xlabel("X Coordinate [cm]")
plt.ylabel(r"Numerical $\phi(x)$ to Analytical $\phi(x)$ Ratio")
plt.title(f"Ratio Numerical to Analytical Flux {n} Mesh Elements")
plt.legend()
plt.grid()
plt.savefig(f"num_to_analytical_flux_{n}.png")
plt.clf()

# compute error norm
flux_means = {}
flux_deviations = {}
flux_dev_norms = {}
analytical_norms = {}
flux_error_norms = {}
# flux error ratio
for n in n_elems:
    flux_means[n] = []
    flux_std_dev[n] = []
    flux_deviations[n] = []
    sigma_r[n] = []
    # analytical - numerical
    for i in range(n):
        flux_deviations[n].append(analytical_phi[n][i]-float(cardinal_fluxes[n][i]))
    # take the norm of the deviation and analytical solution
    flux_dev_norms[n] = np.linalg.norm(flux_deviations[n],ord=2)
    analytical_norms[n] = np.linalg.norm(analytical_phi[n],ord=2)
    # ratio is error norm
    flux_error_norms[n] = float(flux_dev_norms[n]/analytical_norms[n])
    # plot flux with error bars
    # plt.plot(xx[n],flux_means[n],'-ko',label=f"{n} x-elem")
    # plt.errorbar(xx[n],flux_means[n],yerr=flux_std_dev[n],marker = '|',fmt='none',elinewidth=1,capsize=3,capthick=1)
    # plt.xlabel('X Coordniate [cm]')
    # plt.ylabel("Flux [n/cm^2-s]")
    # plt.title("Tallied Flux (Units Converted Using SS)")
    # plt.grid()
    # plt.savefig(f"flux_{n}.png")
    # plt.clf()

# plot all flux error ratios on one plot
for n in n_elems:
    plt.plot(xx[n],ratios_flux_num_to_analy[n],label=f"{n} x-elem")
plt.xticks([-60,-40,-20,0,20,40,60])
# plt.yticks([0.9995,1.000,1.001,1.002,1.003,1.004,1.0045])
plt.xlabel("X Coordinate [cm]",fontsize=16)
plt.ylabel(r"Numerical $\phi(x)$ to Analytical $\phi(x)$ Ratio",fontsize=16)
# plt.title("Ratio Numerical to Analytical Flux All Meshes. 200 Picard Iterations")
plt.legend(ncol=2)
plt.grid()
plt.savefig("flux_num_to_analy_ratios.png",bbox_inches='tight')
plt.clf()

log_flux_error_norms = [np.log(flux_error_norms[n]) for n in n_elems]
print(log_flux_error_norms)
# linear polynomial fit to get slope of line of best fit
pf = np.polyfit(log_N,log_flux_error_norms,1)
print("polyfit:" , pf)

# plot mesh elements vs flux error norms
plt.plot(log_N,log_flux_error_norms,'-o',label=r'$\epsilon_{\phi}=\frac{||\phi_{a} - \phi_{x} ||_{2}}{|| \phi_{a} ||_{2}}$')
plt.xlabel(r"Log of number of X elements $\log(N)$",fontsize=16)
plt.ylabel(r"Log of Error Norm $log(\epsilon_{\phi})$",fontsize=16)
# plt.title("Flux Error Norm vs Mesh Size \n 200 Picard Iterations with Relaxation")
plt.yticks(np.linspace(-6,-10,6))
plt.grid()
plt.legend(bbox_to_anchor=[0.985,0.985],fontsize=14)
plt.savefig("flux_error_norms.png",bbox_inches='tight')
plt.clf()