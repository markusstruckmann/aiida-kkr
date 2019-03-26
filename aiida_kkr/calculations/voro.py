# -*- coding: utf-8 -*-
"""
Input plug-in for a voronoi calculation.
"""
from __future__ import print_function
from __future__ import absolute_import
from aiida.engine import CalcJob
from aiida.common.utils import classproperty
from aiida.common.exceptions import (InputValidationError, ValidationError)
from aiida.common.datastructures import (CalcInfo, CodeInfo)
from aiida.plugins import DataFactory
from aiida_kkr.tools.common_workfunctions import generate_inputcard_from_structure, check_2Dinput_consistency, vca_check
from aiida.common.exceptions import UniquenessError
import os
import six

__copyright__ = (u"Copyright (c), 2017, Forschungszentrum Jülich GmbH, "
                 "IAS-1/PGI-1, Germany. All rights reserved.")
__license__ = "MIT license, see LICENSE.txt file"
__version__ = "0.5"
__contributors__ = ("Jens Broeder", "Philipp Rüßmann")


Dict = DataFactory('dict')
StructureData = DataFactory('structure')
RemoteData = DataFactory('remote')
SingleFileData = DataFactory('singlefile')

class VoronoiCalculation(CalcJob):
    """
    AiiDA calculation plugin for a voronoi calculation (creation of starting potential and shapefun)
    .
    """

    ####################
    # File names etc.
    ####################
    # calculation plugin version
    _CALCULATION_PLUGIN_VERSION = __version__
    # Default input and output files
    _DEFAULT_INPUT_FILE = 'inputcard' # will be shown with inputcat
    _DEFAULT_OUTPUT_FILE = 'out_voronoi' #'shell output will be shown with outputca
    # List of mandatory input files
    _INPUT_FILE_NAME = 'inputcard'
    # List of output files that should always be present
    _OUTPUT_FILE_NAME = 'out_voronoi'
    # template.product entry point defined in setup.json
    _default_parser = 'kkr.voroparser'
    # File names
    _ATOMINFO = 'atominfo.txt'
    _RADII = 'radii.dat'
    _SHAPEFUN = 'shapefun'
    _VERTICES = 'vertices.dat'
    _OUT_POTENTIAL_voronoi = 'output.pot'
    _POTENTIAL_IN_OVERWRITE = 'overwrite_potential'

    @classmethod
    def define(cls, spec):
        """
        define internals and inputs / outputs of calculation
        """
        # reuse base class (i.e. CalcJob) functions
        super(VoronoiCalculation, cls).define(spec)
        # now define input files
        spec.input('metadata.options.parser_name', valid_type=six.string_types, default=cls._default_parser)
        spec.input('metadata.options.input_filename', valid_type=six.string_types, default=cls._DEFAULT_INPUT_FILE)
        spec.input('metadata.options.output_filename', valid_type=six.string_types, default=cls._DEFAULT_OUTPUT_FILE)
        # define input nodes (optional ones have required=False)
        spec.input('parameters', valid_type=Dict, help='Use a node that specifies the input parameters')
        spec.input('structure', valid_type=StructureData, required=False, help='Use a node that specifies the input crystal structure')
        spec.input('parent_KKR', valid_type=RemoteData, required=False, help='Use a node that specifies a parent KKR calculation')
        spec.input('potential_overwrite', valid_type=SingleFileData, required=False, help='Use a node that specifies the potential which is used instead of the voronoi output potential')
        # define outputs
        spec.output('results', valid_type=Dict, help='calculation outputs')
        # define exit codes, also used in parser
        spec.exit_code(301, 'ERROR_NO_OUTPUT_FILE',
          message='Voronoi output file not found')


    def prepare_for_submission(self, tempfolder):
        """Create the input files from the input nodes passed to this instance of the `CalcJob`.

        :param tempfolder: an `aiida.common.folders.Folder` to temporarily write files on disk
        :return: `aiida.common.datastructures.CalcInfo` instance
        """
        # Check inputdict
        parameters = self.inputs.parameters

        if 'structure' in self.inputs:
            structure = self.inputs.structure
            found_structure = True
        else:
            found_structure = False

        vca_structure = False
        if found_structure:
            if not isinstance(structure, StructureData):
                raise InputValidationError("structure not of type "
                                            "StructureData")
            # for VCA: check if input structure and parameter node define VCA structure
            vca_structure = vca_check(structure, parameters)

        code = self.inputs.code

        # check if a parent folder containing a potential file (out_potential) is given
        if 'parent_KKR' in self.inputs:
            parent_calc_folder = self.inputs.parent_KKR
            found_parent = True
        else:
            found_parent = False

        if found_parent:
            # check if parent is either Voronoi or previous KKR calculation
            overwrite_potential, parent_calc = self._check_valid_parent(parent_calc_folder)

            #cross check if no structure was given and extract structure from parent
            if found_structure and not vca_structure:
                raise InputValidationError("parent_KKR and structure found in input. "
                                           "Can only use either parent_KKR or structure in input.")
            else:
                structure_remote_KKR, voro_parent = self.find_parent_structure(parent_calc)
                if not vca_structure:
                    structure = structure_remote_KKR
                else:
                    # check consistency of input vca structure and structure  from remote KKR folder
                    # TODO check consistency
                    pass
        else:
            overwrite_potential = False
            if not found_structure:
                raise InputValidationError("Neither structure nor parent_KKR specified for this "
                                           "calculation")

        # check if overwrite potential is given explicitly
        if 'potfile_overwrite' in self.inputs:
            potfile_overwrite = self.inputs.potfile_overwrite
            has_potfile_overwrite = True
        else:
            has_potfile_overwrite = False

        if has_potfile_overwrite:
            overwrite_potential = True
            if not found_structure:
                raise InputValidationError("Input structure needed for this calculation "
                                           "(using 'potential_overwrite' input node)")

        ###################################
        # Check for 2D case
        twoDimcheck, msg = check_2Dinput_consistency(structure, parameters)
        if not twoDimcheck:
            raise InputValidationError(msg)

        # Prepare inputcard from Structure and input parameter data
        input_filename = tempfolder.get_abs_path(self._INPUT_FILE_NAME)
        try:
            use_alat_input = parameters.get_dict().get('use_input_alat', False)
            natom, nspin, newsosol, warnings_write_inputcard = generate_inputcard_from_structure(parameters, structure, input_filename, isvoronoi=True, vca_structure=vca_structure, use_input_alat=use_alat_input)
        except ValueError as e:
            raise InputValidationError("Input ParameterData not consistent: {}".format(e))

        # Decide what files to copy
        local_copy_list = []
        if overwrite_potential:
            # copy the right files #TODO check first if file, exists and throw
            # warning, now this will throw an error
            if found_parent and self._is_KkrCalc(parent_calc):
                outfolderpath = parent_calc.out.retrieved.folder.abspath
                self.logger.info("out folder path {}".format(outfolderpath))
                filename = os.path.join(outfolderpath, 'path', parent_calc._OUT_POTENTIAL)
                copylist = [filename]
            elif has_potfile_overwrite:
                copylist = [potfile_overwrite.get_file_abs_path()]
            else:
                copylist = []

            for file1 in copylist:
                filename = file1
                if (found_parent or has_potfile_overwrite) and file1 == copylist[0]:
                    filename = self._POTENTIAL_IN_OVERWRITE
                local_copy_list.append((file1, filename))

        # Prepare CalcInfo to be returned to aiida
        calcinfo = CalcInfo()
        calcinfo.uuid = self.uuid
        calcinfo.local_copy_list = local_copy_list
        calcinfo.remote_copy_list = []
        calcinfo.retrieve_list = [self._OUTPUT_FILE_NAME, self._ATOMINFO,
                                  self._RADII, self._SHAPEFUN, self._VERTICES,
                                  self._INPUT_FILE_NAME]

        # pass on overwrite potential if this was given in input
        # (KkrCalculation checks if this file is there and takes this file instead of _OUT_POTENTIAL_voronoi
        #  if given)
        if overwrite_potential:
            calcinfo.retrieve_list += [self._POTENTIAL_IN_OVERWRITE]
        else:
            calcinfo.retrieve_list += [self._OUT_POTENTIAL_voronoi]

        codeinfo = CodeInfo()
        codeinfo.cmdline_params = []
        codeinfo.stdout_name = self._OUTPUT_FILE_NAME
        codeinfo.code_uuid = code.uuid
        calcinfo.codes_info = [codeinfo]

        return calcinfo


    def _check_valid_parent(self, parent_calc_folder):
        """
        Check that calc is a valid parent for a FleurCalculation.
        It can be a VoronoiCalculation, KKRCalculation
        """
        overwrite_pot = False

        # extract parent calculation
        parent_calcs = parent_calc_folder.get_inputs(node_type=JobCalculation)
        n_parents = len(parent_calcs)
        if n_parents != 1:
            raise UniquenessError("Input RemoteData is child of {} "
                                  "calculation{}, while it should have a single parent"
                                  "".format(n_parents, "" if n_parents == 0 else "s"))
        else:
            parent_calc = parent_calcs[0]
            overwrite_pot = True

        if ((not self._is_KkrCalc(parent_calc)) ):
            raise ValueError("Parent calculation must be a KkrCalculation")

        return overwrite_pot, parent_calc


    def _is_KkrCalc(self, calc):
        """
        check if calc contains the file out_potential
        """
        is_KKR = False
        ret = calc.get_retrieved_node()
        ret_path = ret.get_abs_path()
        ret_path = os.path.join(ret_path, 'path')
        if 'out_potential' in os.listdir(ret_path):
            is_KKR = True

        return is_KKR


    @classmethod
    def _get_struc(self, parent_calc):
        """
        Get structure from a parent_folder (result of a calculation, typically a remote folder)
        """
        return parent_calc.inp.structure


    @classmethod
    def _has_struc(self, parent_folder):
        """
        Check if parent_folder has structure information in its input
        """
        success = True
        try:
            parent_folder.inp.structure
        except:
            success = False
        return success


    @classmethod
    def _get_remote(self, parent_folder):
        """
        get remote_folder from input if parent_folder is not already a remote folder
        """
        parent_folder_tmp0 = parent_folder
        try:
            parent_folder_tmp = parent_folder_tmp0.inp.remote_folder
        except:
            #TODO check if this is a remote folder
            parent_folder_tmp = parent_folder_tmp0
        return parent_folder_tmp


    @classmethod
    def _get_parent(self, input_folder):
        """
        get the  parent folder of the calculation. If not parent was found return input folder
        """
        input_folder_tmp0 = input_folder
        try:
            parent_folder_tmp = input_folder_tmp0.inp.parent_calc_folder
        except:
            try:
                parent_folder_tmp = input_folder_tmp0.inp.parent_calc
            except:
                parent_folder_tmp = input_folder_tmp0
        return parent_folder_tmp


    @classmethod
    def find_parent_structure(self, parent_folder):
        """
        Find the Structure node recuresively in chain of parent calculations (structure node is input to voronoi calculation)
        """
        iiter = 0
        Nmaxiter = 100
        parent_folder_tmp = self._get_remote(parent_folder)
        while not self._has_struc(parent_folder_tmp) and iiter<Nmaxiter:
            parent_folder_tmp = self._get_remote(self._get_parent(parent_folder_tmp))
            iiter += 1
        if self._has_struc(parent_folder_tmp):
            struc = self._get_struc(parent_folder_tmp)
            return struc, parent_folder_tmp
        else:
            print('struc not found')
