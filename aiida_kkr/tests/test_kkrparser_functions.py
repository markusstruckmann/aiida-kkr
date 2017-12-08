# -*- coding: utf-8 -*-
"""
@author: ruess
"""

import pytest
from aiida_kkr.tools.kkrparser_functions import parse_kkr_outputfile
from numpy import array


class Test_kkr_parser_functions():
    """
    Tests for the kkr parser functions
    """
    #some global definitions
    global dref, grouping_ref, outfile, outfile_0init, outfile_000, timing_file, potfile_out, nonco_out_file
    dref = {'nspin': 2, 'single_particle_energies': [0.33016425691737111, 1.5169676617833023, 38.200748406400834, 38.200748406400834, 1.5169676617833023, 0.33016425691737111], 'energy_contour_group': {'emin_unit': 'Rydberg', 'emin': -0.6, 'npol': 7, 'temperature_unit': 'Kelvin', 'n1': 3, 'n2': 32, 'n3': 3, 'number_of_energy_points': 45, 'temperature': 800.0}, 'energy': -69143.004155165298, 'warnings_group': {'number_of_warnings': 1, 'warnings_list': ['WARNING: HFIELD>0.0 found, set KHFIELD to 1']}, 'energy_unit': 'eV', 'charge_core_states_per_atom': [0.0, 0.0, 18.0, 18.0, 0.0, 0.0], 'ewald_sum_group': {'rsum_number_of_vectors': 425, 'gsum_cutoff_unit': '1/a_Bohr', 'rsum_number_of_shells': 74, 'gsum_cutoff': 11.98427, 'rsum_cutoff': 37.9646, 'gsum_number_of_shells': 1496, 'ewald_summation_mode': '3D', 'rsum_cutoff_unit': 'a_Bohr', 'gsum_number_of_vectors': 16167}, 'timings_group': [['main0', 22.6841], ['main1a - tbref', 2.9407], ['main1a', 46.106], ['main1b - calctref13', 0.4792], ['main1b', 72.2102]], 'core_states_group': {'energy_highest_lying_core_state_per_atom_unit': 'Rydberg', 'energy_highest_lying_core_state_per_atom': [None, None, None, None, -3.38073664131, -3.38073663703, -3.38073664131, -3.38073663703, None, None, None, None], 'number_of_core_states_per_atom': [0, 0, 0, 0, 5, 5, 5, 5, 0, 0, 0, 0], 'descr_highest_lying_core_state_per_atom': ['no core states', 'no core states', 'no core states', 'no core states', '3p', '3p', '3p', '3p', 'no core states', 'no core states', 'no core states', 'no core states']}, 'total_energy_Ry': -5081.9171143599997, 'fermi_energy': 0.49301096760000002, 'convergence_group': {'rms': 0.23807, 'strmix': 0.01, 'calculation_converged': False, 'charge_neutrality': -0.27584700000000001, 'orbital_moment_per_atom_all_iterations': [[-0.0, -0.0, 0.0, 0.0, -0.0, -0.0], [-0.0, -0.0, -0.0, -0.0, -0.0, -0.0], [-0.0, -0.0, -0.0, -0.0, -0.0, -0.0], [-0.0, -0.0, -0.0, -0.0, -0.0, -0.0], [-0.0, -0.0, -0.0, -0.0, -0.0, -0.0], [-0.0, 0.0, -0.0, -0.0, 0.0, -0.0], [-0.0, 0.0, -0.0, -0.0, 0.0, -0.0], [-0.0, 0.0, -0.0, -0.0, 0.0, -0.0], [0.0, 0.0, -0.0, -0.0, 0.0, 0.0], [0.0, 0.0, -0.0, -0.0, 0.0, 0.0]], 'dos_at_fermi_energy_all_iterations': [10.238607, 15.315281, 15.391192, 15.298192, 15.258272, 15.20493, 15.159147, 15.114337, 15.072376, 15.032559], 'rms_unit': 'unitless', 'charge_neutrality_all_iterations': [-4.899746, -0.590384, -0.298448, -0.371115, -0.329622, -0.324519, -0.309258, -0.298029, -0.286475, -0.275847], 'qbound': 0.0, 'rms_per_atom': [0.31221, 0.092203, 0.15861, 0.15861, 0.092203, 0.31221], 'rms_all_iterations': [2.3466, 0.2333, 0.23309, 0.23439, 0.23513, 0.23596, 0.23664, 0.23724, 0.23771, 0.23807], 'imix': 0, 'nsteps_exhausted': True, 'number_of_iterations_max': 10, 'total_spin_moment_all_iterations': [0.0, 0.0, -0.0, -0.0, -0.0, -0.0, -0.0, -0.0, -0.0, -0.0], 'idtbry': 40, 'charge_neutrality_unit': 'electrons', 'total_energy_Ry_all_iterations': [-5079.95190252, -5081.86670188, -5081.87281356, -5081.88207486, -5081.88933086, -5081.89617526, -5081.9022393, -5081.90772537, -5081.91266074, -5081.91711436], 'fcm': 20.0, 'number_of_iterations': 10, 'spin_moment_per_atom_all_iterations': [[0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [0.0, 0.0, -0.0, -0.0, 0.0, 0.0], [0.0, 0.0, -0.0, -0.0, 0.0, 0.0], [0.0, 0.0, -0.0, -0.0, 0.0, 0.0], [0.0, 0.0, -0.0, -0.0, 0.0, 0.0], [0.0, 0.0, -0.0, -0.0, 0.0, 0.0], [0.0, 0.0, -0.0, -0.0, 0.0, 0.0], [0.0, 0.0, -0.0, -0.0, 0.0, 0.0], [0.0, 0.0, -0.0, -0.0, 0.0, 0.0], [0.0, 0.0, -0.0, -0.0, 0.0, 0.0]], 'fermi_energy_all_iterations': [0.459241, 0.4656657829, 0.468897589, 0.4729407141, 0.4765411904, 0.4800983619, 0.4834984885, 0.4867848704, 0.4899526366, 0.4930109676], 'brymix': 0.01}, 'total_energy_Ry_unit': 'Rydberg', 'number_pf_atoms_in_unit_cell': 6, 'use_newsosol': True, 'two_pi_over_alat_internal_unit': '1/a_Bohr', 'magnetism_group': {'spin_moment_unit': 'mu_Bohr', 'total_spin_moment_unit': 'mu_Bohr', 'spin_moment_per_atom': [0.0, 0.0, -0.0, -0.0, 0.0, 0.0], 'spin_moment_angles_per_atom_unit': 'degree', 'orbital_moment_per_atom': [0.0, 0.0, -0.0, -0.0, 0.0, 0.0], 'spin_moment_vector_per_atom': [[0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [-0.0, -0.0, -0.0], [-0.0, -0.0, -0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]], 'spin_moment_angles_per_atom': [[0.0, 0.0], [0.0, 0.0], [0.0, 0.0], [0.0, 0.0], [0.0, 0.0], [0.0, 0.0]], 'total_spin_moment': -0.0, 'orbital_moment_unit': 'mu_Bohr', 'total_orbital_moment': 0.0}, 'charge_core_states_per_atom_unit': 'electron charge', 'two_pi_over_alat_internal': 1.15850818, 'nuclear_charge_per_atom': [0.0, 0.0, 26.0, 26.0, 0.0, 0.0], 'alat_internal_unit': 'a_Bohr', 'nuclear_charge_per_atom_unit': 'electron charge', 'charge_valence_states_per_atom_unit': 'electron charge', 'parser_warnings': [], 'kmesh_group': {'kmesh_energypoint': [4, 3, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 3, 3, 2, 1], 'number_different_kmeshes': 4, 'number_kpoints_per_kmesh': {'n_kx': [10, 7, 5, 3], 'n_ky': [10, 7, 5, 3], 'n_kz': [10, 7, 5, 3], 'number_of_kpts': [1000, 343, 125, 27]}}, 'symmetries_group': {'number_of_used_symmetries': 1, 'number_of_lattice_symmetries': 4, 'symmetry_description': {'E': {'has_inversion': 0, 'euler_angles': [0.0, 0.0, 0.0], 'is_unitary': 1}}}, 'alat_internal': 5.423514, 'timings_unit': 'seconds', 'code_info_group': {'code_version': 'v2.2-22-g4f8f5ff', 'calculation_serial_number': 'kkrjm_v2.2-22-g4f8f5ff_openmp_20171208103325', 'compile_options': 'openmp'}, 'single_particle_energies_unit': 'eV', 'dos_at_fermi_energy': 15.032558999999999, 'charge_valence_states_per_atom': [0.0040260000000000001, 0.22986200000000001, 7.628188999999999, 7.628188999999999, 0.22986200000000001, 0.0040260000000000001]}
    grouping_ref = ['energy_contour_group', 'warnings_group', 'ewald_sum_group', 'timings_group', 'core_states_group', 'convergence_group', 'magnetism_group', 'kmesh_group', 'symmetries_group', 'code_info_group']
    path0 = './files/kkr/kkr_run_slab_soc_simple/'
    outfile = path0+'out_kkr'
    outfile_0init = path0+'output.0.txt'
    outfile_000 = path0+'output.000.txt'
    timing_file = path0+'out_timing.000.txt'
    potfile_out = path0+'out_potential'
    nonco_out_file = path0+'nonco_angle_out.dat'
    
    
    def test_complete_kkr_output(self):
        """
        Parse complete output of kkr calculation
        """
        out_dict = {}
        success, msg_list, out_dict = parse_kkr_outputfile(out_dict, outfile, outfile_0init, outfile_000, timing_file, potfile_out, nonco_out_file)
        out_dict['parser_warnings'] = msg_list
        assert success
        assert set(out_dict.keys()) == set(dref.keys())
        assert out_dict == dref
        assert msg_list == []
        groups = [i for i in out_dict.keys() if 'group' in i]
        assert set(groups) == set(grouping_ref)
    
    def test_mag_orbmom_kkr_output(self):
        """
        Parse complete output of kkr calculation with orbital moments
        """
        dref = {'nspin': 2, 'single_particle_energies': [0.2097247970611916, 1.2887334935546728, 37.826589199624905, 37.826589199624905, 1.2887334935546728, 0.2097247970611916], 'energy_contour_group': {'emin_unit': 'Rydberg', 'emin': -0.6, 'npol': 7, 'temperature_unit': 'Kelvin', 'n1': 3, 'n2': 32, 'n3': 3, 'number_of_energy_points': 45, 'temperature': 800.0}, 'energy': -69143.565895181309, 'warnings_group': {'number_of_warnings': 1, 'warnings_list': ['WARNING: HFIELD>0.0 found, set KHFIELD to 1']}, 'energy_unit': 'eV', 'charge_core_states_per_atom': [0.0, 0.0, 18.0, 18.0, 0.0, 0.0], 'ewald_sum_group': {'rsum_number_of_vectors': 425, 'gsum_cutoff_unit': '1/a_Bohr', 'rsum_number_of_shells': 74, 'gsum_cutoff': 11.98427, 'rsum_cutoff': 37.9646, 'gsum_number_of_shells': 1496, 'ewald_summation_mode': '3D', 'rsum_cutoff_unit': 'a_Bohr', 'gsum_number_of_vectors': 16167}, 'timings_group': [['main0', 22.5317], ['main1a - tbref', 2.9669], ['main1a', 46.7571], ['main1b - calctref13', 0.5216], ['main1b', 72.7774]], 'core_states_group': {'energy_highest_lying_core_state_per_atom_unit': 'Rydberg', 'energy_highest_lying_core_state_per_atom': [None, None, None, None, -3.3177936736000002, -3.4353219668800001, -3.3177936736000002, -3.4353219668800001, None, None, None, None], 'number_of_core_states_per_atom': [0, 0, 0, 0, 5, 5, 5, 5, 0, 0, 0, 0], 'descr_highest_lying_core_state_per_atom': ['no core states', 'no core states', 'no core states', 'no core states', '3p', '3p', '3p', '3p', 'no core states', 'no core states', 'no core states', 'no core states']}, 'total_energy_Ry': -5081.9584014900001, 'fermi_energy': 0.49007270419999999, 'convergence_group': {'rms': 0.21679000000000001, 'strmix': 0.01, 'calculation_converged': False, 'charge_neutrality': -0.17172599999999999, 'orbital_moment_per_atom_all_iterations': [[-0.0, -0.0001, -0.0063, -0.0063, -0.0001, -0.0], [0.0, -0.0001, 0.0464, 0.0464, -0.0001, 0.0], [0.0, -0.0001, 0.052, 0.052, -0.0001, 0.0], [0.0, -0.0001, 0.053, 0.053, -0.0001, 0.0], [0.0, -0.0001, 0.0539, 0.0539, -0.0001, 0.0], [0.0, -0.0001, 0.0547, 0.0547, -0.0001, 0.0], [0.0, -0.0001, 0.0558, 0.0558, -0.0001, 0.0], [0.0, -0.0002, 0.0572, 0.0572, -0.0002, 0.0], [0.0, -0.0002, 0.0585, 0.0585, -0.0002, 0.0], [-0.0, -0.0002, 0.0599, 0.0599, -0.0002, -0.0]], 'dos_at_fermi_energy_all_iterations': [10.778086, 13.756463, 13.070528, 12.371442, 11.652055, 10.987681, 10.402299, 9.890784, 9.437221, 9.013371], 'rms_unit': 'unitless', 'charge_neutrality_all_iterations': [-4.914607, -0.4306, -0.254987, -0.262482, -0.239525, -0.215776, -0.190357, -0.173403, -0.168785, -0.171726], 'qbound': 0.0, 'rms_per_atom': [0.26244, 0.052778, 0.17549, 0.17549, 0.052778, 0.26244], 'rms_all_iterations': [2.17, 0.22841, 0.22738, 0.22601, 0.22458, 0.22304, 0.22139, 0.21969, 0.21811, 0.21679], 'imix': 0, 'nsteps_exhausted': True, 'number_of_iterations_max': 10, 'total_spin_moment_all_iterations': [1.150471, 2.201148, 2.530913, 2.835644, 3.131747, 3.409436, 3.669548, 3.912214, 4.137758, 4.346569], 'idtbry': 40, 'charge_neutrality_unit': 'electrons', 'total_energy_Ry_all_iterations': [-5080.21763742, -5081.87827258, -5081.89042264, -5081.90349614, -5081.91552341, -5081.92632203, -5081.93573754, -5081.94396567, -5081.95138589, -5081.95840149], 'fcm': 20.0, 'number_of_iterations': 10, 'spin_moment_per_atom_all_iterations': [[0.0005, 0.0214, 0.5534, 0.5534, 0.0214, 0.0005], [0.0005, 0.0156, 1.0844, 1.0844, 0.0156, 0.0005], [0.0005, 0.0152, 1.2497, 1.2497, 0.0152, 0.0005], [0.0005, 0.0159, 1.4015, 1.4015, 0.0159, 0.0005], [0.0005, 0.0166, 1.5488, 1.5488, 0.0166, 0.0005], [0.0005, 0.0174, 1.6869, 1.6869, 0.0174, 0.0005], [0.0004, 0.0181, 1.8162, 1.8162, 0.0181, 0.0004], [0.0004, 0.0187, 1.937, 1.937, 0.0187, 0.0004], [0.0004, 0.0193, 2.0492, 2.0492, 0.0193, 0.0004], [0.0003, 0.02, 2.153, 2.153, 0.02, 0.0003]], 'fermi_energy_all_iterations': [0.459241, 0.4644579419, 0.4677093646, 0.4712454875, 0.4746715679, 0.4779445657, 0.4809944912, 0.4839164583, 0.4868973048, 0.4900727042], 'brymix': 0.01}, 'total_energy_Ry_unit': 'Rydberg', 'number_pf_atoms_in_unit_cell': 6, 'use_newsosol': True, 'two_pi_over_alat_internal_unit': '1/a_Bohr', 'magnetism_group': {'spin_moment_unit': 'mu_Bohr', 'total_spin_moment_unit': 'mu_Bohr', 'spin_moment_per_atom': [0.0003, 0.02, 2.153, 2.153, 0.02, 0.0003], 'spin_moment_angles_per_atom_unit': 'degree', 'orbital_moment_per_atom': [-0.0, -0.0002, 0.0599, 0.0599, -0.0002, -0.0], 'spin_moment_vector_per_atom': [[0.0, 0.0, 0.0003], [0.0, 0.0, 0.02], [0.0, 0.0, 2.153], [0.0, 0.0, 2.153], [0.0, 0.0, 0.02], [0.0, 0.0, 0.0003]], 'spin_moment_angles_per_atom': [[0.0, 0.0], [0.0, 0.0], [0.0, 0.0], [0.0, 0.0], [0.0, 0.0], [0.0, 0.0]], 'total_spin_moment': 4.3465689999999997, 'orbital_moment_unit': 'mu_Bohr', 'total_orbital_moment': 0.11940000000000001}, 'charge_core_states_per_atom_unit': 'electron charge', 'two_pi_over_alat_internal': 1.15850818, 'nuclear_charge_per_atom': [0.0, 0.0, 26.0, 26.0, 0.0, 0.0], 'alat_internal_unit': 'a_Bohr', 'nuclear_charge_per_atom_unit': 'electron charge', 'charge_valence_states_per_atom_unit': 'electron charge', 'parser_warnings': [], 'kmesh_group': {'kmesh_energypoint': [4, 3, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 3, 3, 2, 1], 'number_different_kmeshes': 4, 'number_kpoints_per_kmesh': {'n_kx': [10, 7, 5, 3], 'n_ky': [10, 7, 5, 3], 'n_kz': [10, 7, 5, 3], 'number_of_kpts': [1000, 343, 125, 27]}}, 'symmetries_group': {'number_of_used_symmetries': 1, 'number_of_lattice_symmetries': 4, 'symmetry_description': {'E': {'has_inversion': 0, 'euler_angles': [0.0, 0.0, 0.0], 'is_unitary': 1}}}, 'alat_internal': 5.423514, 'timings_unit': 'seconds', 'code_info_group': {'code_version': 'v2.2-22-g4f8f5ff', 'calculation_serial_number': 'kkrjm_v2.2-22-g4f8f5ff_openmp_20171208132839', 'compile_options': 'openmp'}, 'single_particle_energies_unit': 'eV', 'dos_at_fermi_energy': 9.0133709999999994, 'charge_valence_states_per_atom': [0.003503, 0.21339, 7.6972440000000013, 7.6972440000000013, 0.21339, 0.003503]}
        path0 = './files/kkr/kkr_run_slab_soc_mag/'
        outfile = path0+'out_kkr'
        outfile_0init = path0+'output.0.txt'
        outfile_000 = path0+'output.000.txt'
        timing_file = path0+'out_timing.000.txt'
        potfile_out = path0+'out_potential'
        nonco_out_file = path0+'nonco_angle_out.dat'
        out_dict = {}
        success, msg_list, out_dict = parse_kkr_outputfile(out_dict, outfile, outfile_0init, outfile_000, timing_file, potfile_out, nonco_out_file)
        out_dict['parser_warnings'] = msg_list
        assert success
        assert set(out_dict.keys()) == set(dref.keys())
        assert out_dict == dref
        assert msg_list == []
    
    def test_nosoc_kkr_output(self):
        """
        Parse complete output of kkr calculation nosoc, magnetic
        """        
        dref = {'nspin': 2, 'single_particle_energies': [0.3300528004408107, 1.5175235386980168, 38.205408680071912, 38.205408680071912, 1.5175235386980168, 0.3300528004408107], 'energy_contour_group': {'emin_unit': 'Rydberg', 'emin': -0.6, 'npol': 7, 'temperature_unit': 'Kelvin', 'n1': 3, 'n2': 32, 'n3': 3, 'number_of_energy_points': 45, 'temperature': 800.0}, 'energy': -69142.986794301018, 'warnings_group': {'number_of_warnings': 1, 'warnings_list': ['WARNING: HFIELD>0.0 found, set KHFIELD to 1']}, 'energy_unit': 'eV', 'charge_core_states_per_atom': [0.0, 0.0, 18.0, 18.0, 0.0, 0.0], 'ewald_sum_group': {'rsum_number_of_vectors': 425, 'gsum_cutoff_unit': '1/a_Bohr', 'rsum_number_of_shells': 74, 'gsum_cutoff': 11.98427, 'rsum_cutoff': 37.9646, 'gsum_number_of_shells': 1496, 'ewald_summation_mode': '3D', 'rsum_cutoff_unit': 'a_Bohr', 'gsum_number_of_vectors': 16167}, 'timings_group': [['main0', 4.4618], ['main1a - tbref', 1.4537], ['main1a', 10.5589], ['main1b - calctref13', 0.4878], ['main1b', 16.9623]], 'core_states_group': {'energy_highest_lying_core_state_per_atom_unit': 'Rydberg', 'energy_highest_lying_core_state_per_atom': [None, None, None, None, -3.3808088817000002, -3.3808088773999998, -3.3808088817000002, -3.3808088773999998, None, None, None, None], 'number_of_core_states_per_atom': [0, 0, 0, 0, 5, 5, 5, 5, 0, 0, 0, 0], 'descr_highest_lying_core_state_per_atom': ['no core states', 'no core states', 'no core states', 'no core states', '3p', '3p', '3p', '3p', 'no core states', 'no core states', 'no core states', 'no core states']}, 'total_energy_Ry': -5081.9158383599997, 'fermi_energy': 0.49281398320000003, 'convergence_group': {'rms': 0.23827000000000001, 'strmix': 0.01, 'calculation_converged': False, 'charge_neutrality': -0.27584399999999998, 'dos_at_fermi_energy_all_iterations': [10.260433, 15.367202, 15.427578, 15.336628, 15.293781, 15.239316, 15.191993, 15.145917, 15.102739, 15.061817], 'rms_unit': 'unitless', 'charge_neutrality_all_iterations': [-4.90193, -0.576195, -0.303203, -0.369647, -0.330104, -0.324371, -0.309302, -0.298009, -0.286475, -0.275844], 'qbound': 0.0, 'rms_per_atom': [0.31264, 0.092533, 0.15846, 0.15846, 0.092533, 0.31264], 'rms_all_iterations': [2.3414, 0.23344, 0.23332, 0.2346, 0.23535, 0.23618, 0.23686, 0.23745, 0.23792, 0.23827], 'imix': 0, 'nsteps_exhausted': True, 'number_of_iterations_max': 10, 'total_spin_moment_all_iterations': [0.0, 0.0, -0.0, -0.0, -0.0, -0.0, -0.0, -0.0, -0.0, -0.0], 'idtbry': 40, 'charge_neutrality_unit': 'electrons', 'total_energy_Ry_all_iterations': [-5079.95660683, -5081.8656148, -5081.87192003, -5081.88104897, -5081.88827002, -5081.89505638, -5081.90107597, -5081.90651978, -5081.91141803, -5081.91583836], 'fcm': 20.0, 'number_of_iterations': 10, 'spin_moment_per_atom_all_iterations': [[0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [0.0, 0.0, -0.0, -0.0, 0.0, 0.0], [0.0, 0.0, -0.0, -0.0, 0.0, 0.0], [0.0, 0.0, -0.0, -0.0, 0.0, 0.0], [0.0, 0.0, -0.0, -0.0, 0.0, 0.0], [0.0, 0.0, -0.0, -0.0, 0.0, 0.0], [0.0, 0.0, -0.0, -0.0, 0.0, 0.0], [0.0, 0.0, -0.0, -0.0, 0.0, 0.0], [0.0, 0.0, -0.0, -0.0, 0.0, 0.0], [0.0, 0.0, -0.0, -0.0, 0.0, 0.0]], 'fermi_energy_all_iterations': [0.459241, 0.4654901812, 0.4687657284, 0.472782771, 0.476380134, 0.4799276602, 0.4833209134, 0.4866002281, 0.4897616294, 0.4928139832], 'brymix': 0.01}, 'total_energy_Ry_unit': 'Rydberg', 'number_pf_atoms_in_unit_cell': 6, 'use_newsosol': False, 'two_pi_over_alat_internal_unit': '1/a_Bohr', 'magnetism_group': {'spin_moment_unit': 'mu_Bohr', 'total_spin_moment': -0.0, 'total_spin_moment_unit': 'mu_Bohr', 'spin_moment_per_atom': [0.0, 0.0, -0.0, -0.0, 0.0, 0.0]}, 'charge_core_states_per_atom_unit': 'electron charge', 'two_pi_over_alat_internal': 1.15850818, 'nuclear_charge_per_atom': [0.0, 0.0, 26.0, 26.0, 0.0, 0.0], 'alat_internal_unit': 'a_Bohr', 'nuclear_charge_per_atom_unit': 'electron charge', 'charge_valence_states_per_atom_unit': 'electron charge', 'parser_warnings': [], 'kmesh_group': {'kmesh_energypoint': [4, 3, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 3, 3, 2, 1, 4, 3, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 3, 3, 2, 1], 'number_different_kmeshes': 4, 'number_kpoints_per_kmesh': {'n_kx': [10, 7, 5, 3], 'n_ky': [10, 7, 5, 3], 'n_kz': [10, 7, 5, 3], 'number_of_kpts': [310, 112, 45, 12]}}, 'symmetries_group': {'number_of_used_symmetries': 4, 'number_of_lattice_symmetries': 4, 'symmetry_description': {'C2z': {'has_inversion': 0, 'euler_angles': [180.0, 0.0, 0.0], 'is_unitary': 1}, 'IC2x': {'has_inversion': 1, 'euler_angles': [180.0, 180.0, 0.0], 'is_unitary': 1}, 'IC2y': {'has_inversion': 1, 'euler_angles': [0.0, 180.0, 0.0], 'is_unitary': 1}, 'E': {'has_inversion': 0, 'euler_angles': [0.0, 0.0, 0.0], 'is_unitary': 1}}}, 'alat_internal': 5.423514, 'timings_unit': 'seconds', 'code_info_group': {'code_version': 'v2.2-22-g4f8f5ff', 'calculation_serial_number': 'kkrjm_v2.2-22-g4f8f5ff_openmp_20171208160428', 'compile_options': 'openmp'}, 'single_particle_energies_unit': 'eV', 'dos_at_fermi_energy': 15.061817, 'charge_valence_states_per_atom': [0.0040280000000000003, 0.22997500000000001, 7.6280740000000016, 7.6280740000000016, 0.22997500000000001, 0.0040280000000000003]}
        path0 = './files/kkr/kkr_run_slab_nosoc/'
        outfile = path0+'out_kkr'
        outfile_0init = path0+'output.0.txt'
        outfile_000 = path0+'output.000.txt'
        timing_file = path0+'out_timing.000.txt'
        potfile_out = path0+'out_potential'
        nonco_out_file = path0+'nonco_angle_out.dat'
        out_dict = {}
        success, msg_list, out_dict = parse_kkr_outputfile(out_dict, outfile, outfile_0init, outfile_000, timing_file, potfile_out, nonco_out_file)
        out_dict['parser_warnings'] = msg_list
        assert success
        assert set(out_dict.keys()) == set(dref.keys())
        assert out_dict == dref
        assert msg_list == []

    def test_missing_outfile(self):
        """
        Parse kkr output where out_kkr is missing. Compares error messages
        """
        out_dict = {}
        success, msg_list, out_dict = parse_kkr_outputfile(out_dict, 'wrong_name', outfile_0init, outfile_000, timing_file, potfile_out, nonco_out_file)
        out_dict['parser_warnings'] = msg_list
        return msg_list
        assert not success
        assert set(msg_list) == set(['Error parsing output of KKR: Version Info', 'Error parsing output of KKR: rms-error', 'Error parsing output of KKR: charge neutrality', 'Error parsing output of KKR: total magnetic moment', 'Error parsing output of KKR: spin moment per atom', 'Error parsing output of KKR: orbital moment', 'Error parsing output of KKR: EF', 'Error parsing output of KKR: DOS@EF', 'Error parsing output of KKR: total energy', 'Error parsing output of KKR: search for warnings', 'Error parsing output of KKR: charges', 'Error parsing output of KKR: scfinfo'])

    def test_missing_outfile0init(self):
        """
        Parse kkr output where output.0.txt is missing. Compares error messages
        """
        out_dict = {}
        success, msg_list, out_dict = parse_kkr_outputfile(out_dict, outfile, 'wrong_name', outfile_000, timing_file, potfile_out, nonco_out_file)
        out_dict['parser_warnings'] = msg_list
        return msg_list
        assert not success
        assert set(msg_list) == set(['Error parsing output of KKR: nspin/natom', 'Error parsing output of KKR: spin moment per atom', 'Error parsing output of KKR: orbital moment', 'Error parsing output of KKR: energy contour', 'Error parsing output of KKR: alat, 2*pi/alat', 'Error parsing output of KKR: scfinfo', 'Error parsing output of KKR: kmesh', 'Error parsing output of KKR: symmetries', 'Error parsing output of KKR: ewald summation for madelung poterntial'])

    def test_missing_outfile000(self):
        """
        Parse kkr output where output.000.txt is missing. Compares error messages
        """
        out_dict = {}
        success, msg_list, out_dict = parse_kkr_outputfile(out_dict, outfile, outfile_0init, 'wrong_name', timing_file, potfile_out, nonco_out_file)
        out_dict['parser_warnings'] = msg_list
        return msg_list
        assert not success
        assert set(msg_list) == set(['Error parsing output of KKR: rms-error', 'Error parsing output of KKR: single particle energies', 'Error parsing output of KKR: charges', 'Error parsing output of KKR: scfinfo', 'Error parsing output of KKR: kmesh'])

    def test_missing_timingfile(self):
        """
        Parse kkr output where out_timing.000.txt is missing. Compares error messages
        """
        out_dict = {}
        success, msg_list, out_dict = parse_kkr_outputfile(out_dict, outfile, outfile_0init, outfile_000, 'wrong_name', potfile_out, nonco_out_file)
        out_dict['parser_warnings'] = msg_list
        return msg_list
        assert not success
        assert msg_list == ['Error parsing output of KKR: timings']

    def test_missing_potfile(self):
        """
        Parse kkr output where out_potential is missing. Compares error messages
        """
        out_dict = {}
        success, msg_list, out_dict = parse_kkr_outputfile(out_dict, outfile, outfile_0init, outfile_000, timing_file, 'wrong_name', nonco_out_file)
        out_dict['parser_warnings'] = msg_list
        assert not success
        assert msg_list == ['Error parsing output of KKR: core_states']
        

    def test_missing_nonco_angles(self):
        """
        Parse kkr output where out_potential is missing. Compares error messages
        """
        path0 = './files/kkr/kkr_run_slab_soc_mag/'
        outfile = path0+'out_kkr'
        outfile_0init = path0+'output.0.txt'
        outfile_000 = path0+'output.000.txt'
        timing_file = path0+'out_timing.000.txt'
        potfile_out = path0+'out_potential'
        out_dict = {}
        success, msg_list, out_dict = parse_kkr_outputfile(out_dict, outfile, outfile_0init, outfile_000, timing_file, potfile_out, 'wrong_name')
        out_dict['parser_warnings'] = msg_list
        assert not success
        assert msg_list == ['Error parsing output of KKR: spin moment per atom']
