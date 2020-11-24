# -*- coding: utf-8 -*-
'''
Module with CLI commands to launch for calcjob and workflows of aiida-kkr.
'''
import click

from aiida.cmdline.params import options as options_core
from aiida.orm import Code, load_node, Dict
from aiida.plugins import WorkflowFactory
from aiida.plugins import CalculationFactory
from masci_tools.io.kkr_params import kkrparams

from aiida_kkr.tools.dict_util import clean_nones
from ..util import options
from ..util.utils import launch_process
from ..util import defaults

# TODO: command for kkrimporter
# not sure if this should be a launch command
# TODO: commands for workchains: kkr_scf, vora_start, dos, eos, gf_writeout, kkr_imp, kkr_imp_dos, kkr_imp_sub
# Check_para_convergence, check_magnetic_state. base_restart_calc?


@click.command('voro')
@options.STRUCTURE_OR_FILE(default=defaults.get_cu_bulk_structure, show_default=True)
@options.VORO()
@options.PARAMETERS()
@options.PARENT_FOLDER()
@options.POTENTIAL_OVERWRITE()
@options.DAEMON()
def launch_voro(structure, voro, parameters, parent_folder, potential_overwrite, daemon):
    """
    Launch an voro calcjob on given input
    """
    # TODO?: maybe allow for additional metadata to be given.
    process_class = CalculationFactory('kkr.voro')

    inputs = {
        'structure': structure, 
        'code': voro,
        'parameters': parameters, 
        'parent_kkr': parent_folder, 
        'potential_overwrite': potential_overwrite,
        'metadata': {
            'options': {
                'withmpi': False,
                'max_wallclock_seconds': 6000,
                'resources': {
                    'num_machines': 1,
                    'num_mpiprocs_per_machine': 1,
                }
            }
        }
    }
    inputs = clean_nones(inputs)
    builder = process_class.get_builder()
    builder.update(inputs)
    launch_process(builder, daemon)

@click.command('kkr')
@options.KKR()
@options.PARAMETERS()
@options.PARENT_FOLDER(required=True)
@options.IMPURITY_INFO()
@options.KPOINTS()
@options.DAEMON()
@options.WITH_MPI()
@options.NUM_MPIPROCS_PER_MACHINE()
@options.MAX_WALLCLOCK_SECONDS()
@options.MAX_NUM_MACHINES()
def launch_kkr(kkr, parameters, parent_folder, impurity_info, kpoints, daemon, with_mpi, num_mpiprocs_per_machine, max_wallclock_seconds, max_num_machines):
    """
    Launch an kkr calcjob on given input
    """
    # TODO?: maybe allow for additional metadata to be given.
    process_class = CalculationFactory('kkr.kkr')

    inputs = {
        'code': kkr,
        'parameters': parameters, 
        'parent_folder': parent_folder, 
        'impurity_info': impurity_info,
        'metadata': {
            'options': {
                'withmpi': with_mpi,
                'max_wallclock_seconds': max_wallclock_seconds,
                'resources': {
                    'num_machines': max_num_machines,
                    'num_mpiprocs_per_machine': num_mpiprocs_per_machine,
                }
            }
        }
    }
    inputs = clean_nones(inputs)
    builder = process_class.get_builder()
    builder.update(inputs)
    launch_process(builder, daemon)


@click.command('kkrimp')
@options.KKRIMP()
@options.PARAMETERS()
@options.PARENT_FOLDER(required=True)
@options.IMPURITY_INFO()
@options.DAEMON()
@options.WITH_MPI()
@options.NUM_MPIPROCS_PER_MACHINE()
@options.MAX_WALLCLOCK_SECONDS()
@options.MAX_NUM_MACHINES()
def launch_kkrimp(kkrimp, parameters, parent_folder, impurity_info, daemon, with_mpi, num_mpiprocs_per_machine, max_wallclock_seconds, max_num_machines):
    """
    Launch an kkrimp calcjob on given input
    """
    # TODO?: maybe allow for additional metadata to be given.
    process_class = CalculationFactory('kkr.kkrimp')

    inputs = {
        'code': kkrimp,
        'parameters': parameters, 
        'parent_folder': parent_folder, 
        'impurity_info': impurity_info,
        'metadata': {
            'options': {
                'withmpi': with_mpi,
                'max_wallclock_seconds': max_wallclock_seconds,
                'resources': {
                    'num_machines': max_num_machines,
                    'num_mpiprocs_per_machine': num_mpiprocs_per_machine,
                }
            }
        }
    }
    inputs = clean_nones(inputs)
    builder = process_class.get_builder()
    builder.update(inputs)
    launch_process(builder, daemon)
