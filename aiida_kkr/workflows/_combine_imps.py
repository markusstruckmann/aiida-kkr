# -*- coding: utf-8 -*-
"""
This module contains the workflow which combines pre-converged two single-impurity calculations to a larger impurity calculation
"""

from __future__ import absolute_import
from __future__ import print_function
from aiida.engine import WorkChain, if_, ToContext, calcfunction
from aiida.orm import load_node, Dict, WorkChainNode, Int, RemoteData
from aiida_kkr.calculations import KkrCalculation, KkrimpCalculation
from aiida_kkr.workflows import kkr_imp_sub_wc, kkr_flex_wc, kkr_imp_wc
from aiida_kkr.tools.combine_imps import (create_combined_imp_info_cf, combine_potentials_cf,
                                          get_zimp, get_host_structure, get_nspin_and_pot, combine_settings_ldau)
from aiida_kkr.tools.save_output_nodes import create_out_dict_node
import tarfile
import numpy as np
from masci_tools.io.common_functions import get_Ry2eV
from aiida.orm import ArrayData




__copyright__ = (u"Copyright (c), 2020, Forschungszentrum Jülich GmbH, "
                 "IAS-1/PGI-1, Germany. All rights reserved.")
__license__ = "MIT license, see LICENSE.txt file"
__version__ = "0.3.1"
__contributors__ = (u"Philipp Rüßmann , Rubel Mozumder")


class combine_imps_wc(WorkChain):
    """
    Workchain that combines 2 converged single-impurity calculations to a bigger impurity,
    reusing the preconverged potentials. This is useful, for example, to study co-doping.
   
   Inputs:
    :param impurity1_output_node:(Dict), required, output node from singel impurity wc, and should be one of the
                                 following: 
                                 * for `kkr_imp_wc`: single_imp_worlfow.outputs.workflow_info
                                 * for `kkr_imp_sub_wc`: single_imp_worlfow.outputs.workflow_info
                                 * for `KkrimpCalculation`: single_imp_worlfow.outputs.output_parameters
    
    :param impurity2_output_node:(Dict), required, output node from second singel impurity wc, and should be one of 
                                 the following: 
                                 * for `kkr_imp_wc`: single_imp_worlfow.outputs.workflow_info
                                 * for `kkr_imp_sub_wc`: single_imp_worlfow.outputs.workflow_info
                                 * for `KkrimpCalculation`: single_imp_worlfow.outputs.output_parameters
    :offset_imp2:(Dict), required, offset of the second impurity with respect to the first impurity position.
                 e.g. {'index:0 or 1}, the replacement by the second impurity will take place at the same cell 
                        or at the next nearest cell respectively.

    :param scf.kkrimp: (Code), mandatory, KKRimp code needed to submit kkr_imp_wc
    :param scf.wf_parameters: (Dict), optional, KKRimp code needed to submit kkr_imp_sub_wc
    :param scf.options: (Dict), optional, computer options for kkr_imp_sub_wc

    :param host_gf.kkr: (Code), optional, KKR code for submit kkr_flex_wc, needed if remote_data_gf is not given
    :param host_gf.options: (Dict), optional, computer options for kkr_flex_wc
    :param host_gf.params_kkr_overwrite: (Dict), optional, needed for kkr calculation for GF writeout
    
    :param wf_parameters_overwrite: (Dict), optional, specifications for wf_parameters of kkr_imp_sub_wc as well 
                                  as well as wf_parameters of kkr_flex_wc.
    :param gf_host_remote: (RemoteData), optional, remote folder of a previous kkrflex writeout step
                          calculations containing the flexfiles and will be used for combine host GF.

   Returns:
    :return workflow_info: (Dict), Information of workflow results
    :return last_calc_output_parameters: (Dict), link to output parameters of the last called calculation of the 
                                        scf kkr_imp_sub_wc.
    :return last_potential: (SingleFileData) link to last output potential of scf kkr_imp_sub_wc step.
    :return last_calc_remote: (RemoteData) link to remote data of last called calculation of the scf step.
    :return remote_data_gf: (RemoteData) link to GF_host_remote of outputs of kkr_flex_wc e.g. gf_writeou
                           step (only present of host GF was generated here).
    :return JijData: (ArrayData) Consists magnetic interaction data among the magnetic impurity atoms, 
                    such as vector distance(rx, ry, rz) between atoms, spin interaction magnetude J, 
                    Dzyaloshinskii-Moriya vector magnitude, and Dzyaloshinskii-Moriya vector component(Dx, Dy, Dz)
    :return JijInfo :(Dict) Consists description about the JijData.

    """

    _workflowversion = __version__
    _wf_default = { 'jij_run': False,           # Any kind of addition in _wf_default should be updated into the start() as well.
                    'retrieve_kkrflex': False,
                   }

    @classmethod
    def get_wf_defaults(cls, silent=False):
        """
        Print and return _wf_defaults dictionary. Can be used to easily create
        set of wf_parameters_overwrite.
        returns _wf_defaults
        """
        if not silent:
            print('Version of workflow: {}'.format(cls._workflowversion))
        return cls._wf_default

    @classmethod
    def define(cls, spec):
        """
        Defines the outline of the workflow
        """

        # take define from AiiDA base class and extend it then
        super(combine_imps_wc, cls).define(spec)

        # expose these inputs from sub-workflows
        spec.expose_inputs(kkr_imp_sub_wc, namespace='scf', include=('kkrimp', 'options', 'wf_parameters',))
        spec.expose_inputs(kkr_flex_wc,
                           namespace='host_gf',
                           include=('kkr', 'options', 'params_kkr_overwrite',), # expose only those port which are not set automatically
                           namespace_options={'required': False, 'populate_defaults': False}, # this makes sure the kkr code input is not needed if gf_host_remote is provided and the entire namespace is omitted
                          )

        # mandatory inputs
        spec.input("impurity1_output_node", required=True, valid_type=Dict, #TODO make validator for input node to make sure it is the output of kkr_imp_wc
                   help="""
Output node of a single impurity calculation. This can be the output of either the `kkr_imp_wc`, `kkr_imp_sub_wc`
workflows or of an `KkrimpCalculation`.

Use these output Dict nodes:
  * for `kkr_imp_wc`: single_imp_worlfow.outputs.workflow_info
  * for `kkr_imp_sub_wc`: single_imp_worlfow.outputs.workflow_info
  * for `KkrimpCalculation`: single_imp_worlfow.outputs.output_parameters
""")
        
        spec.input("impurity2_output_node", required=True, valid_type=Dict,
                   help="Output node of second single impurity calculation. See help string of `impurity1_output_node` for more details.")
        
        spec.input("offset_imp2", valid_type=Dict, required=True,
                   help="""Offset of the secon impurity with respect to the first impurity.
Can be given either via the 'vector' or the 'index' keys in the dictionary.
The 'vector' option allows to give the offset vector in cartesian units and 
the 'index' option allows to five the offset vector in units of the lattice 
vectors of the host system's structure.""")
        spec.input("wf_parameters_overwrite", valid_type=Dict, required=False,
                    help="To add or edit wf_parameters in scf namespace and add run optioins, if needed")
        spec.input("gf_host_remote", valid_type=RemoteData, required=False, #TODO Add validator that makes sure this is not given together with the host_gf sub-workflow namespace
                   help="""RemoteData node of pre-calculated host Green function (i.e. with kkr_flex_wc).
If given then the writeout step of the host GF is omitted.""")


        # structure of the workflow
        spec.outline(
            cls.start,                      # initialize workflow (set things in context and some consistency checks)
            cls.create_big_cluster,         # combine imp clusters of the two imps
            cls.update_params,              # update wf_parameters of kkr_imp_sub_wc, kkr_flex_wc and run_options
            if_(cls.need_gf_run)(           # check if GF was given in input and can be reused
                cls.run_gf_writeout),       # write out the host GF
            cls.check_host_gf,              # update the host GF
            cls.create_big_potential,       # combine preconverged potentials to big one
            cls.run_kkrimp_scf,             # run the kkrimp_sub workflow to converge the host-imp startpot
            if_(cls.run_jij)(               # Check Jij step should run or not
            cls.run_jij_step),              # run jij step
            cls.return_results              # check if the calculation was successful and return the result nodes
            )

        # define the possible exit codes
        spec.exit_code(999, 'ERROR_SOMETHING_WENT_WRONG',
            message="ERROR: take a look")
        spec.exit_code(900, 'ERROR_HOST_STRUCTURES_INCONSISTENT',
            message="Host structures of impurity 1 and impurity 2 are not identical!")
        spec.exit_code(800, 'ERROR_INPUT_NOT_SINGLE_IMP_CALC',
            message="Impurity input is not a single impurity calculation.")
        spec.exit_code(850, 'ERROR_INPLANE_NEIGHBOR_TOO_SMALL',
            message="i_neighbor_inplane needs to be positive and bigger than 0 for in-plane neighbors")
        spec.exit_code(950, 'ERROR_INCONSISTENT_NSPIN_VALUES',
            message="The impurity calculations have different NSPIN values")
        spec.exit_code(700, 'ERROR_HOST_GF_CALC_FAILED',
            message="The writeout of the host GF failed")

        #TODO to fix this create_combined_imp_info_cf need to take the different layers into account
        # when the difference vector and the neighbors are created

        # define the outputs of the workflow
        spec.output('workflow_info')
        spec.output('last_calc_output_parameters')
        spec.output('last_potential')
        spec.output('last_calc_remote')
        spec.output('remote_data_gf', required=False)
        spec.output('JijData', required=False)
        spec.output('JijInfo', required=False)


    def start(self): # pylint: disable=inconsistent-return-statements
        """
        prepare context, run_option, wf_parameter, run_option, wf_parameterss and do some consistency checks
        """
        message = 'INFO: started combine_imps_wc workflow version {}'.format(self._workflowversion)
        self.report(message)
        if 'wf_parameters_overwrite' in self.inputs:
            self.ctx.wf_parameters_overwrite= self.inputs.wf_parameters_overwrite
        # wf_parameters_flex to keep upto time the  gf_writeout_step
        self.ctx.wf_parameters_flex = { 'retrieve_kkrflex': False
                                      }
        
        self.ctx.run_options = {'jij_run': False }
        self.ctx.imp1 = self.get_imp_node_from_input(iimp=1)
        self.ctx.imp2 = self.get_imp_node_from_input(iimp=2)
        
        # find and compare host structures for the two imps to make sure the impurities are consistent
        host_structure1 = get_host_structure(self.ctx.imp1)
        host_structure2 = get_host_structure(self.ctx.imp2)
        #TODO this can be relaxed to make sure the same structure is used even if it is not the same node
        if host_structure1.uuid != host_structure2.uuid:
            self.report("host structures inconsistent")
            return self.exit_codes.ERROR_HOST_STRUCTURES_INCONSISTENT # pylint: disable=maybe-no-member

        # save host structure in context
        self.ctx.host_structure = host_structure1

        # settings for offset between imps
        self.ctx.i_neighbor_inplane = self.inputs.offset_imp2['index']
        
        # preserve the inputs from scf namespace to context
        self.ctx.scf_kkrimp = self.inputs.scf.kkrimp
        if 'options' in self.inputs.scf:
            self.ctx.scf_options = self.inputs.scf.options
        if 'wf_parameters' in self.inputs.scf:
            self.ctx.scf_wf_parameters = self.inputs.scf.wf_parameters
        # Add some run option here
        self.ctx.jij_option = False

        # TODO: PRESERVE THE INPUTS FROM host_gf NAMESPACE TO CONTEXT
        # TODO: ALSO EDIT THE RUN_GF_WRITEOUT() FOR THIS CORRESPONDING CHANGES

    
    def get_imp_node_from_input(self, iimp=1):
        """
        extract impurty calculation from impurity output node of inputs
        """
        if iimp==1:
            imp_out = self.inputs.impurity1_output_node
        else:
            imp_out = self.inputs.impurity2_output_node
        
        kkrimpcalc_parents = imp_out.get_incoming(node_class=KkrimpCalculation).all()
        if len(kkrimpcalc_parents) > 0:
            imp = kkrimpcalc_parents[0].node
        else:
            inc = imp_out.get_incoming(link_label_filter='workflow_info').all()
            if len(inc)!=1:
                self.report(f"input node of imp {iimp} inconsistent")
                return self.exit_codes.ERROR_INPUT_NODE_INCONSISTENT # pylint: disable=maybe-no-member
            imp = inc[0].node
        
        # consistency checks of input nodes
        # check if input calc was converged etc.
        if not self._check_input_imp(imp):
            self.report(f"something wrong with imp {iimp}: {imp}")
            return self.exit_codes.ERROR_SOMETHING_WENT_WRONG # pylint: disable=maybe-no-member
        
        return imp
    

    def _check_input_imp(self, imp_calc_or_wf):
        """
        check if input calculation is a kkr_imp_wc workflow which did converge
        """

        if imp_calc_or_wf.process_class == KkrimpCalculation:
            # imp_calc_or_wf can be KkrimpClaculation
            if not imp_calc_or_wf.outputs.output_parameters['convergence_group']['calculation_converged']:
                return False
        else:
            # imp_calc_or_wf should be kkr_imp_wc or kkr_imp_sub_wc or combine_imps_wc workflow
            if not isinstance(imp_calc_or_wf, WorkChainNode):
                self.report("impurity_workflow not a WorkChainNode: {}".format(imp_calc_or_wf))
                return False

            if not (imp_calc_or_wf.process_class == kkr_imp_wc or 
                    imp_calc_or_wf.process_class == kkr_imp_sub_wc or
                     imp_calc_or_wf.process_class == self
                    ):
                self.report("impurity_workflow class is wrong: {}".format(imp_calc_or_wf))
                return False

            # calculation should be converged
            if imp_calc_or_wf.process_class==kkr_imp_wc:
                if not imp_calc_or_wf.outputs.workflow_info.get_dict().get('converged'):
                    self.report("impurity_workflow not converged")
                    return False
            elif imp_calc_or_wf.process_class==kkr_imp_sub_wc:
                if not imp_calc_or_wf.outputs.workflow_info.get_dict().get('convergence_reached'):
                    self.report("impurity_workflow not converged")
                    return False
            elif imp_calc_or_wf.process_class==self:
                if not imp_calc_or_wf.outputs.workflow_info.get_dict().get('convergence_reached'):
                    self.report("impurity_workflow not converged")
                    return False


        # all checks passed
        return True


    def create_big_cluster(self): # pylint: disable=inconsistent-return-statements
        """
        combine imp clusters of the two imps
        """

        impinfo1 = self.ctx.imp1.inputs.impurity_info
        impinfo2 = self.ctx.imp2.inputs.impurity_info
        host_structure = self.ctx.host_structure

        self.report("create combined imp_info:")
        self.report("host structure: {}".format(host_structure))
        self.report("imp info 1: {}".format(impinfo1))
        self.report("imp info 2: {}".format(impinfo2))

        if self.inputs.offset_imp2['index']<0:
            return self.exit_codes.ERROR_INPLANE_NEIGHBOR_TOO_SMALL # pylint: disable=maybe-no-member
        if impinfo1['ilayer_center'] == impinfo2['ilayer_center'] and self.inputs.offset_imp2['index']<1:
            return self.exit_codes.ERROR_INPLANE_NEIGHBOR_TOO_SMALL # pylint: disable=maybe-no-member

        # get zimp of imp1
        _, is_single_imp = self.get_and_check_zimp_list(impinfo1)
        if not is_single_imp:
            return self.exit_codes.ERROR_INPUT_NOT_SINGLE_IMP_CALC # pylint: disable=maybe-no-member

        # do the same for imp2
        _, is_single_imp = self.get_and_check_zimp_list(impinfo2)
        if not is_single_imp:
            return self.exit_codes.ERROR_INPUT_NOT_SINGLE_IMP_CALC # pylint: disable=maybe-no-member

        # create combined cluster, offset of second imp is extracted from i_neighbor_inplane
        out_dict = create_combined_imp_info_cf(host_structure, impinfo1, impinfo2, self.inputs.offset_imp2)

        self.ctx.imp_info_combined = out_dict['imp_info_combined']
        self.ctx.kickout_info = out_dict['kickout_info']


    def get_and_check_zimp_list(self, impurity_info):
        """
        extract zimp from impurity_info node and check if it is consistent (needs to be single impurity calculation)
        """
        is_single_imp = True

        zimp = get_zimp(impurity_info)

        # check if calculation is single imp calculation
        if len(zimp)!=1:
            is_single_imp = False

        return zimp, is_single_imp


    def need_gf_run(self):
        """
        check if GF was given in input and can be reused (then return Falser which means no gf needs to be calculated)
        """
        if 'gf_host_remote' in self.inputs:
            return False

        return True


    def run_gf_writeout(self):
        """
        Write out the host GF
        """

        wf_parameters_flex = self.ctx.wf_parameters_flex
        # create process builder for gf_writeout workflow
        builder = kkr_flex_wc.get_builder()
        builder.impurity_info = self.ctx.imp_info_combined
        builder.kkr = self.inputs.host_gf.kkr
        builder.wf_parameters = Dict(dict=wf_parameters_flex)

        if 'options' in self.inputs.host_gf:
            builder.options = self.inputs.host_gf.options

        if 'params_kkr_overwrite' in self.inputs.host_gf:
            self.report("INFO: using params_kkr_overwrite in host_gf step: {}".format(self.inputs.host_gf.params_kkr_overwrite.get_dict()))
            builder.params_kkr_overwrite = self.inputs.host_gf.params_kkr_overwrite

        # find converged_host_remote input (converged potential of host system)
        gf_writeout_calc = None
        if self.ctx.imp1.process_class == KkrimpCalculation:
            #take gf_writeout directly from input to KkrimpCalculation
            gf_writeout_calc = self.ctx.imp1.inputs.host_Greenfunction_folder.get_incoming(node_class=KkrCalculation).first().node
        if self.ctx.imp1.process_class == kkr_imp_sub_wc:
            imp1_sub = self.ctx.imp1
        else:
            imp1_sub = self.ctx.imp1.get_outgoing(node_class=kkr_imp_sub_wc).first().node
        if gf_writeout_calc is None:
            gf_writeout_calc = imp1_sub.inputs.remote_data.get_incoming(node_class=KkrCalculation).first().node
        builder.remote_data = gf_writeout_calc.inputs.parent_folder

        # set label and description of the calc
        sub_label = 'GF writeout combined imps'
        sub_description = 'GF writeout sub workflow for combine_imps_wc '
        builder.metadata.label = sub_label # pylint: disable=no-member
        builder.metadata.description = sub_description # pylint: disable=no-member

        # now submit the workflow
        future = self.submit(builder)

        self.report('INFO: running GF writeout (pk: {})'.format(future.pk))

        return ToContext(gf_writeout=future)


    def check_host_gf(self):
        """
        Check if host gf is there
        """
        self.ctx.host_gf_ok = True

        if self.need_gf_run(): # check only if the calculation was run
            if not self.ctx.gf_writeout.is_finished_ok:
                self.ctx.host_gf_ok = False

        #TODO check if input host gf remote is consistent

        if not self.ctx.host_gf_ok:
            return self.exit_codes.ERROR_HOST_GF_CALC_FAILED


    def create_big_potential(self): # pylint: disable=inconsistent-return-statements
        """
        combine preconverged potentials to big one
        """

        # get data from context
        imp1 = self.ctx.imp1
        imp2 = self.ctx.imp2
        kickout_info = self.ctx.kickout_info
        
        nspin1, pot_imp1 = get_nspin_and_pot(imp1)
        nspin2, pot_imp2 = get_nspin_and_pot(imp2)
        
        # check consistency of nspin for the two calculations
        if nspin1 != nspin2:
            return self.exit_codes.ERROR_INCONSISTENT_NSPIN_VALUES # pylint: disable=maybe-no-member

        # now combine potentials
        output_potential_sfd_node = combine_potentials_cf(kickout_info, pot_imp1, pot_imp2, Int(nspin1))

        self.ctx.combined_potentials = output_potential_sfd_node
       
    # To collate and combine the wf_parameters_overwrite and scf_wf_parameters
    def update_params(self):
        """
        Update the parameters in scf_wf_parameters according to wf_parameters_overwrite if 
        any change occur there and also add the run options.
        """
        
        scf_wf_parameters = self.ctx.scf_wf_parameters.get_dict()
        wf_parameters_flex = self.ctx.wf_parameters_flex
        run_options = self.ctx.run_options
        # Update the scf_wf_parameters from the wf_parameters_overwrite
        if 'wf_parameters_overwrite' in self.inputs: 
            wf_parameters_overwrite = self.ctx.wf_parameters_overwrite.get_dict()
            
            for key, val in wf_parameters_overwrite.items():
               # Update the scf_wf_parameters from wf_parameters_overwrite
                if key in scf_wf_parameters.keys():
                    if wf_parameters_overwrite[key] != scf_wf_parameters[key]:
                        scf_old_val = scf_wf_parameters[key]
                        scf_wf_parameters[key] = val
                        msg = 'INFO: Parameter value of {} set from {} to {}'.format(key, scf_old_val, val)
                        self.report(msg)
                else:
                    scf_wf_parameters[key] = val

        # Update the wf_parameters_flex and run_options from the scf_wf_parameters            
        key_list = []
        for key, val in scf_wf_parameters.items():
            if key in wf_parameters_flex.keys() or  key in run_options.keys():
                # Here preparing the wf parameters for kkr_flex_wc
                if key in wf_parameters_flex.keys():
                    deflt_val = wf_parameters_flex[key]
                    wf_parameters_flex[key] = scf_wf_parameters.get(key,deflt_val)
                # Here preparing the some run option
                if key in run_options.keys():
                    deflt_val = run_options[key]
                    run_options[key] = scf_wf_parameters.get(key, deflt_val)
                    self.report('INFO: Probable run option <{}> is updated here as <{}>'.format(key,run_options[key]))
                key_list.append(key)
        # Here to remove keys from scf_wf_parameters that are needed only for gf_writeout_step and run_option 
        val_list = [scf_wf_parameters.pop(key, None) for key in key_list[:]]

        self.report('INFO: The wf_parameters Dict for kkr_imp_sub_wc is ready.')
        
        self.ctx.run_options = run_options
        self.ctx.wf_parameters_flex = wf_parameters_flex
        self.ctx.scf_wf_parameters = Dict(dict=scf_wf_parameters)   


    def run_kkrimp_scf(self):
        """
        run the kkrimp_sub workflow to converge the host-imp startpot
        """

        # construct process builder for kkrimp scf workflow
        builder = kkr_imp_sub_wc.get_builder()
        builder.metadata.label = 'kkrimp scf combined imps' # pylint: disable=no-member
        builder.metadata.description = 'scf workflow for combined impurities: {}, {}'.format(self.ctx.imp1.label, self.ctx.imp2.label) # pylint: disable=no-member

        # add combined impurity-info and startpot
        builder.impurity_info = self.ctx.imp_info_combined
        builder.host_imp_startpot = self.ctx.combined_potentials

        # add host GF (either calculated or form input)
        if 'gf_host_remote' not in self.inputs:
            gf_remote = self.ctx.gf_writeout.outputs.GF_host_remote
        else:
            gf_remote = self.inputs.gf_host_remote
        builder.remote_data = gf_remote

        # To set kkrimp code, options, and wf_parameters
        builder.kkrimp = self.ctx.scf_kkrimp
        builder.options = self.ctx.scf_options
        builder.wf_parameters = self.ctx.scf_wf_parameters
            
        # take care of LDA+U settings
        add_ldausettings, settings_LDAU_combined = self.get_ldau_combined()
        self.report(f'add LDA+U settings? {add_ldausettings}')
        if add_ldausettings:
            self.report(f'settings_combined: {settings_LDAU_combined.get_dict()}')
            builder.settings_LDAU = settings_LDAU_combined

        # now submit workflow
        future = self.submit(builder)

        self.report("INFO: running kkrimp scf workflow for combined impts (uuid= {})".format(future.uuid))

        return ToContext(kkrimp_scf_sub=future)
    
    def run_jij(self):
        if not self.ctx.kkrimp_scf_sub.is_finished_ok:
            msg = self.exit_codes.ERROR_SOMETHING_WENT_WRONG
            self.report(msg)
            return False       
        # TODO : work here from the RUNOPT instead of scf_wf_parameters, because all the RUNOPT and wf_parameters_flex are updated in the update parameter funcion.
        run_options = self.ctx.run_options
        if 'jij_run' in run_options.keys():
            self.ctx.jij_option = run_options['jij_run']
        
        return self.ctx.jij_option
        
    
    # To launch jij step
    def run_jij_step(self):
        """Run the jij calculation with the converged combined_imp_host_pot"""
        if self.ctx.kkrimp_scf_sub.is_finished_ok:
            msg = "INFO: kkr_imp_sub_wc for combined impurity cluster is succefully done and jij step is getting prepared for launching."
            self.report(msg)
            combined_scf_node = self.ctx.kkrimp_scf_sub
        else:
            return self.exit_codes.ERROR_SOMETHING_WENT_WRONG
        
        last_calc = load_node(combined_scf_node.outputs.workflow_info['last_calc_nodeinfo']['uuid'])
        builder = last_calc.get_builder_restart()

        builder.pop('parent_calc_folder')
        builder.impurity_potential = combined_scf_node.outputs.host_imp_pot
        param_dict = {k:v for k,v in builder.parameters.get_dict().items() if v is not None}
        param_dict['CALCJIJMAT'] = 1 # activate Jij calculation, leave the rest as is

        builder.parameters = Dict(dict=param_dict)
        builder.metadata.label = 'KKRimp_Jij ('+last_calc.label.split('=')[1][3:]

        future = self.submit(builder)
        self.report('INFO: Submiting Jij calculation (uuid=%s)'%(future.uuid))

        return ToContext(imp_scf_combined_jij = future)


    def get_ldau_combined(self):
        """
        check if impurity input calculations have LDA+U settings in input and add this here if needed
        """
        
        imp1_has_ldau = 'settings_LDAU' in self.ctx.imp1.inputs
        if imp1_has_ldau:
            settings_LDAU1 =  self.ctx.imp1.inputs.settings_LDAU
            self.report('found LDA+U settings for imp1')
            
        imp2_has_ldau = 'settings_LDAU' in self.ctx.imp2.inputs
        if imp2_has_ldau:
            settings_LDAU2 =  self.ctx.imp2.inputs.settings_LDAU
            self.report('found LDA+U settings for imp1')
        
        if imp1_has_ldau and imp2_has_ldau:
            # combine LDA+U settings of the two imps
            settings_LDAU_combined = combine_settings_ldau(settings_LDAU1=settings_LDAU1,
                                                           retrieved1=self.ctx.imp1.outputs.retrieved,
                                                           settings_LDAU2=settings_LDAU2,
                                                           retrieved2=self.ctx.imp2.outputs.retrieved,
                                                           kickout_info=self.ctx.kickout_info)
        elif imp1_has_ldau:
            # use only LDA+U settings of imp 1
            settings_LDAU_combined = combine_settings_ldau(settings_LDAU1=settings_LDAU1,
                                                           retrieved1=self.ctx.imp1.outputs.retrieved, 
                                                           kickout_info=self.ctx.kickout_info)
        elif imp2_has_ldau:
            # add offset to atom index for combined LDA+U settings
            settings_LDAU_combined = combine_settings_ldau(settings_LDAU2=settings_LDAU2,
                                                           retrieved2=self.ctx.imp2.outputs.retrieved,
                                                           kickout_info=self.ctx.kickout_info)
        else:
            # return builder unchanged if none of the impurt calculations has LDA+U settings
            return False, {}
        
        # now add settings_LDAU input to builder
        self.report('add combined LDAU settings (uuid={}): {}'.format(settings_LDAU_combined.uuid, settings_LDAU_combined.get_dict()))
        
        return True, settings_LDAU_combined


    def return_results(self):
        """
        check if the calculation was successful and return the result nodes
        """

        import  numpy as np

        self.report('INFO: Return_results:INFO: Return_results:  To collect the WF info and Other results')

        if not self.ctx.kkrimp_scf_sub.is_finished_ok:
            self.report('ERROR: kkrimp convergence step is not finished successfully')
            return self.exit_codes.ERROR_SOMETHING_WENT_WRONG
        
        # collect results of kkrimp_scf sub-workflow
        kkrimp_scf_sub = self.ctx.kkrimp_scf_sub
        results_kkrimp_sub = kkrimp_scf_sub.outputs.workflow_info
        last_calc = load_node(results_kkrimp_sub['last_calc_nodeinfo']['uuid'])
        output_parameters = last_calc.outputs.output_parameters
        last_remote = last_calc.outputs.remote_folder
        last_pot = kkrimp_scf_sub.outputs.host_imp_pot
        out_dict = {}
        out_dict['workflow_name'] = self.__class__.__name__
        out_dict['workflow_version'] = self._workflowversion

        # collect info of sub workflow
        out_dict['sub_workflows'] = {'kkrimp_scf': {'pk': kkrimp_scf_sub.pk, 'uuid':kkrimp_scf_sub.uuid}}

        # collect some results from scf sub-workflow
        for key in ['successful', 'convergence_value', 'convergence_reached', 'convergence_values_all_steps']:
            out_dict[key] = results_kkrimp_sub[key]

        magmom_all = np.array(output_parameters['magnetism_group']['spin_moment_per_atom'], dtype=float)[:,-1]
        out_dict['magmoms'] = magmom_all
        
        # Parse_jij and collect some info
        is_jij_exist = self.ctx.jij_option 
        if is_jij_exist:
            impurity1_output_node = self.inputs.impurity1_output_node
            impurity2_output_node = self.inputs.impurity2_output_node
            jij_calc = self.ctx.imp_scf_combined_jij
            jij_retrieved = jij_calc.outputs.retrieved
            impurity_info = kkrimp_scf_sub.inputs.impurity_info
            out_dict['run_option_info'] = {'jij_calc':{'pk':jij_calc.pk,
                                           'uuid': jij_calc.uuid,
                                           'is_finished_ok':jij_calc.is_finished_ok }
                                    }
            jij_parsed_dict = parse_Jij(jij_retrieved, impurity_info, impurity1_output_node, impurity2_output_node)
        # collect outputs of host_gf sub_workflow if it was done
        if 'gf_host_remote' not in self.inputs:
            gf_writeout = self.ctx.gf_writeout
            gf_sub_remote = gf_writeout.outputs.GF_host_remote

            # add info about sub-workflow to dict output
            out_dict['sub_workflows']['host_gf'] = {'pk': gf_writeout.pk, 'uuid': gf_writeout.uuid}
            # add as output node
            self.out('remote_data_gf', gf_sub_remote)


        # add information on combined cluster and potential
        out_dict['imp_info_combined'] = self.ctx.imp_info_combined.get_dict()
        out_dict['potential_kickout_info'] = self.ctx.kickout_info.get_dict()
     
        # create results node with input links
        # TODO: Add the imp_scf_combined_jij to link the run_jij_step output on provanace graph 
        link_nodes = {'kkrimp_scf_results': results_kkrimp_sub}
        if 'gf_host_remote' in self.inputs:
            link_nodes['GF_host_remote'] = self.inputs.gf_host_remote 
        if is_jij_exist:
            link_nodes['Jij_retrieved'] =jij_retrieved 
        outputnode = create_out_dict_node(Dict(dict=out_dict), **link_nodes)
        outputnode.label = 'combine_imps_wc_results'

        # add output nodes
        self.out('workflow_info', outputnode)
        self.out('last_potential', last_pot)
        self.out('last_calc_remote', last_remote)
        self.out('last_calc_output_parameters', output_parameters)
        if is_jij_exist:
            self.out('JijData', jij_parsed_dict['Jijdata'])
            self.out('JijInfo', jij_parsed_dict['info'])

@calcfunction
def parse_Jij(retrieved, impurity_info, impurity1_output_node, impurity2_output_node):
    """parser output of Jij calculation and return as ArrayData node"""

    _FILENAME_TAR = 'output_all.tar.gz'

    if _FILENAME_TAR in retrieved.list_object_names():
        # get path of tarfile
        with retrieved.open(_FILENAME_TAR) as tf:
            tfpath = tf.name
        # extract file from tarfile of retrieved to tempfolder
        with tarfile.open(tfpath) as tf:
            tar_filenames = [ifile.name for ifile in tf.getmembers()]
            filename = 'out_Jijmatrix'
            if filename in tar_filenames:
                tf.extract(filename, tfpath.replace(_FILENAME_TAR,'')) # extract to tempfolder
    # Collect the zimp for impurity_output_node
    imp1_z = impurity1_output_node.get_incoming(node_class=kkr_imp_wc).first().node.inputs.impurity_info.get_dict()['Zimp']
    imp2_z = impurity2_output_node.get_incoming(node_class=kkr_imp_wc).first().node.inputs.impurity_info.get_dict()['Zimp'] 
    
    jijdata = np.loadtxt(tfpath.replace(_FILENAME_TAR,'')+'out_Jijmatrix')
    impurity_info = impurity_info.get_dict()
    pos = np.array(impurity_info['imp_cls'])
    z = np.array(impurity_info['imp_cls'])[:,4]
    Vpos = list(np.where( z == imp1_z )[0]) + list(np.where( z == imp2_z )[0])

    Ry2eV = get_Ry2eV()

    # extract number of atoms
    natom = int(np.sqrt(jijdata.shape[0]/3/3))

    # reshape data
    jij_reshape = jijdata.reshape(3, natom, natom, 3, 3) # iter, i, j, k, l (Jij_k,l matrix)

    # now combine iterations to get full 3 by 3 Jij matrices for all atom pairs
    jij_combined_iter = np.zeros((natom, natom, 3, 3))
    for iatom in range(natom-1):
        for jatom in range(natom)[iatom+1:]:
            for iiter in range(3):
                if iiter==0:
                    # first iteration with theta, phi = 0, 0
                    # take complete upper block from here since this calculation should be converged best
                    # (rotated moments only one-shot calculations)
                    jij_combined_iter[iatom, jatom, 0, 0] = jij_reshape[iiter, iatom, jatom, 0, 0]
                    jij_combined_iter[iatom, jatom, 0, 1] = jij_reshape[iiter, iatom, jatom, 0, 1]
                    jij_combined_iter[iatom, jatom, 1, 0] = jij_reshape[iiter, iatom, jatom, 1, 0]
                    jij_combined_iter[iatom, jatom, 1, 1] = jij_reshape[iiter, iatom, jatom, 1, 1]
                elif iiter==1:
                    # second iteraton with theta, phi = 90, 0
                    jij_combined_iter[iatom, jatom, 1, 2] = jij_reshape[iiter, iatom, jatom, 1, 2]
                    jij_combined_iter[iatom, jatom, 2, 1] = jij_reshape[iiter, iatom, jatom, 2, 1]
                    jij_combined_iter[iatom, jatom, 2, 2] = jij_reshape[iiter, iatom, jatom, 2, 2]
                else:
                    # from third iteration with theta, phi = 90, 90
                    jij_combined_iter[iatom, jatom, 0, 2] = jij_reshape[iiter, iatom, jatom, 0, 2]
                    jij_combined_iter[iatom, jatom, 2, 0] = jij_reshape[iiter, iatom, jatom, 2, 0]
                    # add this value to z-z component and average
                    jij_combined_iter[iatom, jatom, 2, 2] += jij_reshape[iiter, iatom, jatom, 2, 2]
                    jij_combined_iter[iatom, jatom, 2, 2] *= 0.5

    # finally convert to meV units (and sign change to have positive number indicate ferromagnetism and negative number antiferromagnetism)
    jij_combined_iter *= -1.*Ry2eV*1000

    jij_trace = (jij_combined_iter[:,:,0,0]+jij_combined_iter[:,:,1,1]+jij_combined_iter[:,:,2,2])/3
    Dij_vec = np.array([(jij_combined_iter[:,:,1,2]-jij_combined_iter[:,:,2,1]), (jij_combined_iter[:,:,2,0]-jij_combined_iter[:,:,0,2]), (jij_combined_iter[:,:,0,1]-jij_combined_iter[:,:,1,0])])

    plotdata = []

    #return jij_combined_iter
    out_txt = "Output Jij values between V impurities:\ni   j     Jij (meV)       Dij(meV)        D/J\n-----------------------------------------------\n"
    for iatom in range(natom-1):
        for jatom in range(natom)[iatom+1:] :
            if iatom!=jatom and iatom in Vpos and jatom in Vpos:
                J = jij_trace[iatom, jatom]
                Dx, Dy, Dz = Dij_vec[0, iatom , jatom], Dij_vec[1, iatom , jatom], Dij_vec[2, iatom , jatom]
                D = np.sqrt(Dx**2 + Dy**2 + Dz**2)
                out_txt += '%3i %3i %15.5e %15.5e %15.5e\n'%(iatom, jatom, J, D, D/J)
                rdiff = pos[jatom] - pos[iatom]
                plotdata.append([rdiff[0], rdiff[1], rdiff[2], J, D, Dx, Dy, Dz])
    plotdata = np.array(plotdata)

    a = ArrayData()
    a.set_array('JijData', plotdata)

    return {'Jijdata': a, 'info': Dict(dict={'text': out_txt})}


