# GLOBAL VARS
# problem physical parameters
T0 = 293
L = 106.47 # equilibrium length from paper (TODO perhaps use formula)
P = 1.0e22 # eV/s
q = 1e8 # eV
k0= 1.25e19 # eV/(s-cm-K^2) k(T) = k0 T(x)
phi0 = 2.5e14 # 1/s-cm^2 flux at the origin
eV_to_J = 1.602e-19 # J per eV
lam = ${fparse 0.5*(1+sqrt(1+(16*q*q*phi0*phi0)/(P*P)))} # eigenvalue solution
h = ${fparse 1/(sqrt(L*(lam-1)/(k0*P)) - (2*T0)/(P)) }

[Mesh]
  [centered_mesh]
    type = FileMeshGenerator
    file = mesh_1000_in.e
  []
[]

[Variables]
  [temp]
    initial_condition = ${T0}
  []
[]

[Kernels]
  [heat_conduction]
    type = HeatConduction
    variable = temp
  []
  [heat_source]
    type = CoupledForce
    variable = temp
    v = heat_source
  []
[]

# This AuxVariable and AuxKernel is only here to get the postprocessors
# to evaluate correctly. This can be deleted after MOOSE issue #17534 is fixed.
[AuxVariables]
  [heat_source]
    family = MONOMIAL
    order = CONSTANT
  []
  [dummy]
  []
[]

[AuxKernels]
  [dummy]
    type = ConstantAux
    variable = dummy
    value = 0.0
  []
[]

[Functions]
  [conductivity]
    type = ParsedFunction
    value = '${fparse k0*eV_to_J*100} * t' # here 't' means temp. the 10 and ev_to_J is to get units of W/m-K
  []
[]

[Materials]
  [thermal_parameters]
    type = HeatConductionMaterial
    temp = temp
    thermal_conductivity_temperature_function = conductivity
  []
[]

[BCs]
  [left_convective_BC]
      type = ConvectiveFluxFunction
      T_infinity = ${T0}
      boundary = left
      coefficient = ${h}
      variable = temp
  []
  [righ_convective_BC]
      type = ConvectiveFluxFunction
      T_infinity = ${T0}
      boundary = right
      coefficient = ${h}
      variable = temp
  []
[]

[MultiApps]
  [openmc]
      type = TransientMultiApp
      app_type = CardinalApp
      input_files = 'openmc_1000.i'
      execute_on = timestep_end
  []
[]

[Executioner]
  type = Transient
  nl_abs_tol = 1e-7
  nl_rel_tol = 1e-12
  # num_steps = 5
  petsc_options_iname = '-pc_type -pc_hypre_type'
  petsc_options_value = 'hypre boomeramg'
  steady_state_detection = true
  verbose = true
[]

[Outputs]
  exodus = true
[]

[Transfers]
  [heat_source_from_openmc]
    type = MultiAppMeshFunctionTransfer
    from_multi_app = openmc
    variable = heat_source
    source_variable = heat_source
    from_postprocessors_to_be_preserved = heat_source
    to_postprocessors_to_be_preserved = source_integral
  []
  [temp_to_openmc]
    type = MultiAppMeshFunctionTransfer
    to_multi_app = openmc
    variable = temp
    source_variable = temp
  []
[]

[Postprocessors]
  [source_integral]
      type = ElementIntegralVariablePostprocessor
      variable = heat_source
      execute_on = transfer
  []
[]